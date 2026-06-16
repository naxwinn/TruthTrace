"""
Analysis Pipeline
Orchestrates all detectors and stores findings in the database.
"""

import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from api.models import AnalysisJob, MediaFile, Finding
from services.media_extractor import MediaExtractor
from detectors.metadata.detector import MetadataDetector
from detectors.audio.splice_detector import AudioSpliceDetector
from detectors.audio.voice_clone_detector import VoiceCloneDetector
from detectors.video.optical_flow_detector import OpticalFlowDetector
from detectors.video.gop_detector import GOPDetector
from detectors.video.compression_detector import CompressionDetector
from detectors.fusion.engine import FusionEngine
from config import settings

logger = logging.getLogger(__name__)


def _sanitize_for_json(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(item) for item in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


class AnalysisPipeline:
    """Runs the full forensic analysis pipeline for a given job."""

    def __init__(self, job_id: str, db_url: str = None):
        self.job_id = job_id
        self.db_url = db_url or settings.database_url
        self.engine = create_engine(self.db_url)

    def run(self):
        """Execute the full pipeline."""
        with Session(self.engine) as db:
            job = db.query(AnalysisJob).filter(AnalysisJob.id == self.job_id).first()
            if not job:
                return

            media_file = db.query(MediaFile).filter(MediaFile.id == job.media_file_id).first()
            if not media_file:
                job.status = "failed"
                job.error_message = "Media file not found"
                db.commit()
                return

            try:
                # Phase 1: Extraction
                self._update_job(db, job, "extracting", 5.0)
                extractor = MediaExtractor(media_file.file_path, self.job_id)
                try:
                    extraction = extractor.extract_all()
                except subprocess.TimeoutExpired as e:
                    job.status = "failed"
                    job.error_message = f"Extraction timed out: {str(e)[:200]}"
                    db.commit()
                    return

                # Update duration
                duration = extraction.get("metadata", {}).get("duration")
                if duration:
                    media_file.duration = duration
                    db.commit()

                self._update_job(db, job, "analyzing", 20.0)

                all_findings: List[dict] = []

                # Phase 2: Metadata Forensics
                metadata_path = extraction.get("metadata", {}).get("path")
                if metadata_path and Path(metadata_path).exists():
                    self._update_job(db, job, "analyzing", 30.0)
                    detector = MetadataDetector(metadata_path)
                    findings = detector.analyze()
                    for f in findings:
                        f["detector_type"] = "metadata"
                    all_findings.extend(findings)

                # Phase 3: Audio Forensics
                audio_path = extraction.get("audio", {}).get("path")
                if audio_path and Path(audio_path).exists():
                    # Load audio once and share between detectors
                    import librosa
                    audio_y, audio_sr = librosa.load(audio_path, sr=22050)

                    # Splice detection
                    self._update_job(db, job, "analyzing", 40.0)
                    splice_detector = AudioSpliceDetector(audio_path, y=audio_y)
                    findings = splice_detector.analyze()
                    for f in findings:
                        f["detector_type"] = "audio"
                    all_findings.extend(findings)

                    # Voice clone detection
                    self._update_job(db, job, "analyzing", 55.0)
                    clone_detector = VoiceCloneDetector(audio_path, y=audio_y)
                    findings = clone_detector.analyze()
                    for f in findings:
                        f["detector_type"] = "audio"
                    all_findings.extend(findings)

                    del audio_y  # Free memory

                # Phase 4: Video Forensics
                frames_path = extraction.get("frames", {}).get("path")
                frames_fps = extraction.get("frames", {}).get("fps", 2.0)

                if frames_path and Path(frames_path).exists():
                    # Optical flow analysis
                    self._update_job(db, job, "analyzing", 65.0)
                    flow_detector = OpticalFlowDetector(frames_path, fps=frames_fps)
                    findings = flow_detector.analyze()
                    for f in findings:
                        f["detector_type"] = "video"
                    all_findings.extend(findings)

                    # Compression analysis
                    self._update_job(db, job, "analyzing", 75.0)
                    comp_detector = CompressionDetector(frames_path, fps=frames_fps)
                    findings = comp_detector.analyze()
                    for f in findings:
                        f["detector_type"] = "video"
                    all_findings.extend(findings)

                # GOP analysis (needs raw file, not frames)
                self._update_job(db, job, "analyzing", 80.0)
                try:
                    gop_data = extractor.get_gop_structure()
                except (subprocess.TimeoutExpired, Exception) as e:
                    gop_data = None  # Skip GOP if it times out — non-critical
                if gop_data:
                    comp_info = extractor.get_compression_info()
                    video_fps = 25.0
                    if comp_info:
                        rfr = comp_info.get("r_frame_rate", "25/1")
                        try:
                            num, den = rfr.split("/")
                            video_fps = float(num) / float(den)
                        except (ValueError, ZeroDivisionError):
                            pass
                    gop_detector = GOPDetector(gop_data, fps=video_fps)
                    findings = gop_detector.analyze()
                    for f in findings:
                        f["detector_type"] = "video"
                    all_findings.extend(findings)

                # Store findings in DB
                self._update_job(db, job, "correlating", 85.0)
                for f_data in all_findings:
                    finding = Finding(
                        job_id=self.job_id,
                        detector_type=f_data["detector_type"],
                        finding_type=f_data["finding_type"],
                        confidence=f_data["confidence"],
                        start_time=f_data.get("start_time"),
                        end_time=f_data.get("end_time"),
                        description=f_data.get("description"),
                        details=f_data.get("details"),
                    )
                    db.add(finding)

                # Phase 5: Fusion / Correlation
                self._update_job(db, job, "correlating", 90.0)
                fusion = FusionEngine(time_tolerance=1.5)
                incidents = fusion.correlate(all_findings)

                # Calculate authenticity score
                authenticity_score = self._calculate_authenticity_score(all_findings, incidents)

                # Sanitize all data for JSON serialization (numpy types → native Python)
                safe_incidents = _sanitize_for_json(incidents)
                safe_extraction = _sanitize_for_json(extraction)

                job.status = "complete"
                job.progress = 100.0
                job.authenticity_score = authenticity_score
                job.findings = {
                    "count": len(all_findings),
                    "incidents": safe_incidents,
                    "extraction": safe_extraction,
                }
                job.updated_at = datetime.utcnow()
                db.commit()
                logger.info(f"Job {self.job_id} completed. Score={authenticity_score}, Findings={len(all_findings)}")

            except Exception as e:
                logger.error(f"Job {self.job_id} failed: {e}", exc_info=True)
                db.rollback()  # Reset session state before error update
                try:
                    job.status = "failed"
                    job.error_message = str(e)[:1000]
                    job.updated_at = datetime.utcnow()
                    db.commit()
                except Exception:
                    logger.error(f"Job {self.job_id}: failed to persist error state")

    def _update_job(self, db: Session, job: AnalysisJob, status: str, progress: float):
        job.status = status
        job.progress = progress
        job.updated_at = datetime.utcnow()
        db.commit()

    def _calculate_authenticity_score(self, findings: List[dict], incidents: List[dict] = None) -> float:
        """
        Calculate overall authenticity score (0.0 = definitely tampered, 1.0 = authentic).
        Factors in both raw findings and correlated incidents.
        """
        if not findings:
            return 1.0

        # Base score from raw findings
        total_suspicion = sum(f["confidence"] for f in findings)
        base_score = max(0.0, 1.0 - (total_suspicion / 5.0))

        # Penalty for high-severity incidents
        if incidents:
            high_incidents = [i for i in incidents if i.get("severity") == "high"]
            medium_incidents = [i for i in incidents if i.get("severity") == "medium"]
            incident_penalty = len(high_incidents) * 0.2 + len(medium_incidents) * 0.1
            base_score = max(0.0, base_score - incident_penalty)

        return round(base_score, 3)
