import os
import aiofiles
from pathlib import Path
from app.core.config import settings
import logging

logger = logging.getLogger("cortexflow")

# Ensure storage directory exists
upload_dir = os.path.abspath(settings.UPLOAD_DIR)
os.makedirs(upload_dir, exist_ok=True)

async def save_file_locally(file_bytes: bytes, filename: str) -> str:
    target_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, filename)
    
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_bytes)
    
    # Auto-detect Cloud Render environment URL
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_url:
        return f"{render_url.rstrip('/')}/storage/{filename}"
    
    return f"{settings.STATIC_URL.rstrip('/')}/{filename}"

async def upload_file_artifact(data: bytes, filename: str, content_type: str = "application/octet-stream") -> str:
    """
    Saves the generated file (PPT, PDF, Image) locally or to S3, returning a downloadable URL.
    """
    if settings.STORAGE_TYPE == "s3" and settings.AWS_ACCESS_KEY_ID:
        try:
            import boto3
            s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            s3.put_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=filename,
                Body=data,
                ContentType=content_type
            )
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET_NAME, "Key": filename},
                ExpiresIn=3600 * 24
            )
            return url
        except Exception as e:
            logger.error(f"S3 upload failed: {e}. Falling back to local storage.")
    
    # Fallback to local storage
    return await save_file_locally(data, filename)
