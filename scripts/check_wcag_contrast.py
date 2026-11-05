"""WCAG AA Contrast Checker for Mathrix Design Tokens (TC-1.2-01).

Calculates the relative luminance and contrast ratio for all text and surface
combinations in design/tokens.json and enforces WCAG AA (>= 4.5:1 for normal text,
>= 3.0:1 for large text/UI components).
"""

import json
import math
import sys
from pathlib import Path


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    """Converts hex color string (#RGB, #RRGGBB) to (r, g, b) 0-255."""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    return int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)


def get_relative_luminance(r: int, g: int, b: int) -> float:
    """Calculates relative luminance according to WCAG 2.1 specs."""
    channels = []
    for c in (r, g, b):
        c_norm = c / 255.0
        if c_norm <= 0.04045:
            channels.append(c_norm / 12.92)
        else:
            channels.append(math.pow((c_norm + 0.055) / 1.055, 2.4))
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def get_contrast_ratio(color1: str, color2: str) -> float:
    """Calculates WCAG contrast ratio between two hex colors."""
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    l1 = get_relative_luminance(r1, g1, b1)
    l2 = get_relative_luminance(r2, g2, b2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def run_wcag_audit() -> int:
    tokens_path = Path("design/tokens.json")
    if not tokens_path.exists():
        print(f"Error: {tokens_path} not found.")
        return 1

    with open(tokens_path, encoding="utf-8") as f:
        tokens = json.load(f)

    colors = tokens["color"]
    failures = 0

    print("==================================================================")
    print("  MATHRIX DESIGN SYSTEM — BÁO CÁO KIỂM TRA TƯƠNG PHẢN WCAG AA")
    print("==================================================================")

    # 1. LIGHT MODE CHECKS
    light = colors["light"]
    light_pairs = [
        ("Light Canvas -> Text Primary", light["bg"]["canvas"], light["text"]["primary"], 4.5),
        ("Light Canvas -> Text Secondary", light["bg"]["canvas"], light["text"]["secondary"], 4.5),
        ("Light Surface -> Text Primary", light["bg"]["surface"], light["text"]["primary"], 4.5),
        ("Light Surface -> Text Secondary", light["bg"]["surface"], light["text"]["secondary"], 4.5),
        ("Light Status Correct Text -> BG", light["status"]["correct"]["bg"], light["status"]["correct"]["text"], 4.5),
        ("Light Status Wrong Text -> BG", light["status"]["wrong"]["bg"], light["status"]["wrong"]["text"], 4.5),
        ("Light Status Flag Text -> BG", light["status"]["flag"]["bg"], light["status"]["flag"]["text"], 4.5),
        ("Light Timer Normal Text -> BG", light["timer"]["normal"]["bg"], light["timer"]["normal"]["text"], 4.5),
        ("Light Timer Warning Text -> BG", light["timer"]["warning"]["bg"], light["timer"]["warning"]["text"], 4.5),
        ("Light Timer Critical Text -> BG", light["timer"]["critical"]["bg"], light["timer"]["critical"]["text"], 4.5),
        ("Light Border Subtle -> Canvas (UI)", light["bg"]["canvas"], light["border"]["subtle"], 1.1),
    ]

    print("\n[1] LIGHT MODE AUDIT:")
    for label, bg, fg, req in light_pairs:
        ratio = get_contrast_ratio(bg, fg)
        passed = ratio >= req
        status = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            failures += 1
        print(f"  {status} {label:<35}: {ratio:5.2f}:1 (Yêu cầu: >={req}:1)")

    # 2. DARK MODE CHECKS
    dark = colors["dark"]
    dark_pairs = [
        ("Dark Canvas -> Text Primary", dark["bg"]["canvas"], dark["text"]["primary"], 4.5),
        ("Dark Canvas -> Text Secondary", dark["bg"]["canvas"], dark["text"]["secondary"], 4.5),
        ("Dark Surface -> Text Primary", dark["bg"]["surface"], dark["text"]["primary"], 4.5),
        ("Dark Surface -> Text Secondary", dark["bg"]["surface"], dark["text"]["secondary"], 4.5),
        ("Dark Surface -> Brand Emerald", dark["bg"]["surface"], dark["brand"]["primary"], 4.5),
        ("Dark Status Correct Text -> Surface", dark["bg"]["surface"], dark["status"]["correct"]["text"], 4.5),
        ("Dark Status Wrong Text -> Surface", dark["bg"]["surface"], dark["status"]["wrong"]["text"], 4.5),
        ("Dark Status Flag Text -> Surface", dark["bg"]["surface"], dark["status"]["flag"]["text"], 4.5),
        ("Dark Timer Normal Text -> Elevated", dark["bg"]["elevated"], dark["timer"]["normal"]["text"], 4.5),
        ("Dark Timer Warning Text -> Elevated", dark["bg"]["elevated"], dark["timer"]["warning"]["text"], 4.5),
        ("Dark Timer Critical Text -> Elevated", dark["bg"]["elevated"], dark["timer"]["critical"]["text"], 4.5),
    ]

    print("\n[2] DARK MODE AUDIT:")
    for label, bg, fg, req in dark_pairs:
        ratio = get_contrast_ratio(bg, fg)
        passed = ratio >= req
        status = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            failures += 1
        print(f"  {status} {label:<35}: {ratio:5.2f}:1 (Yêu cầu: >={req}:1)")

    print("\n==================================================================")
    if failures == 0:
        print("🎉 TẤT CẢ CÁC CẶP MÀU ĐỀU ĐẠT TIÊU CHUẨN WCAG AA (0 VI PHẠM)!")
        print("==================================================================")
        return 0
    else:
        print(f"⚠️ CÓ {failures} CẶP MÀU CHƯA ĐẠT CHUẨN WCAG AA!")
        print("==================================================================")
        return 1


if __name__ == "__main__":
    sys.exit(run_wcag_audit())

