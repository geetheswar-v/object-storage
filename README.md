# Object Storage API

A self-hosted object storage API built with FastAPI. It supports uploading, listing, deleting, and serving files. Upload, delete, and list routes are protected by an API key, while the file access endpoint is public.

## Features

- **Minimal & Protected**: Protected upload, delete, and list endpoints using an API key
- **Web Optimization**: Automatic image/video optimization for web delivery
- **Type Safety**: Full TypeScript-style type hints with modern Python
- **Public File Access**: Direct file serving without authentication
- **Organized Storage**: Automatic file categorization by type

## Quick Start

### 1. Install

#### 1.1 Using UV
```bash
git clone https://github.com/geetheswar-v/object-storage.git
cd object-storage
uv sync
```

#### 1.2 Using Python venv
```bash
git clone https://github.com/geetheswar-v/object-storage.git
cd object-storage
python -m venv .venv
source .venv/bin/active # linux
pip install -r requiremnets.txt
```

### 2. Setup Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run Server

```bash
uv run python run.py
```

Server runs on `http://localhost:8000`

## API Endpoints

| Endpoint                   | Method | Auth | Description                       |
| -------------------------- | ------ | ---- | --------------------------------- |
| `/upload`                  | POST   | ✓    | Upload any file (no optimization) |
| `/upload/web`              | POST   | ✓    | Upload with web optimization      |
| `/list`                    | GET    | ✓    | List files with pagination        |
| `/delete/{file_id}`        | DELETE | ✓    | Delete file by ID                 |
| `/files/{filename}`        | GET    | —    | Public file access                |
| `/files/delete/{filename}` | DELETE | ✓    | Delete file by filename           |

## Web Optimization

The `/upload/web` endpoint optimizes:
- **Images**: JPEG, PNG, BMP, TIFF, WebP (excludes SVG)
- **Videos**: MP4, AVI, MOV, etc. (supported by ffmpeg)

> **Note**: Video optimization requires `ffmpeg` to be installed on the server. If not available, video files will be uploaded as-is without optimization.

Query parameters:
- `quality`: JPEG quality (range: `1–100`, default: `80`)
- `video_quality`: Video quality: `low`, `medium`, or `high` (default: `medium`) 
- `max_width`: Maximum width of the image (range: `100–4000`, default: `1200`)
- `max_height`: Maximum height of the image (range: `100–4000`, default: `800`)
- `preserve_alpha`: Preserve PNG transparency layer (default: `false`

## Usage Examples

### Upload Any File
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "x-api-key: api-key" \
  -F "file=@document.pdf"
```

### Upload with Web Optimization
```bash
curl -X POST "http://localhost:8000/upload/web?quality=90&max_width=1920&preserve_alpha=true" \
  -H "x-api-key: api-key" \
  -F "file=@image.png"
```

### List Files
```bash
curl -X GET "http://localhost:8000/list?page=1&per_page=10&file_type=image" \
  -H "x-api-key: api-key"
```

### Access File (Public)
```bash
curl "http://localhost:8000/files/filename.jpg"
```

## Contributions

Feel free to fork the project, open issues, or submit pull requests for improvements or new features.
