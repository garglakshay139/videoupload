from typing import List, Optional
from pydantic import BaseModel, Field


class InitiateUploadRequest(BaseModel):
    fileName: str = Field(..., description="Original filename from client")
    contentType: Optional[str] = Field(None, description="MIME type, e.g., video/mp4")


class InitiateUploadResponse(BaseModel):
    bucket: str
    region: str
    key: str
    uploadId: str
    expiresInSeconds: int
    recommendedPartSizeBytes: int


class PresignPartResponse(BaseModel):
    url: str
    expiresInSeconds: int


class CompletedPart(BaseModel):
    ETag: str
    PartNumber: int


class CompleteUploadRequest(BaseModel):
    key: str
    uploadId: str
    parts: List[CompletedPart]


class AbortUploadRequest(BaseModel):
    key: str
    uploadId: str


class PresignedPart(BaseModel):
    partNumber: int
    url: str


class PresignPartsRequest(BaseModel):
    key: str
    uploadId: str
    partNumbers: List[int]


class PresignPartsResponse(BaseModel):
    parts: List[PresignedPart]
    expiresInSeconds: int
