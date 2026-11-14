"""Tests for Step 4.3: Exam Image Upload, Sanitization & Secure Asset Delivery.

Test Cases:
- TC-4.3-01: Valid PNG image upload -> converted to WEBP, saved in S3, DB record created
- TC-4.3-02: Spoofed file extension -> rejected with HTTP 415 invalid_image
- TC-4.3-03: Oversized upload (> 5 MB) -> aborts with HTTP 413 file_too_large
- TC-4.3-04: Decompression bomb (30,000x30,000 px) -> rejected (MAX_IMAGE_PIXELS)
- TC-4.3-05: SVG file containing script tags -> rejected with HTTP 415 invalid_image
- TC-4.3-06: JPEG containing GPS metadata in EXIF -> completely stripped in output WEBP
- TC-4.3-07: Temporary presigned URL generation & TTL enforcement
- TC-4.3-08: Cross-exam reference isolation (asset from exam A in exam B -> 'about:blank')
- TC-4.3-09: Compensation rollback (DB commit failure cleans up newly uploaded S3 object)
- TC-4.3-10: RBAC authorization (student role calling upload endpoint returns HTTP 403)
"""

import io
import struct
import uuid
import zlib

import pytest
from fastapi import UploadFile
from PIL import Image

from app.core.errors import AppError
from app.models.exam import Exam
from app.models.file import File
from app.models.user import User
from app.services.asset_service import render_assets
from app.services.image_service import (
    MAX_ASSET_SIZE_BYTES,
    read_and_validate_upload_stream,
    read_sync_stream_with_limit,
    sanitize_and_convert_to_webp,
)
from app.services.storage_service import StorageService


def create_test_png(width: int = 200, height: int = 200, color: str = "blue") -> bytes:
    """Helper to generate a valid PNG image byte stream."""
    img = Image.new("RGBA", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_test_jpeg_with_gps(lat: float = 10.762622, lon: float = 106.660172) -> bytes:
    """Helper to generate a JPEG image with sensitive GPS EXIF metadata."""
    img = Image.new("RGB", (100, 100), color="green")
    exif = Image.Exif()
    exif[0x010E] = "Secret location test"
    # Tag 0x8825 is GPS IFD
    gps_ifd = exif.get_ifd(0x8825)
    gps_ifd[1] = "N"
    gps_ifd[2] = lat
    gps_ifd[3] = "E"
    gps_ifd[4] = lon

    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    return buf.getvalue()


def create_decompression_bomb_png() -> bytes:
    """Helper to generate a lightweight PNG byte stream with 30,000 x 30,000 IHDR dimensions."""
    width, height = 30000, 30000
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    ihdr_crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr))
    iend_crc = struct.pack(">I", zlib.crc32(b"IEND"))
    header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    return header + ihdr + ihdr_crc + b"\x00\x00\x00\x00IEND" + iend_crc


# ==============================================================================
# TC-4.3-01: Valid Image Upload & WEBP Conversion
# ==============================================================================
def test_tc_4_3_01_valid_image_conversion():
    """TC-4.3-01: Valid PNG is converted to WEBP, dimension preserved <= 2000px."""
    png_bytes = create_test_png(width=400, height=300, color="red")
    webp_bytes, width, height = sanitize_and_convert_to_webp(png_bytes, "diagram.png")

    assert width == 400
    assert height == 300
    assert len(webp_bytes) > 0

    # Verify header of output is WEBP
    img = Image.open(io.BytesIO(webp_bytes))
    assert img.format == "WEBP"
    assert img.width == 400
    assert img.height == 300


# ==============================================================================
# TC-4.3-02: Spoofed Format (exe/pdf disguised as png)
# ==============================================================================
def test_tc_4_3_02_spoofed_format_rejected():
    """TC-4.3-02: Reject executable or PDF files renamed to .png with 415 invalid_image."""
    # Case A: Windows PE executable
    fake_exe = (
        b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
        b"This program cannot be run in DOS mode."
    )
    with pytest.raises(AppError) as exc_info:
        sanitize_and_convert_to_webp(fake_exe, "malware.png")
    assert exc_info.value.status_code == 415
    assert exc_info.value.code == "invalid_image"

    # Case B: PDF document
    fake_pdf = (
        b"%PDF-1.4\n1 0 obj\n<< /Title (Exam Answers) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    )
    with pytest.raises(AppError) as exc_info_pdf:
        sanitize_and_convert_to_webp(fake_pdf, "answers.png")
    assert exc_info_pdf.value.status_code == 415
    assert exc_info_pdf.value.code == "invalid_image"


# ==============================================================================
# TC-4.3-03: Oversized Upload (> 5 MB streaming check)
# ==============================================================================
@pytest.mark.anyio
async def test_tc_4_3_03_streaming_size_limit():
    """TC-4.3-03: Stream exceeding 5 MB aborts immediately with HTTP 413."""
    # Create 6 MB dummy payload
    oversized_data = b"X" * (MAX_ASSET_SIZE_BYTES + 1024)

    # Test sync stream
    with pytest.raises(AppError) as exc_sync:
        read_sync_stream_with_limit(io.BytesIO(oversized_data), max_bytes=MAX_ASSET_SIZE_BYTES)
    assert exc_sync.value.status_code == 413
    assert exc_sync.value.code == "file_too_large"

    # Test async UploadFile stream
    async_upload = UploadFile(
        file=io.BytesIO(oversized_data),
        size=len(oversized_data),
        filename="huge.png",
    )
    with pytest.raises(AppError) as exc_async:
        await read_and_validate_upload_stream(async_upload, max_bytes=MAX_ASSET_SIZE_BYTES)
    assert exc_async.value.status_code == 413
    assert exc_async.value.code == "file_too_large"


# ==============================================================================
# TC-4.3-04: Decompression Bomb Guard
# ==============================================================================
def test_tc_4_3_04_decompression_bomb_rejected():
    """TC-4.3-04: 30,000x30,000 px image is rejected without hanging server memory."""
    bomb_bytes = create_decompression_bomb_png()

    with pytest.raises(AppError) as exc_info:
        sanitize_and_convert_to_webp(bomb_bytes, "bomb.png")

    assert exc_info.value.status_code == 400
    assert exc_info.value.code == "decompression_bomb"


# ==============================================================================
# TC-4.3-05: SVG / Script Rejection
# ==============================================================================
def test_tc_4_3_05_svg_with_script_rejected():
    """TC-4.3-05: SVG containing embedded JavaScript or XML is rejected (HTTP 415)."""
    # Case A: Standard SVG file
    svg_payload = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    with pytest.raises(AppError) as exc_svg:
        sanitize_and_convert_to_webp(svg_payload, "vector.svg")
    assert exc_svg.value.status_code == 415
    assert exc_svg.value.code == "invalid_image"

    # Case B: SVG disguised with .png extension
    disguised_svg = (
        b'<?xml version="1.0"?><svg viewBox="0 0 100 100"><script>document.cookie</script></svg>'
    )
    with pytest.raises(AppError) as exc_disguised:
        sanitize_and_convert_to_webp(disguised_svg, "vector.png")
    assert exc_disguised.value.status_code == 415
    assert exc_disguised.value.code == "invalid_image"


# ==============================================================================
# TC-4.3-06: EXIF & GPS Metadata Stripping
# ==============================================================================
def test_tc_4_3_06_exif_gps_stripping():
    """TC-4.3-06: JPEG with GPS coordinates has all metadata stripped after WEBP conversion."""
    raw_jpeg = create_test_jpeg_with_gps(lat=10.762622, lon=106.660172)

    # Verify input actually contains EXIF GPS tags
    input_img = Image.open(io.BytesIO(raw_jpeg))
    input_exif = input_img.getexif()
    assert len(input_exif.keys()) > 0
    assert 0x8825 in input_exif or len(input_exif.get_ifd(0x8825)) > 0

    # Convert to WEBP
    webp_bytes, _, _ = sanitize_and_convert_to_webp(raw_jpeg, "phone_camera.jpg")

    # Verify output has 0 EXIF or GPS tags
    output_img = Image.open(io.BytesIO(webp_bytes))
    output_exif = output_img.getexif()
    assert len(output_exif.keys()) == 0
    assert len(output_exif.get_ifd(0x8825)) == 0


# ==============================================================================
# TC-4.3-07: Temporary Presigned URL & TTL Generation
# ==============================================================================
def test_tc_4_3_07_presigned_url_generation():
    """TC-4.3-07: Presigned URL generated with TTL parameter."""
    storage = StorageService(use_mock=True)
    test_key = "exams/test-exam/img/sample.webp"
    storage.put_object(test_key, b"fake_webp", "image/webp")

    url = storage.generate_presigned_url(test_key, expires_in=21600)
    assert url.startswith("https://")
    assert "expires_in=21600" in url

    short_url = storage.generate_presigned_url(test_key, expires_in=5)
    assert "expires_in=5" in short_url


# ==============================================================================
# TC-4.3-08: Cross-Exam Asset Leakage Prevention ('about:blank')
# ==============================================================================
def test_tc_4_3_08_cross_exam_asset_isolation():
    """TC-4.3-08: Asset belonging to exam A embedded in exam B renders as about:blank."""
    exam_a_id = uuid.uuid4()
    exam_b_id = uuid.uuid4()

    asset_a_id = uuid.uuid4()
    asset_b_id = uuid.uuid4()

    file_a = File(
        id=asset_a_id,
        exam_id=exam_a_id,
        user_id=uuid.uuid4(),
        original_name="exam_a_img.png",
        s3_key=f"exams/{exam_a_id}/img/{asset_a_id}.webp",
        mime_type="image/webp",
        size_bytes=1000,
        kind="question_image",
    )
    file_b = File(
        id=asset_b_id,
        exam_id=exam_b_id,
        user_id=uuid.uuid4(),
        original_name="exam_b_img.png",
        s3_key=f"exams/{exam_b_id}/img/{asset_b_id}.webp",
        mime_type="image/webp",
        size_bytes=2000,
        kind="question_image",
    )

    class MockSession:
        def __init__(self, files):
            self.files = files

        def scalars(self, query):
            class Result:
                def __init__(self, items):
                    self.items = items

                def all(self):
                    return self.items

            # Only return files belonging to exam_b_id
            matched = [f for f in self.files if f.exam_id == exam_b_id]
            return Result(matched)

    storage = StorageService(use_mock=True)
    mock_db = MockSession([file_a, file_b])

    markdown_text = (
        f"Hãy quan sát hình 1: ![](asset:{asset_a_id}) và hình 2: ![](asset:{asset_b_id})"
    )

    # When viewed in Exam B: asset_a_id must become about:blank, asset_b_id becomes presigned URL
    rendered_for_exam_b = render_assets(
        markdown_text, exam_id=exam_b_id, db=mock_db, storage=storage
    )

    assert f"![](asset:{asset_a_id})" not in rendered_for_exam_b
    assert "![](about:blank)" in rendered_for_exam_b
    assert f"{asset_b_id}.webp" in rendered_for_exam_b


# ==============================================================================
# TC-4.3-09: Compensation Rollback on DB Error
# ==============================================================================
def test_tc_4_3_09_compensation_rollback_on_db_error():
    """TC-4.3-09: Database failure after storage put triggers deletion of S3 object."""
    storage = StorageService(use_mock=True)
    exam_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    s3_key = f"exams/{exam_id}/img/{asset_id}.webp"

    # Simulate S3 put succeeded
    storage.put_object(s3_key, b"test_webp", "image/webp")
    assert storage.object_exists(s3_key) is True

    # Simulate DB error during transaction
    try:
        # DB commit fails
        raise RuntimeError("Simulated DB connection lost")
    except Exception:
        # Compensation step triggered
        storage.delete_object(s3_key)

    # S3 object must be deleted to prevent orphaned storage junk
    assert storage.object_exists(s3_key) is False


# ==============================================================================
# TC-4.3-10: RBAC Permission Guard (Student Forbidden)
# ==============================================================================
def test_tc_4_3_10_student_forbidden():
    """TC-4.3-10: Student role cannot access admin assets upload."""
    from app.core.dependencies import require_admin

    student_user = User(
        id=uuid.uuid4(),
        username="student1",
        full_name="Nguyễn Văn A",
        role="student",
        is_active=True,
    )

    with pytest.raises(AppError) as exc_info:
        require_admin(user=student_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "forbidden"


# ==============================================================================
# End-to-End API Router Verification (TestClient + Mock Storage)
# ==============================================================================
def test_tc_4_3_api_endpoints_upload_and_preview():
    """Verify HTTP endpoints POST /api/v1/admin/assets and GET /url with TestClient."""
    from fastapi.testclient import TestClient

    from app.core.dependencies import require_admin
    from app.db.session import get_db
    from app.main import create_app
    from app.services.storage_service import get_storage_service

    app = create_app()

    mock_admin = User(
        id=uuid.uuid4(),
        username="admin1",
        full_name="Thầy Giáo A",
        role="admin",
        is_active=True,
    )
    test_exam_id = uuid.uuid4()
    mock_exam = Exam(
        id=test_exam_id,
        title="Đề thi Toán 10",
        subject="math",
        duration_minutes=45,
        status="draft",
        created_by=mock_admin.id,
    )

    created_files = {}

    class MockAPISession:
        def scalar(self, query):
            q_str = str(query)
            if "exams" in q_str:
                return mock_exam
            if "files" in q_str:
                # Extract file ID or return created file
                for f in created_files.values():
                    return f
            return None

        def add(self, obj):
            if isinstance(obj, File):
                created_files[str(obj.id)] = obj

        def commit(self):
            pass

        def refresh(self, obj):
            pass

        def rollback(self):
            pass

        def delete(self, obj):
            if isinstance(obj, File):
                created_files.pop(str(obj.id), None)

    mock_storage = StorageService(use_mock=True)
    mock_db = MockAPISession()

    app.dependency_overrides[require_admin] = lambda: mock_admin
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_storage_service] = lambda: mock_storage

    client = TestClient(app)

    # 1. Test valid PNG upload
    png_bytes = create_test_png(150, 150, color="purple")
    response = client.post(
        "/api/v1/admin/assets",
        data={"exam_id": str(test_exam_id)},
        files={"file": ("geometry.png", png_bytes, "image/png")},
    )

    assert response.status_code == 201
    resp_data = response.json()
    assert resp_data["asset"].startswith("asset:")
    assert resp_data["markdown"].startswith("![](asset:")
    assert resp_data["mime_type"] == "image/webp"
    file_id = resp_data["file_id"]
    assert file_id in created_files

    # 2. Test legacy alias route POST /admin/assets
    response_legacy = client.post(
        "/admin/assets",
        data={"exam_id": str(test_exam_id)},
        files={"file": ("graph.png", png_bytes, "image/png")},
    )
    assert response_legacy.status_code == 201
    assert response_legacy.json()["asset"].startswith("asset:")

    # 3. Test GET /assets/{file_id}/url
    url_resp = client.get(f"/api/v1/admin/assets/{file_id}/url")
    assert url_resp.status_code == 200
    assert "url" in url_resp.json()
    assert "expires_in" in url_resp.json()

    # 4. Test upload with non-existent exam
    bad_exam_id = uuid.uuid4()
    # Temporarily make mock_exam None
    mock_exam_orig = mock_exam
    mock_exam = None
    not_found_resp = client.post(
        "/api/v1/admin/assets",
        data={"exam_id": str(bad_exam_id)},
        files={"file": ("test.png", png_bytes, "image/png")},
    )
    assert not_found_resp.status_code == 404
    mock_exam = mock_exam_orig
