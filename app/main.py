import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes import router
from app.config import settings
from app.service.db import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await create_db_and_tables()

    if not os.path.exists(settings.upload_directory):
        os.makedirs(settings.upload_directory)
    
    for file_type in ["image", "video", "document", "audio", "other"]:
        category_dir = os.path.join(settings.upload_directory, file_type)
        if not os.path.exists(category_dir):
            os.makedirs(category_dir, exist_ok=True)
    
    yield

app = FastAPI(
    title="Object Storage API",
    description="Self-hosted object storage API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Object Storage API"}

