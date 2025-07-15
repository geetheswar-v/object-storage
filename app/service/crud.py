from sqlmodel import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select
from app.service.models import FileRecord, FileType, FileResponse, FileListResponse
from typing import Optional, List
import json


class FileCRUD:
    
    @staticmethod
    async def create_file_record(
        session: AsyncSession,
        filename: str,
        original_filename: str,
        file_type: FileType,
        mime_type: str,
        file_size: int,
        file_path: str,
        is_optimized: bool = False,
        optimized_path: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> FileRecord:
        """Create a new file record"""
        file_record = FileRecord(
            filename=filename,
            original_filename=original_filename,
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
            file_path=file_path,
            is_optimized=is_optimized,
            optimized_path=optimized_path,
            file_metadata=json.dumps(metadata) if metadata else None
        )
        session.add(file_record)
        await session.commit()
        await session.refresh(file_record)
        return file_record
    
    @staticmethod
    async def get_file_by_filename(session: AsyncSession, filename: str) -> Optional[FileRecord]:
        """Get file record by filename"""
        result = await session.execute(select(FileRecord).where(FileRecord.filename == filename))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_file_by_id(session: AsyncSession, file_id: str) -> Optional[FileRecord]:
        """Get file record by ID"""
        result = await session.execute(select(FileRecord).where(FileRecord.id == file_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_files_paginated(
        session: AsyncSession,
        page: int = 1,
        per_page: int = 10,
        file_type: Optional[FileType] = None
    ) -> FileListResponse:
        """Get paginated list of files"""
        offset = (page - 1) * per_page
        
        # Base query
        statement = select(FileRecord)
        count_statement = select(func.count(FileRecord.id))
        
        # Apply file type filter if provided
        if file_type:
            statement = statement.where(FileRecord.file_type == file_type)
            count_statement = count_statement.where(FileRecord.file_type == file_type)
        
        # Add pagination
        statement = statement.offset(offset).limit(per_page).order_by(FileRecord.created_at.desc())
        
        # Execute queries
        files_result = await session.execute(statement)
        files = files_result.scalars().all()
        
        total_result = await session.execute(count_statement)
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
                is_optimized=file.is_optimized,
                file_metadata=file.file_metadata,
                created_at=file.created_at,
                updated_at=file.updated_at
            )
            for file in files
        ]
        
        return FileListResponse(
            files=file_responses,
            total=total,
            page=page,
            per_page=per_page
        )
    
    @staticmethod
    async def delete_file_record(session: AsyncSession, file_id: str) -> bool:
        """Delete file record by ID"""
        result = await session.execute(select(FileRecord).where(FileRecord.id == file_id))
        file_record = result.scalar_one_or_none()
        
        if file_record:
            await session.delete(file_record)
            await session.commit()
            return True
        return False
    
    @staticmethod
    async def update_file_optimization(
        session: AsyncSession,
        file_id: str,
        optimized_path: str
    ) -> Optional[FileRecord]:
        """Update file record with optimization info"""
        result = await session.execute(select(FileRecord).where(FileRecord.id == file_id))
        file_record = result.scalar_one_or_none()
        
        if file_record:
            file_record.is_optimized = True
            file_record.optimized_path = optimized_path
            await session.commit()
            await session.refresh(file_record)
            return file_record
        return None