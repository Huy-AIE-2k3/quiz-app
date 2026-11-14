"""Admin Assets Router for Exam Image Upload & Asset Management.

Implements Step 4.3:
- POST /admin/assets (and /api/v1/admin/assets): Upload exam image
- 5 MB streaming check (HTTP 413)
- Magic bytes verification, SVG rejection, decompression bomb guard (HTTP 415/400)
- WEBP re-encoding & EXIF removal
- S3 upload + DB insert with compensation rollback on DB error (HTTP 500)
- Presigned URL preview & secure deletion
"""

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.core.errors import AppError
from app.db.session import get_db
from app.models.exam import Exam
from app.models.file import File as FileModel
from app.models.user import User
from app.services.image_service import (
    read_and_validate_upload_stream,
    sanitize_and_convert_to_webp,
)
from app.services.storage_service import StorageService, get_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin Assets"])


@router.post(
    "/assets",
    status_code=status.HTTP_201_CREATED,
    summary="Upload exam image asset",
)
async def upload_exam_asset(
    exam_id: Annotated[uuid.UUID, Form(description="ID của đề thi sở hữu ảnh")],
    file: Annotated[UploadFile, File(description="Tệp hình ảnh JPEG, PNG, WEBP <= 5 MB")],
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    storage: StorageService = Depends(get_storage_service),
) -> dict:
    """Uploads, validates, sanitizes, and stores exam image asset in S3/R2."""
    # 1. Verify exam exists
    exam = db.scalar(select(Exam).where(Exam.id == exam_id))
    if not exam:
        raise AppError(
            code="exam_not_found",
            message="Đề thi không tồn tại.",
            status_code=404,
            details={"exam_id": str(exam_id)},
        )

    # 2. Read stream with 5 MB chunk limit (raises 413 on overflow)
    file_bytes = await read_and_validate_upload_stream(file)

    # 3. Sanitize, verify magic bytes, strip EXIF, convert to WEBP
    original_name = file.filename or "uploaded_image"
    webp_bytes, width, height = sanitize_and_convert_to_webp(file_bytes, original_name)

    # 4. Generate asset UUID and storage key
    asset_id = uuid.uuid4()
    s3_key = f"exams/{exam_id}/img/{asset_id}.webp"

    # 5. Upload to S3/R2
    try:
        storage.put_object(
            key=s3_key,
            body=webp_bytes,
            content_type="image/webp",
        )
    except Exception as e:
        logger.error("Failed to upload image to storage: %s", e)
        raise AppError(
            code="storage_upload_failed",
            message="Lỗi lưu trữ tệp tin lên hệ thống lưu trữ đám mây.",
            status_code=500,
            details=str(e),
        ) from e

    # 6. Insert file record into DB with compensation rollback on error (TC-4.3-09)
    file_record = FileModel(
        id=asset_id,
        user_id=admin.id,
        exam_id=exam_id,
        kind="question_image",
        original_name=original_name,
        s3_key=s3_key,
        mime_type="image/webp",
        size_bytes=len(webp_bytes),
    )
    db.add(file_record)

    try:
        db.commit()
        db.refresh(file_record)
    except Exception as db_exc:
        db.rollback()
        logger.error(
            "Database insert failed for file %s, compensating by deleting S3 object",
            s3_key,
        )
        try:
            storage.delete_object(s3_key)
        except Exception as clean_err:
            logger.warning("Compensation deletion failed for %s: %s", s3_key, clean_err)

        raise AppError(
            code="upload_failed",
            message="Lỗi ghi nhận thông tin tệp vào cơ sở dữ liệu.",
            status_code=500,
            details=str(db_exc),
        ) from db_exc

    return {
        "asset": f"asset:{asset_id}",
        "markdown": f"![](asset:{asset_id})",
        "file_id": str(asset_id),
        "size_bytes": len(webp_bytes),
        "mime_type": "image/webp",
        "width": width,
        "height": height,
    }


@router.get(
    "/assets/{file_id}/url",
    status_code=status.HTTP_200_OK,
    summary="Get temporary signed URL for asset preview",
)
def get_asset_url(
    file_id: uuid.UUID,
    ttl: int = 21600,  # 6 hours
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    storage: StorageService = Depends(get_storage_service),
) -> dict:
    """Generates temporary presigned GET URL for an asset."""
    file_record = db.scalar(select(FileModel).where(FileModel.id == file_id))
    if not file_record:
        raise AppError(
            code="file_not_found",
            message="Tài nguyên hình ảnh không tồn tại.",
            status_code=404,
        )

    url = storage.generate_presigned_url(file_record.s3_key, expires_in=ttl)
    return {
        "file_id": str(file_id),
        "url": url,
        "expires_in": ttl,
    }


@router.delete(
    "/assets/{file_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an asset from storage and DB",
)
def delete_asset(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    storage: StorageService = Depends(get_storage_service),
) -> dict:
    """Deletes an asset from storage and database."""
    file_record = db.scalar(select(FileModel).where(FileModel.id == file_id))
    if not file_record:
        raise AppError(
            code="file_not_found",
            message="Tài nguyên hình ảnh không tồn tại.",
            status_code=404,
        )

    s3_key = file_record.s3_key
    db.delete(file_record)
    db.commit()

    try:
        storage.delete_object(s3_key)
    except Exception as e:
        logger.warning("Failed to delete S3 object %s: %s", s3_key, e)

    return {
        "status": "deleted",
        "file_id": str(file_id),
    }


# Legacy /admin prefix router alias (for spec compatibility with POST /admin/assets)
legacy_router = APIRouter(
    prefix="/admin",
    tags=["Admin Assets"],
    dependencies=[Depends(require_admin)],
)
legacy_router.add_api_route(
    "/assets",
    upload_exam_asset,
    methods=["POST"],
    status_code=status.HTTP_201_CREATED,
)
legacy_router.add_api_route(
    "/assets/{file_id}/url",
    get_asset_url,
    methods=["GET"],
    status_code=status.HTTP_200_OK,
)
legacy_router.add_api_route(
    "/assets/{file_id}",
    delete_asset,
    methods=["DELETE"],
    status_code=status.HTTP_200_OK,
)
