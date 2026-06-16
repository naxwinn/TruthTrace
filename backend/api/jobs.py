from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from pathlib import Path
import concurrent.futures

from database import get_db
from api.models import AnalysisJob, MediaFile, Finding
from api.schemas import AnalysisJobCreate, AnalysisJobResponse, FindingResponse, AnalysisReport, MediaFileResponse
from services.media_extractor import MediaExtractor
from services.analysis_pipeline import AnalysisPipeline
from reports.pdf_generator import generate_report_pdf
from config import settings

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Dedicated thread pool for analysis to avoid blocking the server
_analysis_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="analysis")


def run_analysis(job_id: str, db_url: str):
    """Background task to run full analysis pipeline in dedicated thread pool."""
    _analysis_executor.submit(_run_analysis_worker, job_id, db_url)


def _run_analysis_worker(job_id: str, db_url: str):
    """Actual analysis worker — runs in thread pool, won't block server."""
    pipeline = AnalysisPipeline(job_id, db_url)
    pipeline.run()


@router.post("/", response_model=AnalysisJobResponse)
async def create_job(
    job_data: AnalysisJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    media_file = db.query(MediaFile).filter(MediaFile.id == job_data.media_file_id).first()
    if not media_file:
        raise HTTPException(404, "Media file not found")

    job = AnalysisJob(media_file_id=job_data.media_file_id)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Auto-trigger full analysis pipeline
    from config import settings
    background_tasks.add_task(run_analysis, job.id, settings.database_url)

    return job


@router.post("/{job_id}/analyze", response_model=AnalysisJobResponse)
async def trigger_analysis(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Manually trigger full analysis for a job."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    from config import settings
    background_tasks.add_task(run_analysis, job.id, settings.database_url)

    return job


@router.get("/", response_model=List[AnalysisJobResponse])
async def list_jobs(db: Session = Depends(get_db)):
    return db.query(AnalysisJob).order_by(AnalysisJob.created_at.desc()).all()


@router.get("/{job_id}", response_model=AnalysisJobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/{job_id}/findings", response_model=List[FindingResponse])
async def get_findings(job_id: str, db: Session = Depends(get_db)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return db.query(Finding).filter(Finding.job_id == job_id).all()


@router.get("/{job_id}/incidents")
async def get_incidents(job_id: str, db: Session = Depends(get_db)):
    """Get correlated incidents (fusion results) for a job."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    # Incidents are stored in the job findings JSON
    findings_data = job.findings or {}
    incidents = findings_data.get("incidents", [])

    return {
        "job_id": job_id,
        "status": job.status,
        "authenticity_score": job.authenticity_score,
        "incident_count": len(incidents),
        "incidents": incidents,
    }


@router.get("/{job_id}/report", response_model=AnalysisReport)
async def get_report(job_id: str, db: Session = Depends(get_db)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    media_file = db.query(MediaFile).filter(MediaFile.id == job.media_file_id).first()
    findings = db.query(Finding).filter(Finding.job_id == job_id).all()

    # Build timeline from findings
    timeline = []
    for f in findings:
        if f.start_time is not None:
            timeline.append({
                "start": f.start_time,
                "end": f.end_time,
                "type": f.finding_type,
                "confidence": f.confidence,
                "detector": f.detector_type,
            })
    timeline.sort(key=lambda x: x["start"])

    # Generate summary
    if not findings:
        summary = "No tampering indicators detected. File appears authentic."
    else:
        high_conf = [f for f in findings if f.confidence >= 0.7]
        summary = f"Analysis found {len(findings)} potential indicator(s) of tampering. "
        if high_conf:
            summary += f"{len(high_conf)} finding(s) have high confidence (≥70%)."

    return AnalysisReport(
        job=job,
        file=media_file,
        findings=findings,
        timeline=timeline,
        summary=summary,
    )


@router.get("/{job_id}/report/pdf")
async def download_report_pdf(job_id: str, db: Session = Depends(get_db)):
    """Generate and download a PDF forensic report."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != "complete":
        raise HTTPException(400, "Analysis not complete yet")

    media_file = db.query(MediaFile).filter(MediaFile.id == job.media_file_id).first()
    findings = db.query(Finding).filter(Finding.job_id == job_id).all()

    # Convert findings to dicts
    findings_data = [
        {
            "finding_type": f.finding_type,
            "confidence": f.confidence,
            "start_time": f.start_time,
            "end_time": f.end_time,
            "description": f.description,
            "detector_type": f.detector_type,
            "details": f.details,
        }
        for f in findings
    ]

    # Get incidents from job JSON
    job_findings = job.findings or {}
    incidents = job_findings.get("incidents", [])

    # Generate PDF
    pdf_path = settings.storage_dir / "reports" / f"{job_id}.pdf"
    generate_report_pdf(
        filename=media_file.original_filename,
        duration=media_file.duration,
        file_size=media_file.file_size,
        mime_type=media_file.mime_type,
        authenticity_score=job.authenticity_score or 1.0,
        findings=findings_data,
        incidents=incidents,
        output_path=str(pdf_path),
    )

    return FileResponse(
        path=str(pdf_path),
        filename=f"TruthTrace_Report_{media_file.original_filename}.pdf",
        media_type="application/pdf",
    )
