"""Asset Rendering & Ownership Verification Service.

Implements Step 4.3 requirements:
- Finds all 'asset:<uuid>' tokens in Markdown text
- Verifies that referenced files strictly belong to the specified exam_id
- Replaces valid references with temporary signed URLs (default TTL: 6 hours)
- Replaces invalid or cross-exam references with 'about:blank' (TC-4.3-08)
"""

import logging
import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file import File
from app.services.storage_service import StorageService, get_storage_service

logger = logging.getLogger(__name__)

ASSET_REGEX = re.compile(
    r"asset:([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE,
)


def render_assets(
    md: str | None,
    exam_id: uuid.UUID,
    db: Session,
    storage: StorageService | None = None,
    ttl: int = 6 * 3600,
) -> str:
    """Replaces asset:<uuid> references in markdown with presigned URLs.

    If an asset does not exist or belongs to another exam, it is replaced with 'about:blank'.
    """
    if not md:
        return md or ""

    found_ids = set(ASSET_REGEX.findall(md))
    if not found_ids:
        return md

    # Parse string UUIDs safely
    valid_uuids: list[uuid.UUID] = []
    for raw_id in found_ids:
        try:
            valid_uuids.append(uuid.UUID(raw_id))
        except ValueError:
            pass

    if not valid_uuids:
        return md

    # Query files strictly owned by this exam
    files = db.scalars(
        select(File).where(
            File.id.in_(valid_uuids),
            File.exam_id == exam_id,
        )
    ).all()
    owned_map: dict[str, File] = {str(f.id): f for f in files}

    storage_client = storage or get_storage_service()

    def replace_match(match: re.Match) -> str:
        asset_id_str = match.group(1).lower()
        file_obj = owned_map.get(asset_id_str)
        if file_obj:
            try:
                return storage_client.generate_presigned_url(file_obj.s3_key, expires_in=ttl)
            except Exception as e:
                logger.error("Failed to generate presigned URL for asset %s: %s", asset_id_str, e)
                return "about:blank"
        # Disallowed cross-exam or non-existent asset
        return "about:blank"

    return ASSET_REGEX.sub(replace_match, md)


def render_question_assets(
    question_data: dict[str, Any],
    exam_id: uuid.UUID,
    db: Session,
    storage: StorageService | None = None,
    ttl: int = 6 * 3600,
) -> dict[str, Any]:
    """Applies asset rendering to question fields (content_md, explanation_md, config options)."""
    result = dict(question_data)

    if "content_md" in result and isinstance(result["content_md"], str):
        result["content_md"] = render_assets(
            result["content_md"], exam_id, db, storage=storage, ttl=ttl
        )

    if "explanation_md" in result and isinstance(result["explanation_md"], str):
        result["explanation_md"] = render_assets(
            result["explanation_md"], exam_id, db, storage=storage, ttl=ttl
        )

    # If config contains options with Markdown text, process them as well
    if "config" in result and isinstance(result["config"], dict):
        cfg = dict(result["config"])
        if "options" in cfg and isinstance(cfg["options"], list):
            new_options = []
            for opt in cfg["options"]:
                if isinstance(opt, dict) and "content" in opt and isinstance(opt["content"], str):
                    new_opt = dict(opt)
                    new_opt["content"] = render_assets(
                        opt["content"], exam_id, db, storage=storage, ttl=ttl
                    )
                    new_options.append(new_opt)
                else:
                    new_options.append(opt)
            cfg["options"] = new_options

        if "statements" in cfg and isinstance(cfg["statements"], list):
            new_stmts = []
            for stmt in cfg["statements"]:
                if isinstance(stmt, dict) and "statement" in stmt:
                    new_stmt = dict(stmt)
                    new_stmt["statement"] = render_assets(
                        stmt["statement"], exam_id, db, storage=storage, ttl=ttl
                    )
                    new_stmts.append(new_stmt)
                else:
                    new_stmts.append(stmt)
            cfg["statements"] = new_stmts

        result["config"] = cfg

    return result

