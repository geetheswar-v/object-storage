from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.service.models import FileRecord, FileType, FileResponse, FileListResponse


async def create_file(
    session: AsyncSession,
    filename: str,
    original_filename: str,
    file_type: FileType,
    mime_type: str,
    file_size: int,
    file_path: str,
) -> FileRecord:
    """Create a new file record"""
    file_record = FileRecord(
        filename=filename,
        original_filename=original_filename,
        file_type=file_type,
        mime_type=mime_type,
        file_size=file_size,
        file_path=file_path,
    )
    session.add(file_record)
    await session.commit()
    await session.refresh(file_record)
    return file_record


async def get_file_by_id(session: AsyncSession, file_id: str) -> FileRecord | None:
    """Get file record by ID"""
    result = await session.execute(select(FileRecord).where(FileRecord.id == file_id))
    return result.scalar_one_or_none()


async def get_file_by_filename(session: AsyncSession, filename: str) -> FileRecord | None:
    """Get file record by filename"""
    result = await session.execute(select(FileRecord).where(FileRecord.filename == filename))
    return result.scalar_one_or_none()


async def get_files_paginated(
    session: AsyncSession,
    page: int = 1,
    per_page: int = 10,
    file_type: FileType | None = None
) -> FileListResponse:
    """Get paginated list of files"""
    offset = (page - 1) * per_page
    
    # Base query
    query = select(FileRecord)
    count_query = select(func.count(FileRecord.id))
    
    # Apply file type filter if provided
    if file_type:
        query = query.where(FileRecord.file_type == file_type)
        count_query = count_query.where(FileRecord.file_type == file_type)
    
    # Add pagination and ordering
    query = query.offset(offset).limit(per_page).order_by(FileRecord.created_at.desc())
    
    # Execute queries
    files_result = await session.execute(query)
    files = files_result.scalars().all()
    
    total_result = await session.execute(count_query)
    total = total_result.scalar()
    
    # Convert to response models
    file_responses = [
        FileResponse(
            id=file.id,
            filename=file.filename,
            original_filename=file.original_filename,
            file_type=file.file_type,
            mime_type=file.mime_type,
            file_size=file.file_size,
            created_at=file.created_at,
        )
        for file in files
    ]
    
    return FileListResponse(
        files=file_responses,
        total=total,
        page=page,
        per_page=per_page
    )


async def delete_file(session: AsyncSession, file_id: str) -> bool:
    """Delete file record by ID"""
    result = await session.execute(select(FileRecord).where(FileRecord.id == file_id))
    file_record = result.scalar_one_or_none()
    
    if file_record:
        await session.delete(file_record)
        await session.commit()
        return True
    return False