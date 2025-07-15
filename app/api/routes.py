from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Path
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.api.deps import verify_api_key, get_db_session
from app.service.crud import FileCRUD
from app.service.models import FileType, FileListResponse, UploadResponse, FileRecord
from app.service.db import check_db_connection
from app.utils.file_utils import (
    get_file_type_from_mime, 
    generate_unique_filename,
    create_file_path,
    ensure_directory_exists,
    is_image_file
)
from app.utils.image_utils import ImageOptimizer
from app.config import settings
from typing import Optional
import os
import aiofiles
import mimetypes


router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint that also checks database connection"""
    db_connected = await check_db_connection()
    
    if db_connected:
        return {
            "status": "healthy",
            "database": "connected",
            "message": "BrixAI Object Storage API is running"
        }
    else:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "message": "Database connection failed"
            }
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    optimize: bool = Query(False, description="Optimize image for web usage"),
    _: bool = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db_session)
):
    """Upload a file to the object storage"""
    
    # Check file size
    if file.size and file.size > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    file_type = get_file_type_from_mime(mime_type)

    unique_filename = generate_unique_filename(file.filename)

    file_path = create_file_path(settings.upload_directory, file_type, unique_filename)
    ensure_directory_exists(os.path.dirname(file_path))
    
    # Save file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        file_size = len(content)
        
        # Handle image optimization
        is_optimized = False
        optimized_path = None
        metadata = {}
        if optimize and is_image_file(mime_type) and ImageOptimizer.is_optimizable_image(mime_type):
            optimized_filename = f"optimized_{unique_filename}"
            optimized_path = create_file_path(settings.upload_directory, file_type, optimized_filename)

            success, error, opt_metadata = ImageOptimizer.optimize_for_web(
                file_path, 
                optimized_path
            )
            
            if success:
                is_optimized = True
                metadata.update(opt_metadata or {})
            else:
                optimized_path = None
                metadata["optimization_error"] = error
        
        # Add basic file info to metadata
        if is_image_file(mime_type):
            img_info = ImageOptimizer.get_image_info(file_path)
            if img_info:
                metadata["image_info"] = img_info
        
        file_record = await FileCRUD.create_file_record(
            session=session,
            filename=unique_filename,
            original_filename=file.filename,
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
            file_path=file_path,
            is_optimized=is_optimized,
            optimized_path=optimized_path,
            metadata=metadata
        )
        
        file_url = f"/files/{unique_filename}"
        
        return UploadResponse(
            id=file_record.id,
            filename=unique_filename,
            original_filename=file.filename,
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
            is_optimized=is_optimized,
            url=file_url,
            message="File uploaded successfully"
        )
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        if optimized_path and os.path.exists(optimized_path):
            os.remove(optimized_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.delete("/remove/{file_id}")
async def remove_file(
    file_id: str = Path(..., description="File ID to remove"),
    _: bool = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db_session)
):
    """Remove a file from the object storage"""
    
    # Get file record
    file_record = await FileCRUD.get_file_by_id(session, file_id)
    
    if not file_record:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    # Remove physical files
    files_to_remove = [file_record.file_path]
    if file_record.optimized_path:
        files_to_remove.append(file_record.optimized_path)
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                # Log error but continue with database cleanup
                print(f"Error removing file {file_path}: {e}")
    
    # Remove database record
    success = await FileCRUD.delete_file_record(session, file_id)
    
    if success:
        return {"message": "File removed successfully", "file_id": file_id}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to remove file from database"
        )


@router.get("/list", response_model=FileListResponse)
async def list_files(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    file_type: Optional[FileType] = Query(None, description="Filter by file type"),
    _: bool = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db_session)
):
    """List files with pagination and filtering"""
    
    return await FileCRUD.get_files_paginated(
        session=session,
        page=page,
        per_page=per_page,
        file_type=file_type
    )


@router.get("/files/{filename}")
async def get_file(
    filename: str = Path(..., description="File name to retrieve")
):
    """Get a file (public endpoint)"""
    
    # First, try to find the file in the database to get the correct path
    try:
        from app.service.db import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(FileRecord).where(FileRecord.filename == filename))
            file_record = result.scalar_one_or_none()
            
            if not file_record:
                raise HTTPException(
                    status_code=404,
                    detail="File not found"
                )
            
            file_path = file_record.file_path
            
            # Check if optimized version should be served
            if file_record.is_optimized and file_record.optimized_path:
                if os.path.exists(file_record.optimized_path):
                    file_path = file_record.optimized_path
            
            # Check if file exists
            if not os.path.exists(file_path):
                raise HTTPException(
                    status_code=404,
                    detail="File not found on disk"
                )
            
            # Determine media type
            media_type = file_record.mime_type
            
            return FileResponse(
                path=file_path,
                media_type=media_type,
                filename=file_record.original_filename
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving file: {str(e)}"
        )