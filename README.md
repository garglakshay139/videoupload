# Backend (FastAPI)

FastAPI service that presigns S3 multipart uploads for large video files.

## Requirements
- Python 3.10+
- AWS credentials with S3 multipart permissions

## Setup
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Configure env
copy .env.example .env
```

## Run
```bash
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs.

## Endpoints
- POST `/uploads/initiate`
- GET `/uploads/presign-part`
- POST `/uploads/presign-parts`
- POST `/uploads/complete`
- DELETE `/uploads/abort`
- GET `/health`
