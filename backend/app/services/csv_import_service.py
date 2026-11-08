"""CSV Import Service for Batch Student Onboarding.

Implements Step 3.3 specification:
- Encoding resilience: Auto-detects UTF-8 with BOM (utf-8-sig), UTF-8, and Windows-1258.
- Delimiter sniffing: Auto-detects delimiter (comma, semicolon, tab) or defaults to comma.
- Limits enforcement: <= 1 MB file size (413), <= 500 rows (422), non-empty, valid headers.
- Two-phase execution:
    - dry_run=True: Complete syntax, file duplicate, DB duplicate & class check. Zero DB writes.
    - dry_run=False: Atomic commit. If any row is invalid, rolls back 100% (0 students created).
- Password management:
    - Supports user-provided passwords or teacher-initiated auto-generation (safe 8-char).
    - Sequential Argon2id hashing bounded by concurrency semaphore.
- CSV Injection protection & Export:
    - Prepends single quote (') to cells starting with formula triggers (=, +, -, @, \\t, \\r).
    - Exports UTF-8 with BOM for native Vietnamese rendering in Microsoft Excel.
"""

import csv
import io
import re
import unicodedata
import uuid
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import generate_random_password, hash_password
from app.models import Class, ClassMember, User
from app.schemas.student_schema import (
    STUDENT_USERNAME_REGEX,
    CsvImportResult,
    CsvRowDetail,
    StudentImportedItem,
)

MAX_CSV_BYTES = 1 * 1024 * 1024  # 1 MB
MAX_CSV_ROWS = 500

FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r")


def decode_csv(raw: bytes) -> str:
    """Decodes raw CSV bytes using utf-8-sig, utf-8, or cp1258 (Windows-1258).

    Normalizes output to Unicode NFC for canonical Vietnamese text representation.
    """
    if not raw or not raw.strip():
        raise AppError(
            code="csv_empty",
            message="Tệp CSV rỗng hoặc chỉ chứa khoảng trắng.",
            status_code=400,
        )

    for enc in ("utf-8-sig", "utf-8", "cp1258"):
        try:
            decoded = raw.decode(enc)
            return unicodedata.normalize("NFC", decoded)
        except (UnicodeDecodeError, LookupError):
            pass

    raise AppError(
        code="csv_encoding",
        message="Không đọc được mã hóa tệp CSV. Vui lòng lưu dạng UTF-8 hoặc Windows-1258.",
        status_code=400,
    )


def detect_delimiter(sample: str) -> str:
    """Detects delimiter from text sample using csv.Sniffer, fallback to comma."""
    try:
        dialect = csv.Sniffer().sniff(sample[:4096], delimiters=",;\t")
        return dialect.delimiter
    except Exception:
        return ","


def normalize_header_col(col: str) -> str:
    """Normalizes header column name by stripping diacritics and lowercase."""
    nfkd = unicodedata.normalize("NFKD", col.strip().lower())
    without_diacritics = "".join(c for c in nfkd if not unicodedata.combining(c))
    without_diacritics = without_diacritics.replace("đ", "d").replace("Đ", "D")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", without_diacritics)
    return cleaned.strip("_")


HEADER_ALIASES = {
    "full_name": {
        "ho_ten",
        "hoten",
        "ho_va_ten",
        "hovaten",
        "full_name",
        "fullname",
        "name",
        "ten",
        "ho_ten_hoc_sinh",
    },
    "username": {
        "username",
        "ten_dang_nhap",
        "tendangnhap",
        "user",
        "ma_hoc_sinh",
        "mahocsinh",
        "tai_khoan",
        "taikhoan",
    },
    "password": {
        "password",
        "pass",
        "pwd",
        "mat_khau",
        "matkhau",
    },
    "class_code": {
        "class_code",
        "class",
        "ma_lop",
        "malop",
        "lop",
        "lop_hoc",
    },
}


def map_headers(header_row: list[str]) -> dict[str, int]:
    """Maps header column indices to standard keys ('full_name', 'username', etc.).

    Raises AppError(400, 'csv_missing_header') if required headers are absent.
    """
    col_map: dict[str, int] = {}
    for idx, col in enumerate(header_row):
        norm = normalize_header_col(col)
        for key, aliases in HEADER_ALIASES.items():
            if norm in aliases and key not in col_map:
                col_map[key] = idx
                break

    if "full_name" not in col_map or "username" not in col_map:
        raise AppError(
            code="csv_missing_header",
            message="Tệp CSV thiếu hàng tiêu đề hoặc thiếu cột bắt buộc (Họ tên, Tên đăng nhập).",
            status_code=400,
        )

    return col_map


def sanitize_csv_cell(value: str) -> str:
    """Escapes formula triggers to prevent CSV/Formula Injection attacks."""
    if not value:
        return ""
    if value[0] in FORMULA_TRIGGERS:
        return f"'{value}"
    return value


def generate_passwords_csv(records: list[dict[str, str]]) -> str:
    """Generates a UTF-8 BOM CSV string containing student credentials with injection escaping."""
    output = io.StringIO()
    # Write UTF-8 BOM
    output.write("\ufeff")
    writer = csv.writer(output, delimiter=",", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["STT", "Tên đăng nhập", "Họ và tên", "Mã lớp", "Mật khẩu"])

    for idx, r in enumerate(records, 1):
        writer.writerow(
            [
                idx,
                sanitize_csv_cell(r["username"]),
                sanitize_csv_cell(r["full_name"]),
                sanitize_csv_cell(r.get("class_code", "")),
                sanitize_csv_cell(r["password_plain"]),
            ]
        )

    return output.getvalue()


def process_csv_import(
    raw_bytes: bytes,
    db: Session,
    dry_run: bool = True,
    auto_generate_passwords: bool = False,
    default_class_id: uuid.UUID | None = None,
) -> CsvImportResult:
    """Processes CSV import in dry-run or atomic commit mode."""
    # 1. Enforce file size limit
    if len(raw_bytes) > MAX_CSV_BYTES:
        raise AppError(
            code="csv_file_too_large",
            message="Kích thước tệp CSV vượt quá giới hạn 1MB.",
            status_code=413,
        )

    # 2. Decode text
    decoded_text = decode_csv(raw_bytes)

    # 3. Detect delimiter & read rows
    delimiter = detect_delimiter(decoded_text)
    reader = csv.reader(io.StringIO(decoded_text), delimiter=delimiter)

    all_rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not all_rows:
        raise AppError(
            code="csv_empty",
            message="Tệp CSV không chứa dòng dữ liệu nào.",
            status_code=400,
        )

    header_row = all_rows[0]
    data_rows = all_rows[1:]

    if not data_rows:
        raise AppError(
            code="csv_empty",
            message="Tệp CSV chỉ có hàng tiêu đề, không có dòng dữ liệu học sinh.",
            status_code=400,
        )

    # 4. Enforce row count limit
    if len(data_rows) > MAX_CSV_ROWS:
        raise AppError(
            code="csv_too_many_rows",
            message=f"Tệp CSV vượt quá giới hạn {MAX_CSV_ROWS} dòng ({len(data_rows)} dòng).",
            status_code=422,
        )

    # 5. Map headers
    col_map = map_headers(header_row)
    idx_name = col_map["full_name"]
    idx_user = col_map["username"]
    idx_pwd = col_map.get("password")
    idx_class = col_map.get("class_code")

    # 6. Parse and pre-validate rows
    parsed_rows: list[dict] = []
    usernames_in_file: list[str] = []
    class_codes_in_file: set[str] = set()

    for idx, row in enumerate(data_rows):
        row_num = idx + 2  # Excel row 2 is first data row
        raw_name = row[idx_name].strip() if idx_name < len(row) else ""
        raw_user = row[idx_user].strip() if idx_user < len(row) else ""
        raw_pwd = row[idx_pwd].strip() if idx_pwd is not None and idx_pwd < len(row) else ""
        raw_class = row[idx_class].strip() if idx_class is not None and idx_class < len(row) else ""

        full_name = unicodedata.normalize("NFC", " ".join(raw_name.split()))
        username = raw_user.lower()
        class_code = raw_class.upper() if raw_class else ""

        parsed_rows.append(
            {
                "row_number": row_num,
                "full_name": full_name,
                "username": username,
                "raw_password": raw_pwd,
                "class_code": class_code,
            }
        )

        if username:
            usernames_in_file.append(username)
        if class_code:
            class_codes_in_file.add(class_code)

    # 7. Check for duplicate usernames within the file
    username_counts = Counter(usernames_in_file)

    # 8. Check existing usernames in database
    db_existing_users = set()
    if usernames_in_file:
        db_existing_users = set(
            db.execute(select(User.username).where(User.username.in_(list(set(usernames_in_file)))))
            .scalars()
            .all()
        )

    # 9. Check existing classes in database
    db_classes: dict[str, uuid.UUID] = {}
    if class_codes_in_file:
        rows = db.execute(
            select(Class.code, Class.id).where(Class.code.in_(list(class_codes_in_file)))
        ).all()
        for code, cid in rows:
            db_classes[code] = cid

    # If default_class_id is specified, verify it exists
    default_class_exists = False
    if default_class_id:
        default_class_exists = (
            db.execute(select(Class.id).where(Class.id == default_class_id)).scalar_one_or_none()
            is not None
        )

    # 10. Evaluate each row and build report
    row_details: list[CsvRowDetail] = []
    for item in parsed_rows:
        errors: list[str] = []
        name = item["full_name"]
        uname = item["username"]
        pwd = item["raw_password"]
        ccode = item["class_code"]

        # Validate Name
        if not name:
            errors.append("name_empty")

        # Validate Username
        if not uname or not STUDENT_USERNAME_REGEX.match(uname):
            errors.append("username_invalid")
        else:
            if username_counts[uname] > 1:
                errors.append("username_duplicate_in_file")
            if uname in db_existing_users:
                errors.append("username_taken")

        # Validate Class Code
        if ccode:
            if ccode not in db_classes:
                errors.append("class_not_found")
        elif default_class_id and not default_class_exists:
            errors.append("class_not_found")

        # Validate Password
        if pwd:
            if len(pwd) < 6 or len(pwd) > 128:
                errors.append("password_invalid")
        else:
            if not auto_generate_passwords:
                errors.append("password_required")

        status = "error" if errors else "valid"
        row_details.append(
            CsvRowDetail(
                row_number=item["row_number"],
                full_name=name,
                username=uname,
                class_code=ccode or None,
                status=status,
                errors=errors,
            )
        )

    total_rows = len(row_details)
    error_rows = sum(1 for r in row_details if r.status == "error")
    valid_rows = total_rows - error_rows
    can_commit = error_rows == 0
    estimated_hash_seconds = round(valid_rows * 0.05, 1)

    result = CsvImportResult(
        total_rows=total_rows,
        valid_rows=valid_rows,
        error_rows=error_rows,
        estimated_hash_seconds=estimated_hash_seconds,
        can_commit=can_commit,
        rows=row_details,
    )

    # If dry_run is True, return report without modifying DB
    if dry_run:
        return result

    # dry_run is False (Atomic Commit):
    if not can_commit:
        raise AppError(
            code="csv_import_validation_failed",
            message="Tệp CSV có dòng không hợp lệ. Vui lòng kiểm tra và sửa lại trước khi nhập.",
            status_code=422,
            details=result.model_dump(),
        )

    # All rows valid -> Perform atomic batch creation
    created_students: list[StudentImportedItem] = []
    password_records: list[dict[str, str]] = []

    for item in parsed_rows:
        uname = item["username"]
        name = item["full_name"]
        pwd = item["raw_password"] or generate_random_password(length=8)
        ccode = item["class_code"]

        hashed = hash_password(pwd)
        student = User(
            username=uname,
            full_name=name,
            hashed_password=hashed,
            role="student",
            is_active=True,
        )
        db.add(student)
        db.flush()

        # Determine target class id
        target_class_id: uuid.UUID | None = None
        if ccode and ccode in db_classes:
            target_class_id = db_classes[ccode]
        elif default_class_id and default_class_exists:
            target_class_id = default_class_id

        if target_class_id:
            db.add(ClassMember(class_id=target_class_id, student_id=student.id))

        created_students.append(
            StudentImportedItem(
                id=student.id,
                username=uname,
                full_name=name,
                class_code=ccode or None,
                password_plain=pwd,
            )
        )
        password_records.append(
            {
                "username": uname,
                "full_name": name,
                "class_code": ccode,
                "password_plain": pwd,
            }
        )

    db.commit()

    csv_export = generate_passwords_csv(password_records)
    result.created_count = len(created_students)
    result.students = created_students
    result.csv_export_content = csv_export

    return result
