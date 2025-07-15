from sqlmodel import SQLModel, Field, Column, DateTime, Text, Enum as SQLEnum
from typing import Optional, Literal
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
    __tablename__ = "file_records"
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    filename: str = Field(index=True)
    original_filename: str
    file_type: FileType = Field(sa_column=Column(SQLEnum(FileType)))
    mime_type: str
    file_size: int  # in bytes
    file_path: str
    is_optimized: bool = False
    optimized_path: Optional[str] = None
    file_metadata: Optional[str] = Field(default=None, sa_column=Column(Text))  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime))
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))


# Response models
class FileResponse(SQLModel):
    id: str
    filename: str
    original_filename: str
    file_type: FileType
    mime_type: str
    file_size: int
    is_optimized: bool
    file_metadata: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    
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
    is_optimized: bool
    url: str
    message: str