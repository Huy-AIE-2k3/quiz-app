"""Image validation, sanitization, and WEBP re-encoding service.

Implements Step 4.3 security requirements:
- Streaming size validation (<= 5 MB) reading 64 KB chunks, aborting immediately on overflow
- Magic bytes verification using Pillow (only JPEG, PNG, WEBP allowed)
- Strict rejection of SVG files (containing XML / script vectors)
- Decompression bomb protection (MAX_IMAGE_PIXELS = 40_000_000)
- Stripping EXIF/GPS metadata completely by re-encoding to WEBP (quality=85, max <= 2000px)
"""

import io
import logging
from typing import BinaryIO

from fastapi import UploadFile
from PIL import Image

from app.core.errors import AppError

logger = logging.getLogger(__name__)

# Security & size limits
MAX_ASSET_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
CHUNK_SIZE = 64 * 1024  # 64 KB
MAX_IMAGE_DIMENSION = 2000  # Max dimension 2000px
WEBP_QUALITY = 85
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

# Protect against decompression bomb attacks (40 million pixels)
Image.MAX_IMAGE_PIXELS = 40_000_000


async def read_and_validate_upload_stream(
    upload_file: UploadFile,
    max_bytes: int = MAX_ASSET_SIZE_BYTES,
    chunk_size: int = CHUNK_SIZE,
) -> bytes:
    """Reads UploadFile stream in 64 KB chunks, aborting immediately if exceeding max_bytes.

    Raises:
        AppError(code="file_too_large", status_code=413) if size > max_bytes.
    """
    buffer = io.BytesIO()
    total_bytes = 0

    while True:
        chunk = await upload_file.read(chunk_size)
        if not chunk:
            break

        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            # Drain and close upload file stream immediately
            await upload_file.close()
            max_mb = max_bytes // (1024 * 1024)
            raise AppError(
                code="file_too_large",
                message=f"Kích thước tệp vượt quá giới hạn cho phép ({max_mb} MB).",
                status_code=413,
                details={"max_bytes": max_bytes, "received_bytes": total_bytes},
            )
        buffer.write(chunk)

    return buffer.getvalue()


def read_sync_stream_with_limit(
    stream: BinaryIO,
    max_bytes: int = MAX_ASSET_SIZE_BYTES,
    chunk_size: int = CHUNK_SIZE,
) -> bytes:
    """Synchronous version of chunked reading with hard limit enforcement."""
    buffer = io.BytesIO()
    total_bytes = 0

    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break

        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            max_mb = max_bytes // (1024 * 1024)
            raise AppError(
                code="file_too_large",
                message=f"Kích thước tệp vượt quá giới hạn cho phép ({max_mb} MB).",
                status_code=413,
                details={"max_bytes": max_bytes, "received_bytes": total_bytes},
            )
        buffer.write(chunk)

    return buffer.getvalue()


def sanitize_and_convert_to_webp(
    file_bytes: bytes,
    original_filename: str = "",
) -> tuple[bytes, int, int]:
    """Validates image magic bytes, strips metadata, and re-encodes to clean WEBP.

    Returns:
        tuple of (webp_bytes, width, height)

    Raises:
        AppError(code="invalid_image", status_code=415) if format is unsupported or invalid.
        AppError(code="decompression_bomb", status_code=400) if image pixels exceed 40 million.
    """
    if not file_bytes:
        raise AppError(
            code="invalid_image",
            message="Dữ liệu tệp hình ảnh trống.",
            status_code=400,
        )

    # 1. Reject SVG explicitly (checks filename and text/xml content)
    fn_lower = original_filename.lower()
    if fn_lower.endswith(".svg") or fn_lower.endswith(".svgz"):
        raise AppError(
            code="invalid_image",
            message="Định dạng tệp không được hỗ trợ (không chấp nhận file SVG).",
            status_code=415,
        )

    sample = file_bytes[:1024].lower()
    if b"<svg" in sample or b"<?xml" in sample or b"<script" in file_bytes.lower():
        raise AppError(
            code="invalid_image",
            message="Định dạng tệp không được hỗ trợ (phát hiện nội dung SVG hoặc script).",
            status_code=415,
        )

    # 2. Open with Pillow and guard against decompression bomb
    try:
        raw_stream = io.BytesIO(file_bytes)
        img = Image.open(raw_stream)

        # Check total pixel count against decompression bomb limit
        pixel_count = img.width * img.height
        if pixel_count > Image.MAX_IMAGE_PIXELS:
            raise AppError(
                code="decompression_bomb",
                message="Ảnh có kích thước giải nén quá lớn (vượt ngưỡng 40 triệu điểm ảnh).",
                status_code=400,
                details={"pixels": pixel_count, "max_pixels": Image.MAX_IMAGE_PIXELS},
            )

        # Verify integrity of headers
        img.verify()
    except Image.DecompressionBombError as e:
        raise AppError(
            code="decompression_bomb",
            message="Ảnh có kích thước giải nén quá lớn (nguy cơ bom giải nén).",
            status_code=400,
            details=str(e),
        ) from e
    except AppError:
        raise
    except Exception as e:
        logger.warning("Image verification failed: %s", e)
        raise AppError(
            code="invalid_image",
            message="Tệp tải lên không phải là hình ảnh hợp lệ hoặc dữ liệu bị hỏng.",
            status_code=415,
            details=str(e),
        ) from e

    # 3. Re-open after verify() (verify alters internal image stream state)
    try:
        img = Image.open(io.BytesIO(file_bytes))
        image_format = img.format

        if image_format not in ALLOWED_FORMATS:
            msg = f"Định dạng {image_format} không được hỗ trợ. Chỉ chấp nhận JPEG, PNG, WEBP."
            raise AppError(
                code="invalid_image",
                message=msg,
                status_code=415,
                details={"detected_format": image_format},
            )

        # 4. Color mode conversion & transparency handling
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        # 5. Resize if dimension exceeds MAX_IMAGE_DIMENSION (2000px)
        if max(img.width, img.height) > MAX_IMAGE_DIMENSION:
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

        # 6. Re-encode to clean WEBP without EXIF
        output_buffer = io.BytesIO()
        img.save(
            output_buffer,
            format="WEBP",
            quality=WEBP_QUALITY,
            method=6,  # Best compression speed/size tradeoff
        )
        webp_bytes = output_buffer.getvalue()

        return webp_bytes, img.width, img.height
    except AppError:
        raise
    except Exception as e:
        logger.error("Failed to re-encode image to WEBP: %s", e)
        raise AppError(
            code="image_processing_failed",
            message="Không thể xử lý và chuẩn hóa hình ảnh.",
            status_code=500,
            details=str(e),
        ) from e
