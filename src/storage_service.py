import hashlib
from datetime import datetime
from tempfile import NamedTemporaryFile
from typing import BinaryIO

import boto3
from starlette.datastructures import UploadFile

from src.config import settings

hash_salt = "r2-profile-picture"


def get_s3_resource():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.cloudflare_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
    )


def upload_profile_picture(user_id: str, file: BinaryIO) -> str:
    s3 = get_s3_resource()

    hash_for_file = hashlib.md5(
        (str(user_id) + hash_salt).encode()
    ).hexdigest()  # nosec
    filename = f"{hash_for_file}.png"

    s3.upload_fileobj(file, settings.r2_profile_picture_bucket_name, filename)

    return filename


def get_profile_picture(filename) -> str:
    s3 = get_s3_resource()

    file = NamedTemporaryFile(delete=False)

    tempfile = open(file.name, "wb")
    s3.download_fileobj(settings.r2_profile_picture_bucket_name, filename, tempfile)
    tempfile.flush()
    return tempfile.name
