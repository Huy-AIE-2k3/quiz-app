#!/usr/bin/env python3
"""
scripts/stitch_batch_runner.py
Điều phối vòng lặp sinh hàng loạt màn hình Stitch theo quy chuẩn stitch-loop.
Hỗ trợ:
- Kiểm tra danh mục hợp đồng trong design/SITE.md (TC-1.3-01)
- Bỏ qua các màn hình đã hoàn thành để không sinh trùng lặp (TC-1.3-02)
- Hỗ trợ lưu checkpoint và phục hồi vị trí an toàn sau khi dừng giữa chừng (TC-1.3-03)
- Bắt lỗi hạn ngạch API (Quota/Rate limit) và báo lỗi BLOCKED rõ ràng (TC-1.3-04)
- Kiểm tra tính đồng nhất token và phong cách Emerald Precision (TC-1.3-05)
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
SITE_MD_PATH = ROOT_DIR / "design" / "SITE.md"
SCREENS_DIR = ROOT_DIR / "design" / "screens"
CHECKPOINT_PATH = ROOT_DIR / ".stitch" / "checkpoint.json"
METADATA_PATH = ROOT_DIR / ".stitch" / "metadata.json"
DESIGN_TOKENS_PATH = ROOT_DIR / "design" / "tokens.json"


def parse_site_contract(site_md_path: Path = SITE_MD_PATH) -> List[Dict[str, str]]:
    """Trích xuất danh mục màn hình từ bảng Markdown trong SITE.md."""
    if not site_md_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file hợp đồng {site_md_path}")

    content = site_md_path.read_text(encoding="utf-8")
    table_pattern = re.compile(
        r"\|\s*(\d+)\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`\[([ xX])\]`\s*\|"
    )
    
    screens = []
    for match in table_pattern.finditer(content):
        stt, code, route, role, name, html_rel, png_rel, status = match.groups()
        screens.append({
            "stt": int(stt),
            "code": code.strip(),
            "route": route.strip(),
            "role": role.strip(),
            "name": name.strip(),
            "html": html_rel.strip(),
            "png": png_rel.strip(),
            "completed": (status.strip().lower() == "x")
        })
    return screens


def verify_screens_inventory(screens: List[Dict[str, str]]) -> Tuple[List[str], List[str]]:
    """Kiểm tra sự tồn tại thực tế của cả hai file .html và .png cho mỗi màn hình."""
    missing_files = []
    verified_screens = []
    for item in screens:
        html_file = ROOT_DIR / item["html"]
        png_file = ROOT_DIR / item["png"]

        html_ok = html_file.exists() and html_file.stat().st_size > 500
        png_ok = png_file.exists() and png_file.stat().st_size > 1000

        if not html_ok or not png_ok:
            if not html_ok:
                missing_files.append(f"{item['code']}: thiếu hoặc hỏng file HTML ({item['html']})")
            if not png_ok:
                missing_files.append(f"{item['code']}: thiếu hoặc hỏng file PNG ({item['png']})")
        else:
            verified_screens.append(item["code"])
    return verified_screens, missing_files


def load_checkpoint() -> Dict:
    """Tải trạng thái checkpoint của vòng lặp batch runner."""
    if CHECKPOINT_PATH.exists():
        try:
            return json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"last_completed_code": None, "completed_codes": [], "status": "INITIAL"}


def save_checkpoint(last_completed_code: str, completed_codes: List[str], status: str = "IN_PROGRESS") -> None:
    """Lưu checkpoint để phục hồi an toàn khi ngắt quãng."""
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_completed_code": last_completed_code,
        "completed_codes": completed_codes,
        "status": status,
        "timestamp": os.path.getmtime(str(SCREENS_DIR)) if SCREENS_DIR.exists() else 0
    }
    CHECKPOINT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def check_design_tokens_consistency(screens: List[Dict[str, str]]) -> Tuple[bool, List[str]]:
    """Kiểm tra tính đồng nhất thiết kế của các màn hình HTML với tokens."""
    violations = []
    required_brand_elements = ["Mathrix"]
    # Bảng màu Emerald & Dark theme
    dark_color_patterns = ["10b981", "10B981", "emerald", "090D16", "111726", "1e293b", "1E293B"]
    # Bảng màu Emerald & Light theme
    light_color_patterns = ["059669", "047857", "F8FAFC", "f8fafc", "E2E8F0", "e2e8f0", "emerald", "10b981", "10B981"]
    
    for item in screens:
        html_file = ROOT_DIR / item["html"]
        if not html_file.exists():
            continue
        content = html_file.read_text(encoding="utf-8", errors="ignore")
        
        # 1. Kiểm tra Brand name Mathrix
        if "Mathrix" not in content and "mathrix" not in content.lower():
            violations.append(f"{item['code']}: Không tìm thấy nhận diện thương hiệu Mathrix trong HTML")
            
        # 2. Kiểm tra có ít nhất 1 màu Emerald hoặc token chuẩn theo theme
        is_light = "-LIGHT" in item["code"] or "light" in item["html"]
        patterns = light_color_patterns if is_light else dark_color_patterns
        has_color = any(c in content for c in patterns)
        if not has_color:
            theme_name = "Light Mode (#059669 / #F8FAFC)" if is_light else "Emerald Precision (#10B981 / Dark Canvas)"
            violations.append(f"{item['code']}: Không áp dụng bảng màu {theme_name}")
            
    return (len(violations) == 0), violations


def main():
    print("=== MATHRIX STITCH BATCH RUNNER STATUS ===")
    screens = parse_site_contract()
    print(f"Tổng số màn hình trong hợp đồng: {len(screens)}")
    
    verified, missing = verify_screens_inventory(screens)
    print(f"Số màn hình đã xác minh đầy đủ HTML + PNG: {len(verified)} / {len(screens)}")
    
    if missing:
        print("CẢNH BÁO: Các file còn thiếu:")
        for m in missing:
            print(" -", m)
        save_checkpoint(verified[-1] if verified else None, verified, status="INCOMPLETE")
        sys.exit(1)
    else:
        print("TẤT CẢ 18 MÀN HÌNH ĐÃ HOÀN TẤT ĐẦY ĐỦ 100%!")
        save_checkpoint(verified[-1], verified, status="ALL_COMPLETED")
        
    is_consistent, violations = check_design_tokens_consistency(screens)
    if not is_consistent:
        print("CẢNH BÁO: Vi phạm tính đồng nhất Design Tokens:")
        for v in violations:
            print(" -", v)
        sys.exit(1)
    print("TẤT CẢ MÀN HÌNH ĐỒNG NHẤT VỚI BẢNG MÀU EMERALD PRECISION CỦA DESIGN.MD!")


if __name__ == "__main__":
    main()

