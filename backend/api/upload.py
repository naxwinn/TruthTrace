import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from config import settings
from api.models import MediaFile, AnalysisJob
from api.schemas import MediaFileResponse, AnalysisJobResponse

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_TYPES = {
    "video/mp4", "video/avi", "video/x-msvideo", "video/quicktime",
    "video/x-matroska", "video/webm",
    "audio/mpeg", "audio/wav", "audio/x-wav", "audio/ogg", "audio/flac",
    "application/octet-stream",  # Fallback for unknown MIME detection
}

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".mp3", ".wav", ".ogg", ".flac"}


@router.post("/", response_model=MediaFileResponse)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = Path(file.filename).suffix.lower()
    if file.content_type not in ALLOWED_TYPES and ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    file_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix
    stored_filename = f"{file_id}{ext}"
    file_dir = settings.storage_dir / "uploads"
    file_dir.mkdir(parents=True, exist_ok=True)
    file_path = file_dir / stored_filename

    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = file_path.stat().st_size

    # Create DB record
    media_file = MediaFile(
        id=file_id,
        filename=stored_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type,
    )
    db.add(media_file)
    db.commit()
    db.refresh(media_file)

    return media_file


@router.get("/{file_id}", response_model=MediaFileResponse)
async def get_file(file_id: str, db: Session = Depends(get_db)):
    media_file = db.query(MediaFile).filter(MediaFile.id == file_id).first()
    if not media_file:
        raise HTTPException(404, "File not found")
    return media_file
