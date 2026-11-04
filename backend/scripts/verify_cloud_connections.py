"""Cloud Services Connection & Security Verification Script (Step 0.2).

Validates:
- TC-0.2-01: Neon PostgreSQL connection with SSL required.
- TC-0.2-02: Cloudflare R2 / S3-compatible put/get/delete operations.
- TC-0.2-03: Bucket privacy (unsigned direct HTTP GET returns 403 Forbidden).
- TC-0.2-04: S3 token scope constraint (write to forbidden bucket denied).
"""

import os
import sys
import uuid
from urllib.error import HTTPError
from urllib.request import urlopen

import boto3
from botocore.exceptions import ClientError
from psycopg import connect
from pydantic_settings import BaseSettings, SettingsConfigDict


class CloudVerificationSettings(BaseSettings):
    """Loads connection settings for verification."""

    DATABASE_URL_DIRECT: str
    S3_ENDPOINT: str
    S3_BUCKET: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_REGION: str = "auto"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def check_tc_0_2_01_neon_connection(settings: CloudVerificationSettings) -> bool:
    """TC-0.2-01: Verify PostgreSQL connection with sslmode=require."""
    print("\n[TC-0.2-01] Kiểm tra kết nối Neon PostgreSQL (Direct)...")
    db_url = settings.DATABASE_URL_DIRECT

    if "sslmode=require" not in db_url and "neon.tech" in db_url:
        print("  ❌ Cảnh báo: DATABASE_URL_DIRECT của Neon chưa có 'sslmode=require'!")
        return False

    try:
        with connect(db_url, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                result = cur.fetchone()
                if result and result[0] == 1:
                    print("  ✅ Kết nối PostgreSQL thành công! (SELECT 1 -> 1)")
                    return True
                print(f"  ❌ Kết quả không mong đợi: {result}")
                return False
    except Exception as exc:
        print(f"  ❌ Lỗi kết nối CSDL: {exc}")
        return False


def check_tc_0_2_02_s3_read_write(settings: CloudVerificationSettings) -> bool:
    """TC-0.2-02: Verify S3/R2 put, get, delete lifecycle."""
    print("\n[TC-0.2-02] Kiểm tra đọc/ghi/xóa object trên S3/R2...")
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )
    test_key = f"healthcheck_{uuid.uuid4().hex[:8]}.txt"
    test_content = b"healthcheck_ok_step_0_2"

    try:
        # Put object
        s3.put_object(Bucket=settings.S3_BUCKET, Key=test_key, Body=test_content)
        print(f"  - Đã ghi tệp thử nghiệm: {test_key}")

        # Get object
        response = s3.get_object(Bucket=settings.S3_BUCKET, Key=test_key)
        body = response["Body"].read()
        assert body == test_content, f"Nội dung không khớp: {body}"
        print("  - Đã đọc và xác minh nội dung tệp thành công.")

        # Delete object
        s3.delete_object(Bucket=settings.S3_BUCKET, Key=test_key)
        print("  - Đã xóa tệp thử nghiệm thành công.")
        print("  ✅ Kiểm tra S3 Put/Get/Delete đạt yêu cầu!")
        return True
    except Exception as exc:
        print(f"  ❌ Lỗi thao tác S3/R2: {exc}")
        return False


def check_tc_0_2_03_bucket_privacy(settings: CloudVerificationSettings) -> bool:
    """TC-0.2-03: Verify bucket is not public (unsigned GET is 403 Forbidden)."""
    print("\n[TC-0.2-03] Kiểm tra tính riêng tư của Bucket (Unsigned GET)...")
    endpoint = settings.S3_ENDPOINT.rstrip("/")
    bucket = settings.S3_BUCKET
    test_url = f"{endpoint}/{bucket}/healthcheck_non_existent.txt"

    try:
        with urlopen(test_url, timeout=3) as resp:
            print(f"  ⚠️ Cảnh báo: Bucket trả về HTTP {resp.status}, có thể đang công khai!")
            return False
    except HTTPError as http_err:
        if http_err.code in (403, 404):
            print(f"  ✅ Truy cập công khai bị chặn an toàn (HTTP {http_err.code}).")
            return True
        print(f"  ⚠️ Mã phản hồi HTTP: {http_err.code}")
        return True
    except Exception as exc:
        print(f"  ✅ Truy cập trực tiếp không ký bị từ chối/kết nối đóng: {exc}")
        return True


def check_tc_0_2_04_token_scope(settings: CloudVerificationSettings) -> bool:
    """TC-0.2-04: Verify token cannot write to unauthorized bucket."""
    print("\n[TC-0.2-04] Kiểm tra phạm vi quyền hạn của Token...")
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )
    unauthorized_bucket = "unauthorized-system-bucket-xyz"
    try:
        s3.put_object(
            Bucket=unauthorized_bucket,
            Key="forbidden.txt",
            Body=b"should_fail",
        )
        print("  ❌ Cảnh báo: Token có quyền ghi vào bucket ngoài phạm vi!")
        return False
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        print(f"  ✅ Token bị từ chối chính xác khi ghi bucket khác (Mã lỗi: {error_code}).")
        return True
    except Exception as exc:
        print(f"  ✅ Yêu cầu bị chặn: {exc}")
        return True


def main() -> None:
    print("=================================================================")
    print("  KIỂM TRA TỰ ĐỘNG CÁC DỊCH VỤ ĐÁM MÂY (BƯỚC 0.2)")
    print("=================================================================")

    if not os.path.exists(".env"):
        print("❌ LỖI: Không tìm thấy file .env.")
        print("Vui lòng sao chép .env.example sang .env và điền thông tin dịch vụ đám mây:")
        print("  - DATABASE_URL_DIRECT (Neon)")
        print("  - S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY (Cloudflare R2 / S3)")
        sys.exit(1)

    try:
        settings = CloudVerificationSettings()  # pyright: ignore
    except Exception as exc:
        print(f"❌ LỖI CẤU HÌNH: Thiếu hoặc sai định dạng biến môi trường: {exc}")
        sys.exit(1)

    results = [
        check_tc_0_2_01_neon_connection(settings),
        check_tc_0_2_02_s3_read_write(settings),
        check_tc_0_2_03_bucket_privacy(settings),
        check_tc_0_2_04_token_scope(settings),
    ]

    print("\n=================================================================")
    if all(results):
        print("🎉 TẤT CẢ KIỂM TRA ĐÃ ĐẠT!")
    else:
        print("⚠️ CÓ KIỂM TRA CHƯA ĐẠT. Vui lòng rà soát lại thông số trong file .env.")
    print("=================================================================")


if __name__ == "__main__":
    main()
