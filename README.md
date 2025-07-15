# FastAPI Object Storage API

A self-hosted object storage API built with FastAPI. It supports uploading, listing, deleting, and serving files. Upload, delete, and list routes are protected by an API key, while the file access endpoint is public.

## Features

- Protected upload, delete, and list endpoints using an API key
- Public file access via `/files/{filename}`
- Optional PostgreSQL integration for file metadata
- Local file storage with configurable upload directory
- File type and size validation
- Image Optimization for Web Image Serving

## Setup Instructions

### 1. Clone & Install

```bash
git clone https://github.com/geetheswar-v/object-storage.git
cd object_storage_api
uv sync # If using uv
pip install -r requirements.txt
````

### 2. Environment Configuration

Create a `.env` file in the root directory with the following content:

```env
API_KEY=url_safe_key
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=10
DATABASE_URL=postgresql://fastapi_user:yourpassword@localhost/object_storage
```

## Running the Server

```bash
python run.py
```

The application will be accessible at `http://localhost:8000`.

## API Endpoints

| Endpoint             | Method | Auth Required   | Description             |
| -------------------- | ------ | --------------- | ----------------------- |
| `/upload`            | POST   | Yes (x-api-key) | Upload a file           |
| `/list`              | GET    | Yes (x-api-key) | List all uploaded files |
| `/delete/{filename}` | DELETE | Yes (x-api-key) | Delete a specific file  |
| `/files/{filename}`  | GET    | No              | Public file access      |

## Example Upload Request

```bash
curl -X POST http://localhost:8000/upload \
  -H "x-api-key: key" \
  -F "file=@mydocument.pdf"
```

## Contributions

Feel free to fork the project, open issues, or submit pull requests for improvements or new features.
