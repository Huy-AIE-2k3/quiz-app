"""Exam Business Logic & Services.

Handles:
- Validation prior to publishing
- State machine lifecycle transitions
- Content lock policy enforcement
- Transactional exam duplication with S3 asset copy & compensation cleanup
"""

import json
import logging
import re
import uuid
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.time import SystemClock
from app.models import Attempt, Class, Exam, ExamClass, Question

logger = logging.getLogger(__name__)

ASSET_REGEX = re.compile(
    r"asset:([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)


def validate_exam_for_publish(exam: Exam, db: Session, now: datetime | None = None) -> list[str]:
    """Validates an exam prior to publishing. Returns a list of error strings."""
    if now is None:
        now = SystemClock().now()

    errors: list[str] = []

    # 1. Check questions count and points
    questions = db.scalars(select(Question).where(Question.exam_id == exam.id)).all()

    if not questions:
        errors.append("Đề thi phải có ít nhất 1 câu hỏi.")
    else:
        total_points = sum((q.points for q in questions), Decimal("0"))
        if total_points <= Decimal("0"):
            errors.append("Tổng điểm của các câu hỏi trong đề thi phải lớn hơn 0.")

        # Question-level integrity checks (TC-4.5-03)
        for q in questions:
            q_type = getattr(q, "question_type", None) or getattr(q, "type", None)
            cfg = q.config or {}
            ans = q.answer_key or {}

            if q_type == "mcq":
                options = cfg.get("options") or []
                if len(options) < 2:
                    errors.append(f"Câu {q.position} (Trắc nghiệm): Phải có ít nhất 2 lựa chọn.")
                correct = ans.get("correct")
                valid_opt_ids = {opt.get("id") for opt in options if isinstance(opt, dict)}
                if not correct or correct not in valid_opt_ids:
                    errors.append(f"Câu {q.position} (Trắc nghiệm): Chưa chọn đáp án đúng.")

            elif q_type == "tf":
                statements = cfg.get("statements") or []
                if len(statements) < 1:
                    errors.append(f"Câu {q.position} (Đúng/Sai): Phải có ít nhất 1 mệnh đề.")
                missing_stmts = [
                    s.get("id")
                    for s in statements
                    if isinstance(s, dict)
                    and (s.get("id") not in ans or ans[s.get("id")] not in (True, False))
                ]
                if missing_stmts:
                    errors.append(
                        f"Câu {q.position} (Đúng/Sai): "
                        "Chưa chọn đáp án Đúng/Sai cho tất cả các mệnh đề."
                    )

            elif q_type == "short_text":
                if cfg.get("grading") == "auto":
                    accepted = ans.get("accepted") or []
                    if not accepted or not any(str(a).strip() for a in accepted):
                        errors.append(
                            f"Câu {q.position} (Trả lời ngắn): "
                            "Chưa nhập đáp án được chấp nhận khi chấm tự động."
                        )

            elif q_type == "short_number":
                values = ans.get("values") or []
                if not values or not any(str(v).strip() for v in values):
                    errors.append(f"Câu {q.position} (Điền số): Chưa nhập giá trị số đúng.")

    # 2. Check assigned classes
    assigned_classes = db.scalars(
        select(Class)
        .join(ExamClass, ExamClass.class_id == Class.id)
        .where(ExamClass.exam_id == exam.id)
    ).all()

    if not assigned_classes:
        errors.append("Đề thi phải được phân công cho ít nhất 1 lớp học.")
    else:
        archived_classes = [c.code for c in assigned_classes if c.is_archived]
        if archived_classes:
            errors.append(
                f"Không thể xuất bản: Các lớp [{', '.join(archived_classes)}] đã bị lưu trữ."
            )

    # 3. Check duration
    if exam.duration_minutes < 1 or exam.duration_minutes > 300:
        errors.append("Thời lượng làm bài phải trong khoảng từ 1 đến 300 phút.")

    # 4. Check time window
    if exam.open_at and exam.close_at and exam.open_at >= exam.close_at:
        errors.append("Thời điểm mở đề (open_at) phải trước thời điểm đóng đề (close_at).")

    if exam.close_at and exam.close_at <= now:
        errors.append("Thời điểm đóng đề (close_at) đã ở trong quá khứ.")

    return errors


def check_exam_latex_warnings(questions: list[Question]) -> list[str]:
    """Detects potential KaTeX syntax issues across all questions and returns warnings."""
    warnings: list[str] = []
    for q in questions:
        content = q.content_md or ""
        unescaped_dollars = len(re.findall(r"(?<!\\)\$", content))
        if unescaped_dollars % 2 != 0:
            warnings.append(
                f"Câu {q.position}: Phát hiện dấu công thức '$' chưa đóng cặp hoàn chỉnh."
            )
        elif r"\frac{" in content and content.count("{") != content.count("}"):
            warnings.append(
                f"Câu {q.position}: "
                "Phát hiện công thức phân số '\\frac' có thể chưa đóng ngoặc nhọn đúng."
            )
    return warnings


def validate_exam_details(
    exam: Exam, db: Session, now: datetime | None = None
) -> tuple[list[str], list[str], dict[str, Any]]:
    """Returns (errors, warnings, summary_dict) for pre-publish inspection."""
    errors = validate_exam_for_publish(exam, db, now=now)
    questions = db.scalars(
        select(Question).where(Question.exam_id == exam.id).order_by(Question.position.asc())
    ).all()
    warnings = check_exam_latex_warnings(questions)

    assigned_classes = db.scalars(
        select(Class)
        .join(ExamClass, ExamClass.class_id == Class.id)
        .where(ExamClass.exam_id == exam.id)
    ).all()

    from app.models.class_model import ClassMember

    student_count = (
        db.scalar(
            select(func.count(func.distinct(ClassMember.student_id)))
            .join(ExamClass, ExamClass.class_id == ClassMember.class_id)
            .where(ExamClass.exam_id == exam.id)
        )
        or 0
    )

    total_points = sum((q.points for q in questions), Decimal("0.00"))

    summary = {
        "question_count": len(questions),
        "total_points": total_points,
        "duration_minutes": exam.duration_minutes,
        "class_count": len(assigned_classes),
        "student_count": student_count,
    }

    return errors, warnings, summary


def transition_exam_status(
    exam: Exam,
    target_status: str,
    db: Session,
    now: datetime | None = None,
) -> None:
    """Executes a validated lifecycle transition according to the exam state machine.

    Valid transitions:
    - draft -> published: Must pass pre-publish validation.
    - published -> draft: Allowed ONLY IF no student has started an attempt.
    - published -> closed: Always allowed.
    - closed -> published: Allowed ONLY IF close_at is None or in the future.
    - closed -> archived: Always allowed.
    All other transitions raise 409 invalid_transition.
    """
    if now is None:
        now = SystemClock().now()

    current_status = exam.status

    if current_status == target_status:
        return  # No-op

    # 1. draft -> published
    if current_status == "draft" and target_status == "published":
        errors = validate_exam_for_publish(exam, db, now=now)
        if errors:
            raise AppError(
                code="exam_validation_failed",
                message=f"Không thể xuất bản đề thi: {'; '.join(errors)}",
                status_code=409,
                details=[{"message": err} for err in errors],
            )
        exam.status = "published"

    # 2. published -> draft
    elif current_status == "published" and target_status == "draft":
        attempt_count = (
            db.scalar(select(func.count(Attempt.id)).where(Attempt.exam_id == exam.id)) or 0
        )
        if attempt_count > 0:
            raise AppError(
                code="exam_locked",
                message=(
                    "Không thể đưa đề thi về bản nháp (draft) vì đã có học sinh bắt đầu làm bài."
                ),
                status_code=409,
            )
        exam.status = "draft"

    # 3. published -> closed
    elif current_status == "published" and target_status == "closed":
        exam.status = "closed"

    # 4. closed -> published
    elif current_status == "closed" and target_status == "published":
        if exam.close_at and exam.close_at <= now:
            raise AppError(
                code="invalid_transition",
                message="Không thể mở lại đề thi đã đóng vì thời hạn đóng đề (close_at) đã qua.",
                status_code=409,
            )
        exam.status = "published"

    # 5. closed -> archived
    elif current_status == "closed" and target_status == "archived":
        exam.status = "archived"

    else:
        raise AppError(
            code="invalid_transition",
            message=(
                f"Không thể chuyển trạng thái đề thi từ '{current_status}' sang '{target_status}'."
            ),
            status_code=409,
        )


def duplicate_exam_with_assets(
    exam: Exam,
    creator_id: uuid.UUID,
    db: Session,
    copy_asset_fn: Callable[[str, str], None] | None = None,
    delete_asset_fn: Callable[[str], None] | None = None,
) -> Exam:
    """Duplicates an exam and all its questions into a new draft exam.

    Also copies all referenced storage assets (copy_asset_fn).
    If an error occurs while copying assets, cleans up any newly created assets
    (compensating transaction) and rolls back the database.
    """
    new_exam = Exam(
        title=f"{exam.title} (bản sao)",
        description_md=exam.description_md,
        subject=exam.subject,
        duration_minutes=exam.duration_minutes,
        status="draft",
        open_at=exam.open_at,
        close_at=exam.close_at,
        locked_at=None,
        shuffle_questions=exam.shuffle_questions,
        shuffle_options=exam.shuffle_options,
        result_visibility=exam.result_visibility,
        version=1,
        created_by=creator_id,
    )
    db.add(new_exam)
    db.flush()

    # Fetch original questions
    old_questions = db.scalars(
        select(Question).where(Question.exam_id == exam.id).order_by(Question.position.asc())
    ).all()

    # Track asset mapping old_uuid -> new_uuid and copied assets for rollback compensation
    asset_id_map: dict[str, str] = {}
    copied_new_assets: list[str] = []

    # Gather all referenced asset UUIDs
    for q in old_questions:
        combined_text = (
            f"{q.content_md} "
            f"{q.explanation_md or ''} "
            f"{json.dumps(q.config)} "
            f"{json.dumps(q.answer_key)}"
        )
        for match in ASSET_REGEX.finditer(combined_text):
            old_asset_uuid = match.group(1)
            if old_asset_uuid not in asset_id_map:
                asset_id_map[old_asset_uuid] = str(uuid.uuid4())

    # Perform storage asset copy if copy function supplied
    if copy_asset_fn and asset_id_map:
        try:
            for old_uuid, new_uuid in asset_id_map.items():
                copy_asset_fn(old_uuid, new_uuid)
                copied_new_assets.append(new_uuid)
        except Exception as e:
            logger.error("Failed to copy storage asset during duplication: %s", e)
            # Compensating rollback: delete all successfully copied new assets
            if delete_asset_fn:
                for new_uuid in copied_new_assets:
                    try:
                        delete_asset_fn(new_uuid)
                    except Exception as clean_err:
                        logger.warning(
                            "Failed to clean up orphan copied asset %s: %s",
                            new_uuid,
                            clean_err,
                        )
            db.rollback()
            raise AppError(
                code="asset_copy_failed",
                message=f"Lỗi khi sao chép tài nguyên hình ảnh bài thi: {e}",
                status_code=500,
            ) from e

    # Create new questions with replaced asset IDs
    for q in old_questions:
        new_content = q.content_md
        new_explanation = q.explanation_md
        new_config_str = json.dumps(q.config)
        new_answer_key_str = json.dumps(q.answer_key)

        for old_uuid, new_uuid in asset_id_map.items():
            new_content = new_content.replace(f"asset:{old_uuid}", f"asset:{new_uuid}")
            if new_explanation:
                new_explanation = new_explanation.replace(f"asset:{old_uuid}", f"asset:{new_uuid}")
            new_config_str = new_config_str.replace(f"asset:{old_uuid}", f"asset:{new_uuid}")
            new_answer_key_str = new_answer_key_str.replace(
                f"asset:{old_uuid}", f"asset:{new_uuid}"
            )

        new_q = Question(
            exam_id=new_exam.id,
            position=q.position,
            question_type=q.question_type,
            content_md=new_content,
            config=json.loads(new_config_str),
            answer_key=json.loads(new_answer_key_str),
            explanation_md=new_explanation,
            points=q.points,
            version=1,
        )
        db.add(new_q)

    db.commit()
    db.refresh(new_exam)
    return new_exam
