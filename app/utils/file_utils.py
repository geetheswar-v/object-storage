import os
import uuid
import mimetypes
from app.service.models import FileType


def get_file_type_from_mime(mime_type: str) -> FileType:
    """Determine file type from MIME type"""
    mime_type = mime_type.lower()
    
    if mime_type.startswith('image/'):
        return FileType.IMAGE
    elif mime_type.startswith('video/'):
        return FileType.VIDEO
    elif mime_type.startswith('audio/'):
        return FileType.AUDIO
    elif mime_type in [
        'application/pdf', 'application/msword', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint', 
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain', 'text/csv', 'application/json', 'application/xml'
    ]:
        return FileType.DOCUMENT
    else:
        return FileType.OTHER


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving extension"""
    name, ext = os.path.splitext(original_filename)
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{ext}"


def create_file_path(base_dir: str, file_type: FileType, filename: str) -> str:
    """Create full file path with category structure"""
    return os.path.join(base_dir, file_type.value, filename)


def ensure_directory_exists(directory: str) -> None:
    """Ensure directory exists, create if it doesn't"""
    os.makedirs(directory, exist_ok=True)


def get_mime_type(filename: str) -> str:
    """Get MIME type for a file"""
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def is_image_file(mime_type: str) -> bool:
    """Check if file is an image"""
    return get_file_type_from_mime(mime_type) == FileType.IMAGE


def is_video_file(mime_type: str) -> bool:
    """Check if file is a video"""
    return get_file_type_from_mime(mime_type) == FileType.VIDEO