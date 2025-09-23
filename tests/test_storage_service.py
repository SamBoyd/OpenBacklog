import hashlib
from unittest.mock import MagicMock, mock_open, patch

import pytest
from hamcrest import assert_that, equal_to

from src import storage_service
from src.config import settings


def test_s3_resource_is_setup_correctly():
    expected_endpoint = (
        f"https://{settings.cloudflare_account_id}.r2.cloudflarestorage.com"
    )
    with patch("src.storage_service.boto3.client") as mock_boto3_client:
        mock_s3_client = MagicMock()
        # Setup the nested attributes for dummy s3 resource
        mock_boto3_client.return_value = mock_s3_client

        s3 = storage_service.get_s3_resource()
        mock_boto3_client.assert_called_once_with(
            "s3",
            endpoint_url=expected_endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
        )
        assert_that(s3, equal_to(mock_s3_client))


@patch("src.storage_service.NamedTemporaryFile")
@patch("src.storage_service.get_s3_resource")
def test_can_get_a_profile_picture_for_a_user(
    mock_get_s3_resource, mock_named_temporary_file
):
    filename = "3d6b91ba261ed243ee4a377164a1ab90.png"
    mock_s3_resource = MagicMock()
    mock_get_s3_resource.return_value = mock_s3_resource

    mock_named_temporary_file.return_value.name = "mock_name"

    mock_returned_file = MagicMock()
    mock_file = MagicMock()

    with patch("builtins.open", mock_open(read_data=b"data")) as mock_file_open:
        mock_file_open.return_value = mock_file
        mock_s3_resource.download_fileobj.return_value = mock_returned_file

        file = storage_service.get_profile_picture(filename)

        mock_s3_resource.download_fileobj.assert_called_once_with(
            settings.r2_profile_picture_bucket_name, filename, mock_file
        )
        mock_file_open.assert_called_once_with("mock_name", "wb")
        assert_that(file, equal_to(mock_file.name))


def test_can_upload_a_profile_picture_for_a_user():
    user_id = "user123"
    file = MagicMock()

    with patch("src.storage_service.get_s3_resource") as mock_get_s3_resource:
        mock_s3_resource = MagicMock()
        mock_get_s3_resource.return_value = mock_s3_resource

        storage_service.upload_profile_picture(user_id, file)

        mock_s3_resource.upload_fileobj.assert_called_once_with(
            file,
            settings.r2_profile_picture_bucket_name,
            "05db73715990652447f1476a4f3b99c1.png",
        )
