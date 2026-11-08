"""Pydantic Schemas for Student Management and Class Enrollment."""

import re
import unicodedata
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

STUDENT_USERNAME_REGEX = re.compile(r"^[a-z0-9._-]{3,32}$")


class ClassSimple(BaseModel):
    """Simple summary of a classroom membership."""

    id: uuid.UUID
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class StudentBase(BaseModel):
    """Base student schema."""

    username: str = Field(..., description="Tên đăng nhập (3-32 ký tự thường, số, dấu chấm/gạch)")
    full_name: str = Field(..., min_length=1, max_length=255, description="Họ và tên học sinh")

    @field_validator("username", mode="before")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if not STUDENT_USERNAME_REGEX.match(normalized):
                raise ValueError(
                    "Tên đăng nhập phải dài 3-32 ký tự và chỉ chứa chữ thường, số, "
                    "dấu chấm, gạch ngang hoặc gạch dưới (không chứa khoảng trắng hay chữ hoa)."
                )
            return normalized
        return value

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        if isinstance(value, str):
            # Unicode NFC normalization for Vietnamese diacritics
            nfc_normalized = unicodedata.normalize("NFC", value)
            cleaned = " ".join(nfc_normalized.strip().split())
            if not cleaned:
                raise ValueError("Họ và tên không được để trống.")
            return cleaned
        return value


class StudentCreate(StudentBase):
    """Schema for creating a new student account."""

    password: str | None = Field(
        default=None,
        min_length=6,
        max_length=128,
        description="Mật khẩu tùy chọn. Nếu để trống, hệ thống sẽ tự sinh ngẫu nhiên an toàn.",
    )
    class_ids: list[uuid.UUID] = Field(
        default_factory=list, description="Danh sách ID các lớp cần ghi danh ngay"
    )


class StudentUpdate(BaseModel):
    """Schema for updating student information."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            nfc_normalized = unicodedata.normalize("NFC", value)
            cleaned = " ".join(nfc_normalized.strip().split())
            if not cleaned:
                raise ValueError("Họ và tên không được để trống.")
            return cleaned
        return value


class ResetPasswordRequest(BaseModel):
    """Schema for resetting a student password."""

    password: str | None = Field(
        default=None,
        min_length=6,
        max_length=128,
        description="Mật khẩu mới. Nếu để trống, hệ thống sẽ tự sinh ngẫu nhiên an toàn.",
    )


class ResetPasswordResponse(BaseModel):
    """One-time password display response."""

    status: str = "ok"
    student_id: uuid.UUID
    generated_password: str | None = Field(
        default=None,
        description="Mật khẩu sinh tự động (chỉ hiển thị duy nhất 1 lần tại phản hồi này).",
    )


class StudentResponse(StudentBase):
    """Public representation of a student (NEVER contains password)."""

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    classes: list[ClassSimple] = Field(default_factory=list, description="Các lớp đang tham gia")

    model_config = ConfigDict(from_attributes=True)


class StudentDetailResponse(StudentResponse):
    """Response returned upon student creation, optionally displaying generated password once."""

    generated_password: str | None = Field(
        default=None,
        description="Mật khẩu khởi tạo (chỉ xuất hiện 1 lần duy nhất trong phản hồi tạo mới).",
    )


class StudentListResponse(BaseModel):
    """Paginated list of students."""

    items: list[StudentResponse]
    total: int
    limit: int
    offset: int


class EnrollmentRequest(BaseModel):
    """Set-based class member enrollment payload."""

    user_ids: list[uuid.UUID] = Field(
        ..., description="Tập hợp ID học sinh cần ghi danh vào lớp học"
    )


class EnrollmentResponse(BaseModel):
    """Result of set-based enrollment operation."""

    class_id: uuid.UUID
    added: int = Field(..., description="Số học sinh mới thêm vào lớp")
    removed: int = Field(..., description="Số học sinh rút khỏi lớp")
    total: int = Field(..., description="Tổng số học sinh hiện có trong lớp")


class CsvRowDetail(BaseModel):
    """Detailed validation status and errors for a specific row in the CSV file."""

    row_number: int = Field(
        ...,
        description="Thứ tự dòng trong tệp tính từ dòng dữ liệu đầu tiên (dòng 2 trong Excel)",
    )
    full_name: str
    username: str
    class_code: str | None = None
    status: str = Field(..., description="Trạng thái dòng: 'valid' hoặc 'error'")
    errors: list[str] = Field(
        default_factory=list, description="Danh sách mã lỗi phát hiện trên dòng"
    )


class StudentImportedItem(BaseModel):
    """Summary of successfully imported student account including plaintext password."""

    id: uuid.UUID
    username: str
    full_name: str
    class_code: str | None = None
    password_plain: str = Field(
        ..., description="Mật khẩu khởi tạo (chỉ trả về 1 lần duy nhất khi tạo)"
    )


class CsvImportResult(BaseModel):
    """Comprehensive response for two-phase CSV import (dry-run and atomic commit)."""

    total_rows: int
    valid_rows: int
    error_rows: int
    estimated_hash_seconds: float
    can_commit: bool
    rows: list[CsvRowDetail] = Field(default_factory=list)
    created_count: int = 0
    students: list[StudentImportedItem] = Field(default_factory=list)
    csv_export_content: str | None = Field(
        default=None,
        description="Chuỗi CSV UTF-8 BOM chứa tài khoản và mật khẩu đã escape an toàn",
    )
