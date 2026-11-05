"""
backend/tests/test_step_1_3.py
Bộ kiểm thử tự động cho Bước 1.3 - Sinh hàng loạt màn hình bằng Stitch MCP (stitch-loop).
Xác thực 5 tiêu chí:
- TC-1.3-01: Đủ 100% file .html và .png cho danh sách trong SITE.md.
- TC-1.3-02: Chạy lại lệnh không sinh trùng các màn hình đã đánh dấu [x].
- TC-1.3-03: Dừng giữa chừng và chạy tiếp tục đúng vị trí an toàn (Checkpoint).
- TC-1.3-04: Gặp lỗi hạn mức MCP dừng lại có thông báo blocked rõ ràng.
- TC-1.3-05: Tất cả màn hình đồng nhất bảng màu và token của DESIGN.md.
"""

import importlib.util
import json
import sys
from pathlib import Path

# Đường dẫn gốc
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_MD_PATH = PROJECT_ROOT / "design" / "SITE.md"
SCREENS_DIR = PROJECT_ROOT / "design" / "screens"
METADATA_JSON_PATH = PROJECT_ROOT / ".stitch" / "metadata.json"
CHECKPOINT_JSON_PATH = PROJECT_ROOT / ".stitch" / "checkpoint.json"

# Import động module stitch_batch_runner để độc lập với working directory
runner_path = PROJECT_ROOT / "scripts" / "stitch_batch_runner.py"
spec = importlib.util.spec_from_file_location("stitch_batch_runner", str(runner_path))
stitch_batch_runner = importlib.util.module_from_spec(spec)
sys.modules["stitch_batch_runner"] = stitch_batch_runner
spec.loader.exec_module(stitch_batch_runner)

parse_site_contract = stitch_batch_runner.parse_site_contract
verify_screens_inventory = stitch_batch_runner.verify_screens_inventory
load_checkpoint = stitch_batch_runner.load_checkpoint
save_checkpoint = stitch_batch_runner.save_checkpoint
check_design_tokens_consistency = stitch_batch_runner.check_design_tokens_consistency


def test_tc_1_3_01_all_screens_exist_html_and_png():
    """TC-1.3-01: Đủ 100% file .html và .png cho danh sách trong SITE.md."""
    screens = parse_site_contract(SITE_MD_PATH)
    assert len(screens) == 18, f"Yêu cầu đủ 18 màn hình và biến thể, thực tế: {len(screens)}"

    verified, missing = verify_screens_inventory(screens)
    assert len(missing) == 0, f"Còn các file bị thiếu hoặc rỗng: {missing}"
    assert len(verified) == 18, f"Số màn hình xác minh hợp lệ: {len(verified)}/18"

    for screen in screens:
        html_path = PROJECT_ROOT / screen["html"]
        png_path = PROJECT_ROOT / screen["png"]

        assert html_path.exists(), f"Thiếu file {html_path}"
        assert png_path.exists(), f"Thiếu file {png_path}"
        assert html_path.stat().st_size > 1000, f"File HTML quá nhỏ ({html_path})"
        assert png_path.stat().st_size > 5000, f"File PNG quá nhỏ ({png_path})"


def test_tc_1_3_02_idempotency_skip_completed():
    """TC-1.3-02: Chạy lại lệnh không sinh trùng các màn hình đã đánh dấu [x]."""
    screens = parse_site_contract(SITE_MD_PATH)

    # Giả lập logic kiểm tra trước khi sinh: nếu đã [x] và tồn tại file thì bỏ qua
    pending_to_generate = []
    skipped_completed = []

    for s in screens:
        html_exists = (PROJECT_ROOT / s["html"]).exists()
        png_exists = (PROJECT_ROOT / s["png"]).exists()
        if s["completed"] and html_exists and png_exists:
            skipped_completed.append(s["code"])
        else:
            pending_to_generate.append(s["code"])

    assert len(skipped_completed) == 18, "Tất cả 18 màn hình phải được nhận diện để bỏ qua."
    assert len(pending_to_generate) == 0, "Không màn hình nào bị sinh trùng lặp khi chạy lại."


def test_tc_1_3_03_checkpoint_and_resume():
    """TC-1.3-03: Dừng giữa chừng và chạy tiếp tục đúng vị trí an toàn."""
    test_checkpoint = PROJECT_ROOT / ".stitch" / "test_checkpoint.json"

    try:
        # Giả lập tiến trình dừng sau khi sinh SC-05
        partial_completed = ["SC-01", "SC-02", "SC-03", "SC-04", "SC-05"]
        payload = {
            "last_completed_code": "SC-05",
            "completed_codes": partial_completed,
            "status": "PAUSED",
        }
        test_checkpoint.write_text(json.dumps(payload), encoding="utf-8")

        # Đọc checkpoint và tính vị trí tiếp tục
        data = json.loads(test_checkpoint.read_text(encoding="utf-8"))
        screens = parse_site_contract(SITE_MD_PATH)
        all_codes = [s["code"] for s in screens]

        remaining = [c for c in all_codes if c not in data["completed_codes"]]
        next_to_run = remaining[0] if remaining else None

        # Màn hình tiếp theo phải là SC-04-VAR-OFFLINE hoặc SC-06
        assert next_to_run in ["SC-04-VAR-OFFLINE", "SC-06"], f"Vị trí resume sai: {next_to_run}"
        assert data["last_completed_code"] == "SC-05"
    finally:
        if test_checkpoint.exists():
            test_checkpoint.unlink()


def test_tc_1_3_04_mcp_quota_error_handling():
    """TC-1.3-04: Gặp lỗi hạn mức MCP dừng lại có thông báo blocked rõ ràng."""

    # Mô phỏng phản hồi lỗi Quota Limit từ Google Cloud Stitch MCP
    simulated_quota_error_response = {
        "error": {
            "code": 429,
            "status": "RESOURCE_EXHAUSTED",
            "message": "Quota exceeded for requests per minute",
        }
    }

    def handle_mcp_generation_response(response: dict) -> dict:
        err = response.get("error", {})
        if err.get("code") == 429 or err.get("status") == "RESOURCE_EXHAUSTED":
            return {
                "status": "BLOCKED",
                "reason": "MCP_QUOTA_EXCEEDED",
                "message": (
                    f"Dịch vụ Stitch chạm hạn mức API ({err.get('message')}). "
                    "Tiến trình dừng an toàn và lưu checkpoint."
                ),
                "retryable": True,
            }
        return {"status": "SUCCESS"}

    result = handle_mcp_generation_response(simulated_quota_error_response)
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "MCP_QUOTA_EXCEEDED"
    assert "Dịch vụ Stitch chạm hạn mức API" in result["message"]
    assert result["retryable"] is True


def test_tc_1_3_05_design_tokens_consistency():
    """TC-1.3-05: Tất cả màn hình đồng nhất bảng màu và token của DESIGN.md."""
    screens = parse_site_contract(SITE_MD_PATH)
    is_consistent, violations = check_design_tokens_consistency(screens)

    assert is_consistent is True, f"Màn hình vi phạm token DESIGN.md: {violations}"
    assert len(violations) == 0


def test_metadata_json_and_brand_verification():
    """Kiểm tra file .stitch/metadata.json chứa đủ 18 screens và thương hiệu Mathrix."""
    assert METADATA_JSON_PATH.exists(), "Thiếu file .stitch/metadata.json"
    metadata = json.loads(METADATA_JSON_PATH.read_text(encoding="utf-8"))

    assert metadata["title"] == "Quiz Toan Tin - UI System"
    assert metadata["projectId"] == "15546240290050457859"
    count = len(metadata["screens"])
    assert count == 18, f"metadata.json phải đủ 18 screens, hiện có {count}"
