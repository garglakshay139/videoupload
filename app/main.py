from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.uploads import router as uploads_router


app = FastAPI(title="S3 Upload Presigner", version="0.1.0")

if settings.allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["ETag"],
    )


@app.get("/health")
def health():
  
    return {"status": "ok"}


app.include_router(uploads_router, prefix="/uploads", tags=["uploads"])