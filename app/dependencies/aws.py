import boto3
from botocore.config import Config

from app.core.config import settings


def get_s3_client():
    session = boto3.session.Session(
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
        aws_session_token=settings.aws_session_token or None,
        region_name=settings.aws_region,
    )
    # Force Signature Version 4 for presigned URLs to avoid legacy SigV2
    cfg = Config(signature_version="s3v4", s3={"addressing_style": "virtual"})
    return session.client("s3", config=cfg)
