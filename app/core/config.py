from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core AWS/S3
    aws_region: str = "us-east-1"
    s3_bucket_name: str

    # Upload behavior
    upload_prefix: str = "uploads/"
    presign_expiration_seconds: int = 3600
    recommended_part_size_mb: int = 10

    # CORS
    allowed_origins: List[str] = ["*"]

    # Optional explicit creds (prefer default AWS resolution if unset)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        case_sensitive=False,
    )


settings = Settings()
