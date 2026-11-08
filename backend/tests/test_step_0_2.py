"""Unit tests for Step 0.2 Verification Script and Cloud Security Controls."""

from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from botocore.exceptions import ClientError

from scripts.verify_cloud_connections import (
    CloudVerificationSettings,
    check_tc_0_2_01_neon_connection,
    check_tc_0_2_02_s3_read_write,
    check_tc_0_2_03_bucket_privacy,
    check_tc_0_2_04_token_scope,
)


def get_mock_settings():
    return CloudVerificationSettings(
        DATABASE_URL_DIRECT="postgresql://user:pass@ep-xyz.ap-southeast-1.neon.tech/neondb?sslmode=require",
        S3_ENDPOINT="https://account.r2.cloudflarestorage.com",
        S3_BUCKET="quiz-files-prod",
        S3_ACCESS_KEY="mock_access_key",
        S3_SECRET_KEY="mock_secret_key",
        S3_REGION="auto",
    )


def test_tc_0_2_01_neon_connection_success():
    """TC-0.2-01: Neon connection succeeds when sslmode=require and query returns 1."""
    settings = get_mock_settings()
    with patch("scripts.verify_cloud_connections.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (1,)
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_connect.return_value.__enter__.return_value = mock_conn

        assert check_tc_0_2_01_neon_connection(settings) is True


def test_tc_0_2_01_neon_connection_missing_ssl():
    """TC-0.2-01: Warning and failure if sslmode=require is missing on Neon."""
    settings = get_mock_settings()
    settings.DATABASE_URL_DIRECT = "postgresql://user:pass@ep-xyz.ap-southeast-1.neon.tech/neondb"
    assert check_tc_0_2_01_neon_connection(settings) is False


def test_tc_0_2_02_s3_lifecycle_success():
    """TC-0.2-02: S3 put/get/delete lifecycle succeeds."""
    settings = get_mock_settings()
    with patch("scripts.verify_cloud_connections.boto3.client") as mock_client:
        mock_s3 = MagicMock()
        mock_body = MagicMock()
        mock_body.read.return_value = b"healthcheck_ok_step_0_2"
        mock_s3.get_object.return_value = {"Body": mock_body}
        mock_client.return_value = mock_s3

        assert check_tc_0_2_02_s3_read_write(settings) is True
        mock_s3.put_object.assert_called_once()
        mock_s3.delete_object.assert_called_once()


def test_tc_0_2_03_bucket_privacy():
    """TC-0.2-03: HTTP 403 Forbidden confirms private bucket."""
    settings = get_mock_settings()
    with patch("scripts.verify_cloud_connections.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = HTTPError(
            url="http://mock",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=None,  # pyright: ignore
        )
        assert check_tc_0_2_03_bucket_privacy(settings) is True


def test_tc_0_2_04_token_scope():
    """TC-0.2-04: Writing to unauthorized bucket is rejected."""
    settings = get_mock_settings()
    with patch("scripts.verify_cloud_connections.boto3.client") as mock_client:
        mock_s3 = MagicMock()
        mock_s3.put_object.side_effect = ClientError(
            error_response={"Error": {"Code": "AccessDenied"}},
            operation_name="PutObject",
        )
        mock_client.return_value = mock_s3

        assert check_tc_0_2_04_token_scope(settings) is True
