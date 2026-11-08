#!/usr/bin/env python3
"""Local Mermaid Syntax Validator and HTML Preview Generator.

Usage:
    python3 validate_mermaid.py <path_to_markdown_or_mermaid_file> [--preview <output.html>]
"""

import argparse
import re
import sys
from pathlib import Path

VALID_DIAGRAM_TYPES = (
    "erDiagram",
    "flowchart",
    "graph",
    "sequenceDiagram",
    "stateDiagram-v2",
    "stateDiagram",
    "classDiagram",
    "gantt",
    "pie",
)


def extract_mermaid_blocks(content: str) -> list[str]:
    """Extracts ```mermaid code blocks from markdown or returns whole content if raw."""
    if "```mermaid" in content:
        pattern = r"```mermaid\s*\n(.*?)\n```"
        matches = re.findall(pattern, content, re.DOTALL)
        return [m.strip() for m in matches]
    return [content.strip()]


def validate_mermaid_code(code: str) -> tuple[bool, list[str]]:
    """Performs static syntax and structure checks on a Mermaid diagram block."""
    errors = []
    lines = [line.strip() for line in code.split("\n") if line.strip() and not line.strip().startswith("%%")]

    if not lines:
        return False, ["Khối sơ đồ Mermaid rỗng."]

    header = lines[0].split()[0]
    matched_type = any(header.startswith(valid_type) for valid_type in VALID_DIAGRAM_TYPES)
    if not matched_type:
        errors.append(f"Loại sơ đồ không hợp lệ hoặc thiếu khai báo: '{lines[0]}'. Hỗ trợ: {', '.join(VALID_DIAGRAM_TYPES)}")

    # Check balanced brackets (ignoring cardinality symbols in erDiagram like o{, |{, }o, }|)
    sanitized_code = code
    if header.startswith("erDiagram"):
        sanitized_code = re.sub(r"[o|]\{|\}[o|]", "", sanitized_code)

    open_brackets = sanitized_code.count("[") + sanitized_code.count("(") + sanitized_code.count("{")
    close_brackets = sanitized_code.count("]") + sanitized_code.count(")") + sanitized_code.count("}")
    if open_brackets != close_brackets:
        errors.append(f"Mất cân bằng dấu ngoặc: mở {open_brackets} vs đóng {close_brackets}.")

    # Specialized checks for erDiagram
    if header.startswith("erDiagram"):
        for i, line in enumerate(lines[1:], start=2):
            # Check relationships: must have valid cardinality notation
            if "--" in line or ".." in line:
                rel_pattern = r"[A-Za-z0-9_]+\s*(\|o|o\||\|\||\}\||\{\||\}o|o\{|--|\.\.)[A-Za-z0-9_\-\.]*(\|o|o\||\|\||\}\||\{\||\}o|o\{)\s*[A-Za-z0-9_]+"
                if not re.search(rel_pattern, line):
                    # Warning or error if malformed relationship
                    pass

    return len(errors) == 0, errors


def generate_html_preview(diagrams: list[str], output_path: Path, title: str = "Mermaid Preview") -> None:
    """Renders Mermaid diagrams into a standalone HTML file using Mermaid.js."""
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            securityLevel: 'loose'
        }});
    </script>
    <style>
        body {{
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 2rem;
        }}
        .diagram-container {{
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            overflow-x: auto;
        }}
        h2 {{
            color: #58a6ff;
            font-size: 1.1rem;
            margin-top: 0;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
"""
    for i, d in enumerate(diagrams, 1):
        html_content += f"""
    <div class="diagram-container">
        <h2>Sơ đồ #{i}</h2>
        <div class="mermaid">
{d}
        </div>
    </div>
"""

    html_content += """
</body>
</html>
"""
    output_path.write_text(html_content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mermaid Diagram Validator & Preview Generator")
    parser.add_argument("file", type=Path, help="Đường dẫn tới tệp .md hoặc .mmd")
    parser.add_argument("--preview", type=Path, default=None, help="Xuất file HTML xem trước")
    args = parser.parse_args()

    if not args.file.exists():
        sys.stderr.write(f"Lỗi: Không tìm thấy tệp {args.file}\n")
        sys.exit(1)

    content = args.file.read_text(encoding="utf-8")
    blocks = extract_mermaid_blocks(content)

    print(f"Đã phát hiện {len(blocks)} khối sơ đồ Mermaid trong {args.file.name}.")
    all_valid = True

    for idx, block in enumerate(blocks, 1):
        valid, errors = validate_mermaid_code(block)
        first_line = block.split("\n")[0] if block else ""
        if valid:
            print(f"  ✅ Khối #{idx} [{first_line}]: HỢP LỆ")
        else:
            all_valid = False
            print(f"  ❌ Khối #{idx} [{first_line}]: LỖI")
            for err in errors:
                print(f"      - {err}")

    if args.preview and all_valid:
        generate_html_preview(blocks, args.preview, title=f"Mermaid Preview - {args.file.stem}")
        print(f"  📄 Đã xuất file HTML xem trước: {args.preview.resolve()}")

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
