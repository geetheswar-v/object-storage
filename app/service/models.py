from sqlmodel import SQLModel, Field, Column, DateTime, Enum as SQLEnum
from datetime import datetime
from enum import Enum
import uuid


class FileType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    OTHER = "other"


class FileRecord(SQLModel, table=True):
    __tablename__ = "files"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    filename: str = Field(index=True)
    original_filename: str
    file_type: FileType = Field(sa_column=Column(SQLEnum(FileType)))
    mime_type: str
    file_size: int
    file_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))


# Response models
class FileResponse(SQLModel):
    id: str
    filename: str
    original_filename: str
    file_type: FileType
    mime_type: str
    file_size: int
    created_at: datetime
    
    
class FileListResponse(SQLModel):
    files: list[FileResponse]
    total: int
    page: int
    per_page: int


class UploadResponse(SQLModel):
    id: str
    filename: str
    original_filename: str
    file_type: FileType
    mime_type: str
    file_size: int
    url: str
    message: str