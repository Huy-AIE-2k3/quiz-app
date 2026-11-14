"""Student Question View & Allow-list Serialization.

STRICT ALLOW-LIST ENFORCEMENT:
Guarantees 0% leakage of sensitive examination data:
- answer_key
- explanation_md
- accepted strings
- correct option IDs
- numerical target values
- tolerance metadata
- secret or unapproved configuration parameters
"""

import copy
import logging
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.question_utils import stable_key

logger = logging.getLogger(__name__)

# Strict allow-list of config keys allowed in student-facing payloads
STUDENT_CONFIG_KEYS: dict[str, set[str]] = {
    "mcq": {"options"},
    "tf": {"statements"},
    "short_text": set(),
    "short_number": set(),
    "file_upload": {"max_files", "max_mb", "allowed_ext"},
}

# Forbidden keys that must NEVER appear at any depth in student view
FORBIDDEN_STUDENT_KEYS = {
    "answer_key",
    "explanation_md",
    "correct",
    "accepted",
    "values",
    "tolerance",
    "tolerance_type",
    "rubric_md",
    "secret",
}


class StudentOption(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    content_md: str


class StudentStatement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    content_md: str


class StudentQuestionView(BaseModel):
    """Schema representing the student-facing question representation."""

    model_config = ConfigDict(extra="forbid")

    id: str
    type: str
    content_md: str = ""
    points: str = "1.00"
    config: dict[str, Any] = Field(default_factory=dict)
    unavailable: bool = False


def student_view(
    q: Any,
    seed: int | None = None,
    shuffle_options: bool = False,
    exam_id: uuid.UUID | None = None,
    db: Any | None = None,
    storage: Any | None = None,
    ttl: int = 6 * 3600,
) -> dict[str, Any]:
    """Serializes a question object, schema, or dict into a student-facing representation.

    Strictly applies an allow-list:
    1. Extracts id, type, content_md, points.
    2. Filters config to only include allowed keys for that question type.
    3. If question is MCQ and shuffle_options is True, stably shuffles options using seed.
    4. Omits answer_key, explanation_md, and all unapproved fields.
    5. Resolves asset:<uuid> to signed presigned URLs if db and exam_id are provided (Step 4.3).
    6. If data is corrupted/invalid in DB, marks question with 'unavailable': True without crashing.
    """
    # Extract identifiers and raw attributes
    if isinstance(q, dict):
        q_id = str(q.get("id", ""))
        q_type = str(q.get("question_type") or q.get("type") or "")
        content_md = str(q.get("content_md", ""))
        points = str(q.get("points", "1.00"))
        raw_config = q.get("config") or {}
    else:
        q_id = str(getattr(q, "id", ""))
        q_type = str(getattr(q, "question_type", None) or getattr(q, "type", ""))
        content_md = str(getattr(q, "content_md", ""))
        raw_points = getattr(q, "points", "1.00")
        points = str(raw_points)
        raw_config = getattr(q, "config", {}) or {}

    # Map legacy question_type names if encountered
    if q_type == "true_false":
        q_type = "tf"
    elif q_type == "short_answer":
        q_type = "short_text"

    # Corruption detection: verify basic structural integrity
    if not isinstance(raw_config, dict):
        logger.warning(
            "Corrupt question detected (config is not dict): id=%s type=%s",
            q_id,
            q_type,
        )
        return {
            "id": q_id,
            "type": q_type,
            "content_md": content_md,
            "points": points,
            "config": {},
            "unavailable": True,
        }

    # Verify type-specific required fields
    if q_type == "mcq":
        options = raw_config.get("options")
        if not isinstance(options, list) or len(options) < 2:
            logger.warning(
                "Corrupt MCQ question detected (invalid or missing options): id=%s",
                q_id,
            )
            return {
                "id": q_id,
                "type": q_type,
                "content_md": content_md,
                "points": points,
                "config": {},
                "unavailable": True,
            }

    elif q_type == "tf":
        statements = raw_config.get("statements")
        if not isinstance(statements, list) or len(statements) < 1:
            logger.warning(
                "Corrupt TF question detected (invalid or missing statements): id=%s",
                q_id,
            )
            return {
                "id": q_id,
                "type": q_type,
                "content_md": content_md,
                "points": points,
                "config": {},
                "unavailable": True,
            }

    # Allow-list filtering of config dictionary
    allowed_keys = STUDENT_CONFIG_KEYS.get(q_type, set())
    filtered_config: dict[str, Any] = {}

    for k in allowed_keys:
        if k in raw_config:
            val = raw_config[k]
            # Deep sanitization for sub-objects like options and statements
            if k == "options" and isinstance(val, list):
                sanitized_options = []
                for item in val:
                    if isinstance(item, dict):
                        # Only expose id and content_md for each option
                        sanitized_options.append(
                            {
                                "id": str(item.get("id", "")),
                                "content_md": str(item.get("content_md", "")),
                            }
                        )
                # Stably shuffle options if requested
                if shuffle_options and seed is not None:
                    sanitized_options = sorted(
                        sanitized_options,
                        key=lambda o: stable_key(seed, q_id, o["id"]),
                    )
                filtered_config["options"] = sanitized_options

            elif k == "statements" and isinstance(val, list):
                sanitized_statements = []
                for item in val:
                    if isinstance(item, dict):
                        sanitized_statements.append(
                            {
                                "id": str(item.get("id", "")),
                                "content_md": str(item.get("content_md", "")),
                            }
                        )
                filtered_config["statements"] = sanitized_statements

            else:
                filtered_config[k] = copy.deepcopy(val)

    # Step 4.3: Resolve asset:<uuid> to signed presigned URLs if db and exam_id are provided
    if exam_id is not None and db is not None:
        from app.services.asset_service import render_assets

        content_md = render_assets(content_md, exam_id, db, storage=storage, ttl=ttl)

        if "options" in filtered_config and isinstance(filtered_config["options"], list):
            for opt in filtered_config["options"]:
                if isinstance(opt, dict) and "content_md" in opt:
                    opt["content_md"] = render_assets(
                        opt["content_md"], exam_id, db, storage=storage, ttl=ttl
                    )

        if "statements" in filtered_config and isinstance(filtered_config["statements"], list):
            for stmt in filtered_config["statements"]:
                if isinstance(stmt, dict) and "content_md" in stmt:
                    stmt["content_md"] = render_assets(
                        stmt["content_md"], exam_id, db, storage=storage, ttl=ttl
                    )

    # Return STRICT allow-listed dictionary
    return {
        "id": q_id,
        "type": q_type,
        "content_md": content_md,
        "points": points,
        "config": filtered_config,
    }


def student_view_list(
    questions: list[Any],
    seed: int | None = None,
    shuffle_options: bool = False,
    exam_id: uuid.UUID | None = None,
    db: Any | None = None,
    storage: Any | None = None,
    ttl: int = 6 * 3600,
) -> list[dict[str, Any]]:
    """Transforms a collection of questions into safe student-facing representations.

    Guarantees that a single corrupt question marks itself as 'unavailable'
    without failing the entire examination.
    """
    res: list[dict[str, Any]] = []
    for q in questions:
        try:
            view = student_view(
                q,
                seed=seed,
                shuffle_options=shuffle_options,
                exam_id=exam_id,
                db=db,
                storage=storage,
                ttl=ttl,
            )
            res.append(view)
        except Exception as e:
            logger.exception(
                "Unexpected error transforming question %s: %s", getattr(q, "id", None), e
            )
            raw_id = getattr(q, "id", None) or (q.get("id") if isinstance(q, dict) else None)
            q_id = str(raw_id or uuid.uuid4())
            q_type = str(getattr(q, "type", "unknown"))
            res.append(
                {
                    "id": q_id,
                    "type": q_type,
                    "content_md": "",
                    "points": "0.00",
                    "config": {},
                    "unavailable": True,
                }
            )
    return res
