#!/usr/bin/env python3
"""Auto-remediation script for Step 1.4: Fix AI slop and a11y issues across all 35 screens.
"""

from pathlib import Path
import re

SCREENS_DIR = Path("design/screens")

def remediate_html(content: str, filename: str) -> str:
    # 1. Fix emoji in SC-06
    if "💡" in content:
        content = content.replace("💡", '<span class="material-symbols-outlined text-xs text-brand-primary-dark align-middle" data-icon="lightbulb">lightbulb</span>')

    # 2. Fix SC-01: Remember me checkbox
    content = re.sub(
        r'<input([^>]*?)type="checkbox"([^>]*?)class="([^"]*?accent-emerald[^"]*?)"([^>]*?)>',
        r'<input\1type="checkbox"\2class="\3 focus:ring-2 focus:ring-emerald-500"\4 aria-label="Ghi nhớ đăng nhập" id="remember-me">',
        content
    )

    # 3. Fix SC-03: Agree checkbox
    content = re.sub(
        r'<input([^>]*?)id="agree-check"([^>]*?)>',
        r'<input\1id="agree-check" aria-label="Xác nhận cam kết tuân thủ quy định và bảo mật"\2>',
        content
    )

    # 4. Fix SC-04 & SC-04-offline: MCQ radio buttons
    for opt, char in [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]:
        content = re.sub(
            rf'<input([^>]*?)type="radio"([^>]*?)name="q-option"([^>]*?)value="{char}"([^>]*?)>',
            rf'<input\1type="radio"\2name="q-option"\3value="{char}"\4 aria-label="Lựa chọn {char}">',
            content
        )
        content = re.sub(
            rf'<input([^>]*?)value="{char}"([^>]*?)name="q-option"([^>]*?)type="radio"([^>]*?)>',
            rf'<input\1value="{char}"\2name="q-option"\3type="radio"\4 aria-label="Lựa chọn {char}">',
            content
        )

    # General nameless radio buttons
    content = re.sub(
        r'<input([^>]*?)type="radio"((?![^>]*aria-label)[^>]*?)>',
        r'<input\1type="radio"\2 aria-label="Phương án lựa chọn">',
        content
    )

    # 5. Fix SC-05, SC-06 & SC-13: Missing focus classes
    # Add focus classes to all button and a tags that lack focus:
    def add_focus_class(match):
        full_tag = match.group(0)
        tag_name = match.group(1)
        if "focus:" in full_tag or "focus-visible:" in full_tag:
            return full_tag
        if 'class="' in full_tag:
            return full_tag.replace('class="', 'class="focus:outline-none focus:ring-2 focus:ring-emerald-500 ')
        elif "class='" in full_tag:
            return full_tag.replace("class='", "class='focus:outline-none focus:ring-2 focus:ring-emerald-500 ")
        else:
            return f'<{tag_name} class="focus:outline-none focus:ring-2 focus:ring-emerald-500" {full_tag[len(tag_name)+1:]}'

    content = re.sub(r'<(button|a)\b[^>]*>', add_focus_class, content)

    # 6. Fix nameless select tags
    def add_select_aria(match):
        full_tag = match.group(0)
        if "aria-label" in full_tag or "id=" in full_tag:
            return full_tag
        return full_tag[:-1] + ' aria-label="Tùy chọn danh mục">'

    content = re.sub(r'<select\b[^>]*>', add_select_aria, content)

    # 7. Fix nameless text inputs
    content = re.sub(
        r'<input([^>]*?)placeholder="Tìm kiếm([^"]*?)"((?![^>]*aria-label)[^>]*?)>',
        r'<input\1placeholder="Tìm kiếm\2"\3 aria-label="Tìm kiếm \2">',
        content
    )

    # Checkboxes without aria-label
    content = re.sub(
        r'<input([^>]*?)type="checkbox"((?![^>]*aria-label)[^>]*?)>',
        r'<input\1type="checkbox"\2 aria-label="Chọn mục">',
        content
    )

    # Number inputs
    content = re.sub(
        r'<input([^>]*?)type="number"((?![^>]*aria-label)[^>]*?)>',
        r'<input\1type="number"\2 aria-label="Giá trị số">',
        content
    )

    # Password inputs
    content = re.sub(
        r'<input([^>]*?)type="password"((?![^>]*aria-label)[^>]*?)>',
        r'<input\1type="password"\2 aria-label="Mật khẩu">',
        content
    )

    # Remaining text inputs
    content = re.sub(
        r'<input([^>]*?)type="text"((?![^>]*aria-label)[^>]*?)>',
        r'<input\1type="text"\2 aria-label="Dữ liệu nhập">',
        content
    )

    # 8. Images without alt
    content = re.sub(
        r'<img((?![^>]*alt=)[^>]*?)>',
        r'<img\1 alt="Hình ảnh minh họa">',
        content
    )

    return content

def main():
    files = sorted(SCREENS_DIR.glob("*.html"))
    remediated = 0
    for f in files:
        old_content = f.read_text(encoding="utf-8")
        new_content = remediate_html(old_content, f.name)
        if new_content != old_content:
            f.write_text(new_content, encoding="utf-8")
            remediated += 1
            print(f"  -> Remediated {f.name}")

    print(f"\nRemediated {remediated}/{len(files)} screens.")
    return 0

if __name__ == "__main__":
    main()
