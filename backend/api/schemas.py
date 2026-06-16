from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MediaFileResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    duration: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisJobCreate(BaseModel):
    media_file_id: str


class AnalysisJobResponse(BaseModel):
    id: str
    media_file_id: str
    status: str
    progress: float
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    authenticity_score: Optional[float] = None

    class Config:
        from_attributes = True


class FindingResponse(BaseModel):
    id: str
    job_id: str
    detector_type: str
    finding_type: str
    confidence: float
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    description: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisReport(BaseModel):
    job: AnalysisJobResponse
    file: MediaFileResponse
    findings: List[FindingResponse]
    timeline: List[dict]
    summary: str
