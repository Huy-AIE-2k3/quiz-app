#!/usr/bin/env python3
"""Generate WCAG AA compliant Light Mode variants for all Mathrix screens.

Matches tokens defined in design/tokens.json.
"""

from pathlib import Path
import re
import sys

BASE_SCREENS = [
    "SC-01-login",
    "SC-02-student-exams",
    "SC-03-exam-lobby",
    "SC-04-assessment-workspace",
    "SC-04-offline-state",
    "SC-05-exam-submitted",
    "SC-07-admin-dashboard",
    "SC-08-admin-classes",
    "SC-09-class-detail-csv",
    "SC-10-admin-students",
    "SC-11-admin-exams",
    "SC-12-exam-editor",
    "SC-13-exam-preview",
    "SC-14-exam-monitor",
    "SC-15-exam-grading",
    "SC-16-exam-analytics",
    "SC-17-admin-settings",
]

def convert_to_light_mode(content: str, filename: str) -> str:
    # 1. Switch root class
    content = re.sub(r'<html([^>]*?)class="dark"([^>]*?)>', r'<html\1class="light"\2>', content)
    content = re.sub(r'<html([^>]*?)class=\'dark\'([^>]*?)>', r'<html\1class="light"\2>', content)

    # 2. Update title to indicate Light Mode
    content = re.sub(r'<title>(.*?)</title>', r'<title>\1 (Giao diện sáng)</title>', content)

    # 3. Update tailwind config color values to Light Mode tokens
    # Dark -> Light Hex Replacements
    color_replacements = [
        # Dark Canvas -> Light Canvas #F8FAFC
        (r'["\']#090D16["\']', '"#F8FAFC"'),
        (r'["\']#0e1511["\']', '"#F8FAFC"'),
        (r'["\']#09100c["\']', '"#FFFFFF"'),
        (r'["\']#161d19["\']', '"#F8FAFC"'),
        # Dark Surface -> Light Surface #FFFFFF
        (r'["\']#111726["\']', '"#FFFFFF"'),
        (r'["\']#1a211d["\']', '"#F1F5F9"'),
        # Dark Elevated -> Light Elevated #F1F5F9
        (r'["\']#1A2234["\']', '"#F1F5F9"'),
        (r'["\']#242c27["\']', '"#F1F5F9"'),
        (r'["\']#2f3632["\']', '"#E2E8F0"'),
        (r'["\']#343b36["\']', '"#FFFFFF"'),
        # Dark Borders -> Light Borders
        (r'["\']#1E293B["\']', '"#E2E8F0"'),
        (r'["\']#334155["\']', '"#CBD5E1"'),
        (r'["\']#3c4a42["\']', '"#E2E8F0"'),
        (r'["\']#3c4a5e["\']', '"#E2E8F0"'),
        # Text colors: Primary -> #0F172A, Secondary -> #475569, Muted -> #94A3B8
        (r'["\']#F1F5F9["\']', '"#0F172A"'),
        (r'["\']#dde4dd["\']', '"#0F172A"'),
        (r'["\']#bbcabf["\']', '"#475569"'),
        (r'["\']#94A3B8["\']', '"#475569"'),
        (r'["\']#64748B["\']', '"#94A3B8"'),
        (r'["\']#86948a["\']', '"#94A3B8"'),
        (r'["\']#b9c7e0["\']', '"#475569"'),
        (r'["\']#abb9d2["\']', '"#475569"'),
        # Brand colors: Dark Emerald #10B981 -> Light Primary #059669, Hover #047857
        (r'["\']#10B981["\']', '"#059669"'),
        (r'["\']#10b981["\']', '"#059669"'),
        (r'["\']#4edea3["\']', '"#059669"'),
        (r'["\']#6ffbbe["\']', '"#059669"'),
        (r'["\']#34D399["\']', '"#047857"'),
        (r'["\']#005236["\']', '"#FFFFFF"'),
        (r'["\']#003824["\']', '"#FFFFFF"'),
        (r'["\']#002113["\']', '"#FFFFFF"'),
        (r'["\']#00422b["\']', '"#065F46"'),
        # Glow & Selected
        (r'rgba\(16,\s*185,\s*129,\s*0\.1[0-9]*\)', '"#ECFDF5"'),
        (r'rgba\(16,\s*185,\s*129,\s*0\.18\)', 'rgba(5, 150, 105, 0.12)'),
        (r'rgba\(16,\s*185,\s*129,\s*0\.05\)', 'rgba(5, 150, 105, 0.05)'),
    ]

    for pattern, repl in color_replacements:
        content = re.sub(pattern, repl, content)

    # 4. Styles in <style> block (gradients, scrollbars, paper)
    content = content.replace("#090D16", "#F8FAFC")
    content = content.replace("#111726", "#FFFFFF")
    content = content.replace("#1A2234", "#F1F5F9")
    content = content.replace("#1E293B", "#E2E8F0")
    content = content.replace("#334155", "#CBD5E1")
    content = content.replace("#131924", "#FFFFFF")
    content = content.replace("rgba(30, 41, 59, 0.35)", "rgba(226, 232, 240, 0.8)")
    content = content.replace("rgba(30, 41, 59, 0.25)", "rgba(226, 232, 240, 0.8)")

    # 5. Direct tailwind classes adjustments where slate/white is hardcoded
    # Keep button text on brand solid as white/canvas
    content = re.sub(r'\btext-slate-100\b', 'text-slate-800', content)
    content = re.sub(r'\btext-slate-200\b', 'text-slate-700', content)
    content = re.sub(r'\btext-slate-300\b', 'text-slate-600', content)
    content = re.sub(r'\bplaceholder-slate-500\b', 'placeholder-slate-400', content)
    content = re.sub(r'\bbg-surface-canvas\b', 'bg-canvas', content)

    # 6. Mode toggle icon
    content = content.replace('>dark_mode<', '>light_mode<')
    content = content.replace('data-icon="dark_mode"', 'data-icon="light_mode"')

    return content

def main():
    screens_dir = Path("design/screens")
    generated_count = 0

    print("Generating Light Mode screens...")
    for base_name in BASE_SCREENS:
        dark_file = screens_dir / f"{base_name}.html"
        light_file = screens_dir / f"{base_name}-light.html"

        if not dark_file.exists():
            print(f"Warning: {dark_file} does not exist, skipping.")
            continue

        dark_content = dark_file.read_text(encoding="utf-8")
        light_content = convert_to_light_mode(dark_content, base_name)
        light_file.write_text(light_content, encoding="utf-8")
        print(f"  -> Generated {light_file.name}")
        generated_count += 1

    print(f"\nSuccessfully generated {generated_count} Light Mode screens!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
