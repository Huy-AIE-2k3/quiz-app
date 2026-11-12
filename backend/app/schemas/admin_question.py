"""Admin Question Schemas & Validation.

Supports 5 question types:
- mcq: Multiple Choice (2-8 options, IDs 'o1'..'o8', single correct answer)
- tf: True / False statements (1-8 statements, IDs 's1'..'s8', thpt/proportional scoring)
- short_text: Short text answers (1-20 accepted strings NFC normalized, auto/manual grading)
- short_number: Numerical answers (1-10 parseable values, abs/rel tolerance >= 0)
- file_upload: Submission attachment (1-5 files, <= 50MB, allowed safe extensions)
"""

import uuid
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.question_utils import normalize_nfc, parse_number

QuestionType = Literal["mcq", "tf", "short_text", "short_number", "file_upload"]
TfScoring = Literal["thpt", "proportional", "all_or_nothing"]
ToleranceType = Literal["abs", "rel"]
GradingMode = Literal["auto", "manual"]

ALLOWED_FILE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "pdf",
    "zip",
    "py",
    "cpp",
    "c",
    "pas",
    "txt",
    "docx",
}


# ==============================================================================
# 1. Sub-models for MCQ
# ==============================================================================
class MCQOption(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., pattern=r"^o[1-8]$")
    content_md: str = Field(..., min_length=1, max_length=10000)

    @field_validator("content_md")
    @classmethod
    def validate_content(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Nội dung lựa chọn không được để trống.")
        return normalize_nfc(s)


class MCQConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    options: list[MCQOption] = Field(..., min_length=2, max_length=8)

    @field_validator("options")
    @classmethod
    def validate_unique_option_ids(cls, v: list[MCQOption]) -> list[MCQOption]:
        ids = [opt.id for opt in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Các mã lựa chọn (id) phải là duy nhất.")
        return v


class MCQAnswerKey(BaseModel):
    model_config = ConfigDict(extra="forbid")
    correct: str = Field(..., pattern=r"^o[1-8]$")


# ==============================================================================
# 2. Sub-models for TF (True/False)
# ==============================================================================
class TFStatement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., pattern=r"^s[1-8]$")
    content_md: str = Field(..., min_length=1, max_length=10000)

    @field_validator("content_md")
    @classmethod
    def validate_content(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Nội dung mệnh đề không được để trống.")
        return normalize_nfc(s)


class TFConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statements: list[TFStatement] = Field(..., min_length=1, max_length=8)
    scoring: TfScoring = "thpt"

    @field_validator("statements")
    @classmethod
    def validate_unique_statement_ids(cls, v: list[TFStatement]) -> list[TFStatement]:
        ids = [s.id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Các mã mệnh đề (id) phải là duy nhất.")
        return v


class TFAnswerKey(BaseModel):
    model_config = ConfigDict(extra="allow")  # keys are s1, s2...


# ==============================================================================
# 3. Sub-models for Short Text
# ==============================================================================
class ShortTextConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grading: GradingMode = "auto"
    review_wrong: bool = False


class ShortTextAnswerKey(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accepted: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("accepted")
    @classmethod
    def validate_accepted(cls, v: list[str]) -> list[str]:
        cleaned = []
        for s in v:
            c = normalize_nfc(str(s).strip())
            if c:
                cleaned.append(c)
        return cleaned


# ==============================================================================
# 4. Sub-models for Short Number
# ==============================================================================
class ShortNumberConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tolerance: Decimal = Field(default=Decimal("0"), ge=0)
    tolerance_type: ToleranceType = "abs"


class ShortNumberAnswerKey(BaseModel):
    model_config = ConfigDict(extra="forbid")
    values: list[str] = Field(..., min_length=1, max_length=10)

    @field_validator("values")
    @classmethod
    def validate_values(cls, v: list[str]) -> list[str]:
        cleaned = []
        for raw in v:
            s = str(raw).strip()
            try:
                parse_number(s)
            except ValueError as e:
                raise ValueError(f"Giá trị số không hợp lệ trong answer_key: '{s}' ({e})") from e
            cleaned.append(s)
        return cleaned


# ==============================================================================
# 5. Sub-models for File Upload
# ==============================================================================
class FileUploadConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_files: int = Field(default=1, ge=1, le=5)
    max_mb: int = Field(default=10, ge=1, le=50)
    allowed_ext: list[str] = Field(
        default_factory=lambda: ["jpg", "jpeg", "png", "pdf"],
        min_length=1,
    )

    @field_validator("allowed_ext")
    @classmethod
    def validate_extensions(cls, v: list[str]) -> list[str]:
        cleaned = []
        for ext in v:
            clean_ext = ext.strip().lstrip(".").lower()
            if clean_ext not in ALLOWED_FILE_EXTENSIONS:
                raise ValueError(
                    f"Đuôi tệp '.{clean_ext}' không được cho phép. "
                    f"Chỉ chấp nhận: {', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}"
                )
            cleaned.append(clean_ext)
        return list(dict.fromkeys(cleaned))  # Deduplicate while preserving order


class FileUploadAnswerKey(BaseModel):
    model_config = ConfigDict(extra="allow")
    rubric_md: str | None = None


# ==============================================================================
# Unified Question Create & Update Request Models
# ==============================================================================
class QuestionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: QuestionType
    content_md: str = Field(..., min_length=1, max_length=20000)
    points: Decimal = Field(default=Decimal("1.00"))
    config: dict[str, Any] = Field(default_factory=dict)
    answer_key: dict[str, Any] = Field(default_factory=dict)
    explanation_md: str | None = Field(default=None, max_length=20000)
    position: int | None = Field(default=None, ge=1)

    @field_validator("content_md")
    @classmethod
    def validate_content_md(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Nội dung câu hỏi không được để trống.")
        return normalize_nfc(s)

    @field_validator("explanation_md")
    @classmethod
    def validate_explanation_md(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return normalize_nfc(v)

    @field_validator("points")
    @classmethod
    def validate_points(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("Điểm số phải lớn hơn 0.")
        if v > Decimal("100"):
            raise ValueError("Điểm số không được vượt quá 100 điểm.")
        # Check scale <= 2 (at most 2 decimal places)
        exponent = v.as_tuple().exponent
        if isinstance(exponent, int) and exponent < -2:
            raise ValueError("Điểm số chỉ được phép tối đa 2 chữ số thập phân (ví dụ: 0.25, 1.50).")
        return v

    @model_validator(mode="after")
    def validate_config_and_answer_key(self) -> "QuestionCreate":
        q_type = self.type
        cfg = self.config or {}
        ans = self.answer_key or {}

        if q_type == "mcq":
            mcq_cfg = MCQConfig(**cfg)
            mcq_ans = MCQAnswerKey(**ans)
            valid_ids = {opt.id for opt in mcq_cfg.options}
            if mcq_ans.correct not in valid_ids:
                raise ValueError(
                    f"Đáp án đúng '{mcq_ans.correct}' không nằm trong danh sách "
                    f"lựa chọn {valid_ids}."
                )
            self.config = mcq_cfg.model_dump()
            self.answer_key = mcq_ans.model_dump()

        elif q_type == "tf":
            tf_cfg = TFConfig(**cfg)
            # TC-4.1-08: If scoring == "thpt" and statements != 4, auto convert to proportional
            if tf_cfg.scoring == "thpt" and len(tf_cfg.statements) != 4:
                tf_cfg.scoring = "proportional"

            valid_ids = {s.id for s in tf_cfg.statements}
            if not isinstance(ans, dict):
                raise ValueError(
                    "answer_key cho câu hỏi Đúng/Sai phải là từ điển "
                    "ánh xạ mã mệnh đề sang boolean."
                )

            # Validate all statement IDs are present and values are booleans
            ans_keys = set(ans.keys())
            if ans_keys != valid_ids:
                missing = valid_ids - ans_keys
                extra = ans_keys - valid_ids
                err_parts = []
                if missing:
                    err_parts.append(f"thiếu mệnh đề: {missing}")
                if extra:
                    err_parts.append(f"thừa mệnh đề: {extra}")
                raise ValueError(
                    f"Đáp án câu Đúng/Sai không khớp danh sách mệnh đề: {', '.join(err_parts)}."
                )

            for sid, val in ans.items():
                if not isinstance(val, bool):
                    raise ValueError(
                        f"Giá trị đáp án cho mệnh đề '{sid}' phải là kiểu boolean (True/False)."
                    )

            self.config = tf_cfg.model_dump()
            self.answer_key = ans

        elif q_type == "short_text":
            st_cfg = ShortTextConfig(**cfg)
            st_ans = ShortTextAnswerKey(**ans)
            if st_cfg.grading == "auto" and not st_ans.accepted:
                raise ValueError(
                    "Câu trả lời ngắn ở chế độ chấm tự động (auto) "
                    "phải có ít nhất 1 đáp án chấp nhận."
                )
            self.config = st_cfg.model_dump()
            self.answer_key = st_ans.model_dump()

        elif q_type == "short_number":
            sn_cfg = ShortNumberConfig(**cfg)
            sn_ans = ShortNumberAnswerKey(**ans)
            # Serialization of Decimal in config
            self.config = {
                "tolerance": float(sn_cfg.tolerance),
                "tolerance_type": sn_cfg.tolerance_type,
            }
            self.answer_key = sn_ans.model_dump()

        elif q_type == "file_upload":
            fu_cfg = FileUploadConfig(**cfg)
            fu_ans = FileUploadAnswerKey(**ans)
            self.config = fu_cfg.model_dump()
            self.answer_key = fu_ans.model_dump()

        return self


class QuestionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content_md: str | None = Field(default=None, min_length=1, max_length=20000)
    points: Decimal | None = None
    config: dict[str, Any] | None = None
    answer_key: dict[str, Any] | None = None
    explanation_md: str | None = None
    position: int | None = Field(default=None, ge=1)
    version: int = Field(..., description="Optimistic locking version")


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    exam_id: uuid.UUID
    position: int
    type: str = Field(..., serialization_alias="type")
    content_md: str
    points: Decimal
    config: dict[str, Any]
    answer_key: dict[str, Any]
    explanation_md: str | None = None
    version: int
    warning: str | None = None
