import hashlib
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import BinaryIO

import boto3

from src.config import settings

hash_salt = "r2-profile-picture"

LOCAL_UPLOADS_DIR = Path("/app/uploads/profile_pictures")


def _use_local_storage() -> bool:
    """Returns True if local storage should be used (R2 not configured)."""
    return not settings.cloudflare_account_id


def get_s3_resource():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.cloudflare_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
    )


def upload_profile_picture(user_id: str, file: BinaryIO) -> str:
    hash_for_file = hashlib.md5(
        (str(user_id) + hash_salt).encode()
    ).hexdigest()  # nosec
    filename = f"{hash_for_file}.png"

    if _use_local_storage():
        LOCAL_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        filepath = LOCAL_UPLOADS_DIR / filename
        with open(filepath, "wb") as f:
            f.write(file.read())
        return filename

    s3 = get_s3_resource()
    s3.upload_fileobj(file, settings.r2_profile_picture_bucket_name, filename)

    return filename


def get_profile_picture(filename: str) -> str:
    if _use_local_storage():
        filepath = LOCAL_UPLOADS_DIR / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Profile picture not found: {filename}")
        return str(filepath)

    s3 = get_s3_resource()

    file = NamedTemporaryFile(delete=False)

    tempfile = open(file.name, "wb")
    s3.download_fileobj(settings.r2_profile_picture_bucket_name, filename, tempfile)
    tempfile.flush()
    return tempfile.name
