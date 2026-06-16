import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class MediaFile(Base):
    __tablename__ = "media_files"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    duration = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("AnalysisJob", back_populates="media_file")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    media_file_id = Column(String, ForeignKey("media_files.id"), nullable=False)
    status = Column(String, default="pending")  # pending, extracting, analyzing, complete, failed
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(Text, nullable=True)

    # Results
    findings = Column(JSON, nullable=True)
    authenticity_score = Column(Float, nullable=True)
    report_path = Column(String, nullable=True)

    media_file = relationship("MediaFile", back_populates="jobs")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True, default=generate_uuid)
    job_id = Column(String, ForeignKey("analysis_jobs.id"), nullable=False)
    detector_type = Column(String, nullable=False)  # audio, video, metadata, fusion
    finding_type = Column(String, nullable=False)  # audio_splice, synthetic_voice, frame_deletion, etc.
    confidence = Column(Float, nullable=False)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
