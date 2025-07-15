import os
import uuid
from typing import Dict, Optional
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
    elif mime_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                       'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                       'application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                       'text/plain', 'text/csv', 'application/json', 'application/xml']:
        return FileType.DOCUMENT
    else:
        return FileType.OTHER


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving extension"""
    name, ext = os.path.splitext(original_filename)
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{ext}"


def get_file_category_path(file_type: FileType) -> str:
    """Get directory path for file category"""
    return file_type.value


def create_file_path(base_dir: str, file_type: FileType, filename: str) -> str:
    """Create full file path with category structure"""
    category_path = get_file_category_path(file_type)
    return os.path.join(base_dir, category_path, filename)


def ensure_directory_exists(directory: str) -> None:
    """Ensure directory exists, create if it doesn't"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    return os.path.getsize(file_path)


def is_image_file(mime_type: str) -> bool:
    """Check if file is an image"""
    return get_file_type_from_mime(mime_type) == FileType.IMAGE


def get_allowed_extensions() -> Dict[FileType, list]:
    """Get allowed file extensions by type"""
    return {
        FileType.IMAGE: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.ico'],
        FileType.VIDEO: ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.3gp'],
        FileType.DOCUMENT: ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.json', '.xml', '.rtf', '.html', '.md'],
        FileType.AUDIO: ['.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a', '.wma'],
        FileType.OTHER: []  # Allow any extension for other types
    }