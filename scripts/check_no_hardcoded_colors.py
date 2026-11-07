#!/usr/bin/env python3
"""
TC-1.5-04: Check that no hardcoded hex (#xxxxxx) or rgb(...) color codes
exist in frontend/src/ component files (excluding tokens.css/style tokens).
"""

import sys
import re
from pathlib import Path

SRC_DIR = Path("frontend/src")
EXCLUDE_FILES = {"tokens.css", "tokens.test.tsx"}

# Regex for #hex (3, 6, 8 hex digits) or rgb/rgba
HEX_COLOR_PATTERN = re.compile(r'#[0-9a-fA-F]{3,8}\b')
RGB_COLOR_PATTERN = re.compile(r'\brgba?\s*\(')

def check_hardcoded_colors() -> int:
    violations = []

    for file_path in SRC_DIR.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.name in EXCLUDE_FILES or file_path.suffix not in {".ts", ".tsx", ".css"}:
            continue

        lines = file_path.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, start=1):
            # Ignore comments
            clean_line = re.sub(r'//.*$', '', line)
            clean_line = re.sub(r'/\*.*?\*/', '', clean_line)

            # Check hex colors
            hex_matches = HEX_COLOR_PATTERN.findall(clean_line)
            if hex_matches:
                for match in hex_matches:
                    violations.append((file_path, idx, f"Hardcoded HEX color '{match}'", line.strip()))

            # Check rgb/rgba colors
            rgb_matches = RGB_COLOR_PATTERN.findall(clean_line)
            if rgb_matches:
                for match in rgb_matches:
                    violations.append((file_path, idx, f"Hardcoded RGB color '{match}'", line.strip()))

    print("==================================================================")
    print("  TC-1.5-04: KIỂM TRA MÃ MÀU HARDCODE TRONG FRONTEND/SRC")
    print("==================================================================")

    if violations:
        print(f"❌ PHÁT HIỆN {len(violations)} VI PHẠM:")
        for path, line_no, desc, snippet in violations:
            print(f"  - {path}:{line_no}: {desc}")
            print(f"      Code: {snippet}")
        return 1
    else:
        print("✅ 100% TUÂN THỦ: 0 mã màu hardcode trong frontend/src/!")
        print("   Mọi màu sắc đều được điều khiển qua Design Tokens (tokens.css / Tailwind).")
        return 0

if __name__ == "__main__":
    sys.exit(check_hardcoded_colors())

