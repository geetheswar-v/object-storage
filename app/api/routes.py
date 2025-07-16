import os
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Path
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import verify_api_key, get_db_session
from app.service.crud import (
    create_file,
    get_file_by_id,
    get_file_by_filename,
    get_files_paginated,
    delete_file
)
from app.service.models import FileType, FileListResponse, UploadResponse
from app.service.db import check_db_connection
from app.utils.file_utils import (
    get_file_type_from_mime,
    generate_unique_filename,
    create_file_path,
    ensure_directory_exists,
    get_mime_type
)
from app.utils.web_utils import (
    optimize_image_for_web,
    optimize_video_for_web,
    is_optimizable_image,
    is_optimizable_video
)
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    db_connected = await check_db_connection()
    return {
        "status": "healthy" if db_connected else "unhealthy",
        "database": "connected" if db_connected else "disconnected",
        "message": "Object Storage API is running"
    }


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    _: bool = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db_session)
):
    """Upload any file type without optimization"""
    
    # Check file size
    if file.size and file.size > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    # Get file info
    mime_type = file.content_type or get_mime_type(file.filename)
    file_type = get_file_type_from_mime(mime_type)
    unique_filename = generate_unique_filename(file.filename)
    file_path = create_file_path(settings.upload_directory, file_type, unique_filename)
    
    # Ensure directory exists
    ensure_directory_exists(os.path.dirname(file_path))
    
    try:
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Create database record
        file_record = await create_file(
            session=session,
            filename=unique_filename,
            original_filename=file.filename,
            file_type=file_type,
            mime_type=mime_type,
            file_size=len(content),
            file_path=file_path
        )
        
        return UploadResponse(
            id=file_record.id,
            filename=unique_filename,
            original_filename=file.filename,
            file_type=file_type,
            mime_type=mime_type,
            file_size=len(content),
            url=f"/files/{unique_filename}",
            message="File uploaded successfully"
        )
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/upload/web", response_model=UploadResponse)
async def upload_file_web_optimized(
    file: UploadFile = File(...),
    quality: int = Query(80, ge=1, le=100, description="Image quality (1-100)"),
    video_quality: str = Query("medium", description="Video quality: low, medium, high"),
    max_width: int = Query(1200, ge=100, le=4000, description="Maximum width"),
    max_height: int = Query(800, ge=100, le=4000, description="Maximum height"),
    preserve_alpha: bool = Query(False, description="Preserve PNG transparency"),
    _: bool = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db_session)
):
    """Upload and optimize images/videos for web usage"""
    
    # Validate video quality parameter
    if video_quality not in ["low", "medium", "high"]:
        raise HTTPException(
            status_code=400,
            detail="video_quality must be one of: low, medium, high"
        )
    
    # Check file size
    if file.size and file.size > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    # Get file info
    mime_type = file.content_type or get_mime_type(file.filename)
    file_type = get_file_type_from_mime(mime_type)
    
    # Check if file can be optimized
    if not (is_optimizable_image(mime_type) or is_optimizable_video(mime_type)):
        raise HTTPException(
            status_code=400,
            detail="Web optimization only supports images (JPEG, PNG, BMP, TIFF, WebP) and videos"
        )
    
    unique_filename = generate_unique_filename(file.filename)
    original_path = create_file_path(settings.upload_directory, file_type, unique_filename)
    optimized_path = create_file_path(settings.upload_directory, file_type, f"web_{unique_filename}")
    
    # Ensure directory exists
    ensure_directory_exists(os.path.dirname(original_path))
    
    try:
        # Save original file
        async with aiofiles.open(original_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Optimize file
        success = False
        error_msg = None
        
        if is_optimizable_image(mime_type):
            success, error_msg = optimize_image_for_web(
                original_path,
                optimized_path,
                quality=quality,
                max_width=max_width,
                max_height=max_height,
                preserve_alpha=preserve_alpha
            )
        elif is_optimizable_video(mime_type):
            success, error_msg = optimize_video_for_web(
                original_path,
                optimized_path,
                max_width=max_width,
                max_height=max_height,
                quality=video_quality
            )
        
        if not success:
            # Use original file if optimization fails
            optimized_path = original_path
            print(f"Optimization failed: {error_msg}")
        
        # Use optimized file size
        final_size = os.path.getsize(optimized_path)
        
        # Create database record
        file_record = await create_file(
            session=session,
            filename=unique_filename,
            original_filename=file.filename,
            file_type=file_type,
            mime_type=mime_type,
            file_size=final_size,
            file_path=optimized_path
        )
        
        # Clean up original file if optimization was successful
        if success and optimized_path != original_path:
            os.remove(original_path)
        
        return UploadResponse(
            id=file_record.id,
            filename=unique_filename,
            original_filename=file.filename,
            file_type=file_type,
            mime_type=mime_type,
            file_size=final_size,
            url=f"/files/{unique_filename}",
            message="File uploaded and optimized for web" if success else "File uploaded (optimization failed)"
        )
        
    except Exception as e:
        # Clean up on error
        for path in [original_path, optimized_path]:
            if os.path.exists(path):
                os.remove(path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/list", response_model=FileListResponse)
async def list_files(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    file_type: FileType | None = Query(None, description="Filter by file type"),
    _: bool = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db_session)
):
    """List files with pagination and filtering"""
    return await get_files_paginated(
        session=session,
        page=page,
        per_page=per_page,
        file_type=file_type
    )


@router.delete("/delete/{file_id}")
async def delete_file_by_id(
    file_id: str = Path(..., description="File ID to delete"),
    _: bool = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db_session)
):
    """Delete file by ID"""
    file_record = await get_file_by_id(session, file_id)
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Remove physical file
    if os.path.exists(file_record.file_path):
        try:
            os.remove(file_record.file_path)
        except Exception as e:
            print(f"Error removing file {file_record.file_path}: {e}")
    
    # Remove database record
    success = await delete_file(session, file_id)
    
    if success:
        return {"message": "File deleted successfully", "file_id": file_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete file from database")


@router.get("/files/{filename}")
async def get_file(
    filename: str = Path(..., description="Filename to retrieve")
):
    """Get file by filename (public endpoint)"""
    try:
        from app.service.db import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            file_record = await get_file_by_filename(session, filename)
            
            if not file_record:
                raise HTTPException(status_code=404, detail="File not found")
            
            if not os.path.exists(file_record.file_path):
                raise HTTPException(status_code=404, detail="File not found on disk")
            
            return FileResponse(
                path=file_record.file_path,
                media_type=file_record.mime_type,
                filename=file_record.original_filename
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")


@router.delete("/files/delete/{filename}")
async def delete_file_by_filename(
    filename: str = Path(..., description="Filename to delete"),
    _: bool = Depends(verify_api_key),
    session: AsyncSession = Depends(get_db_session)
):
    """Delete file by filename"""
    file_record = await get_file_by_filename(session, filename)
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Remove physical file
    if os.path.exists(file_record.file_path):
        try:
            os.remove(file_record.file_path)
        except Exception as e:
            print(f"Error removing file {file_record.file_path}: {e}")
    
    # Remove database record
    success = await delete_file(session, file_record.id)
    
    if success:
        return {"message": "File deleted successfully", "filename": filename}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete file from database")
