import datetime as dt
import re
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings
from app.dependencies.aws import get_s3_client
from app.models.schemas import (
    InitiateUploadRequest,
    InitiateUploadResponse,
    PresignPartResponse,
    PresignPartsRequest,
    PresignPartsResponse,
    PresignedPart,
    CompleteUploadRequest,
    AbortUploadRequest,
)


router = APIRouter()


def _sanitize_filename(name: str) -> str:
    name = name.replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name)
    return name or f"file-{uuid.uuid4()}"


def _build_key(original_name: str) -> str:
    today = dt.datetime.utcnow()
    uid = uuid.uuid4()
    safe = _sanitize_filename(original_name)
    date_path = today.strftime("%Y/%m/%d")
    prefix = settings.upload_prefix.rstrip("/")
    return f"{prefix}/{date_path}/{uid}-{safe}"


@router.post("/initiate", response_model=InitiateUploadResponse)
def initiate_upload(payload: InitiateUploadRequest):
    print("Hello from FastAPI!")
  
    s3 = get_s3_client()
    bucket = settings.s3_bucket_name
    print(bucket)
    key = _build_key(payload.fileName)
    try:
        create_args = {
            "Bucket": bucket,
            "Key": key,
        }
        if payload.contentType:
            create_args["ContentType"] = payload.contentType

        resp = s3.create_multipart_upload(**create_args)
        upload_id = resp["UploadId"]

        return InitiateUploadResponse(
            bucket=bucket,
            region=settings.aws_region,
            key=key,
            uploadId=upload_id,
            expiresInSeconds=settings.presign_expiration_seconds,
            recommendedPartSizeBytes=settings.recommended_part_size_mb * 1024 * 1024,
        )
    except (ClientError, BotoCoreError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate upload: {e}")


@router.get("/presign-part", response_model=PresignPartResponse)
def presign_part(
    key: str = Query(..., description="S3 object key"),
    uploadId: str = Query(..., description="S3 multipart upload ID"),
    partNumber: int = Query(..., ge=1, description="Part number starting at 1"),
):
    s3 = get_s3_client()
    try:
        url = s3.generate_presigned_url(
            ClientMethod="upload_part",
            Params={
                "Bucket": settings.s3_bucket_name,
                "Key": key,
                "UploadId": uploadId,
                "PartNumber": partNumber,
            },
            ExpiresIn=settings.presign_expiration_seconds,
            HttpMethod="PUT",
        )
        return PresignPartResponse(url=url, expiresInSeconds=settings.presign_expiration_seconds)
    except (ClientError, BotoCoreError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to presign part: {e}")


@router.post("/presign-parts", response_model=PresignPartsResponse)
def presign_parts(payload: PresignPartsRequest):
    s3 = get_s3_client()
    print("presign_parts called with payload:", payload)
    parts = []
    try:
        for pn in payload.partNumbers:
            if pn < 1:
                raise HTTPException(status_code=400, detail="partNumbers must be >= 1")
            url = s3.generate_presigned_url(
                ClientMethod="upload_part",
                Params={
                    "Bucket": settings.s3_bucket_name,
                    "Key": payload.key,
                    "UploadId": payload.uploadId,
                    "PartNumber": pn,
                },
                ExpiresIn=settings.presign_expiration_seconds,
                HttpMethod="PUT",
            )
            parts.append(PresignedPart(partNumber=pn, url=url))
        print("end of presign_parts")
        return PresignPartsResponse(parts=parts, expiresInSeconds=settings.presign_expiration_seconds)
    except (ClientError, BotoCoreError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to presign parts: {e}")


@router.post("/complete")
def complete_upload(payload: CompleteUploadRequest):
    s3 = get_s3_client()
    print("complete_upload called with payload:", payload)
    try:
        result = s3.complete_multipart_upload(
            Bucket=settings.s3_bucket_name,
            Key=payload.key,
            UploadId=payload.uploadId,
            MultipartUpload={"Parts": [p.model_dump() for p in payload.parts]},
        )
        return {
            "bucket": settings.s3_bucket_name,
            "key": payload.key,
            "location": result.get("Location"),
            "versionId": result.get("VersionId"),
            "etag": result.get("ETag"),
        }
    except (ClientError, BotoCoreError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete upload: {e}")


@router.delete("/abort")
def abort_upload(payload: AbortUploadRequest):
    s3 = get_s3_client()
    try:
        s3.abort_multipart_upload(
            Bucket=settings.s3_bucket_name,
            Key=payload.key,
            UploadId=payload.uploadId,
        )
        return {"aborted": True}
    except (ClientError, BotoCoreError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to abort upload: {e}")
