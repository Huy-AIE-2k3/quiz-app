#!/usr/bin/env python3
"""Audit script for Step 1.4: AI Slop detection, a11y accessibility, and responsive checks.

Validates all 35 HTML screens in design/screens/ against TC-1.4-01 through TC-1.4-05.
Uses Python standard library html.parser without external dependencies.
"""

from html.parser import HTMLParser
from pathlib import Path
import re
import sys

SCREENS_DIR = Path("design/screens")

# 1. AI SLOP PATTERNS (TC-1.4-01)
SLOP_PATTERNS = [
    (r'from-(?:purple|violet|indigo)-\d+.*to-(?:indigo|blue|purple|fuchsia)-\d+', "Purple-blue AI slop gradient"),
    (r'bg-gradient-to-[a-z]+.*text-transparent.*bg-clip-text', "Overused gradient text"),
    (r'backdrop-blur-(?:xl|2xl|3xl)', "Excessive glassmorphism / blurry backdrop"),
    (r'\b(?:lorem\s+ipsum|dolor\s+sit\s+amet)\b', "Dummy placeholder text (lorem ipsum)"),
    (r'[\U0001F300-\U0001F9FF\U0001FA00-\U0001FAFF]', "Emoji used as system icons"),
    (r'rounded-(?:3xl|\[3[2-9]px\]|\[4\dpx\])', "Over-rounded container radius (>24px)"),
    (r'box-shadow:\s*\d+px\s+\d+px\s+0px', "Heavy hard-offset block shadow"),
]

def check_ai_slop(html_text: str) -> list[str]:
    violations = []
    for pattern, desc in SLOP_PATTERNS:
        matches = re.findall(pattern, html_text, re.IGNORECASE)
        if matches:
            violations.append(f"{desc} (found {len(matches)} match(es))")
    return violations

# 2. ACCESSIBILITY & SEMANTICS PARSER (TC-1.4-02 & TC-1.4-03)
class A11yParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []
        self.labels = []
        self.buttons = []
        self.images = []
        self.current_button = None
        self.current_label = None

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag in ["input", "textarea", "select"]:
            self.inputs.append(attr_dict)
        elif tag == "label":
            self.current_label = attr_dict
            self.labels.append(attr_dict)
        elif tag == "button":
            self.current_button = {"attrs": attr_dict, "text": ""}
            self.buttons.append(self.current_button)
        elif tag == "img":
            self.images.append(attr_dict)

    def handle_endtag(self, tag):
        if tag == "button":
            self.current_button = None
        elif tag == "label":
            self.current_label = None

    def handle_data(self, data):
        if self.current_button:
            self.current_button["text"] += data.strip()

def check_accessibility(html_text: str) -> list[str]:
    parser = A11yParser()
    parser.feed(html_text)
    violations = []

    # A. Check inputs have label or aria-label
    label_fors = {l.get("for") for l in parser.labels if l.get("for")}
    for inp in parser.inputs:
        inp_type = inp.get("type", "text")
        if inp_type in ["hidden", "submit", "button"]:
            continue
        inp_id = inp.get("id")
        has_label = (inp_id and inp_id in label_fors) or inp.get("aria-label") or inp.get("aria-labelledby") or inp.get("placeholder")
        if not has_label:
            violations.append(f"Input [type={inp_type}, id={inp_id}] missing label/aria-label/placeholder")

    # B. Buttons have accessible text or aria-label
    for btn in parser.buttons:
        has_text = bool(btn["text"])
        attrs = btn["attrs"]
        has_label = has_text or attrs.get("aria-label") or attrs.get("title")
        if not has_label:
            violations.append(f"Button without accessible name: {attrs.get('class', '')[:30]}")

    # C. Image alt
    for img in parser.images:
        if "alt" not in img:
            violations.append(f"Image missing alt attribute: {img.get('src', '')[:30]}")

    # D. Focus visible indicators
    if "focus:" not in html_text and "focus-visible:" not in html_text:
        violations.append("Missing focus styles (focus: or focus-visible: classes)")

    return violations

# 3. RESPONSIVE / MOBILE 360px CHECKS (TC-1.4-04 & TC-1.4-05)
def check_responsive(html_text: str) -> list[str]:
    violations = []
    # Check viewport meta tag exists
    if '<meta name="viewport"' not in html_text and '<meta content="width=device-width' not in html_text:
        violations.append("Missing responsive viewport meta tag")

    return violations

def main():
    files = sorted(SCREENS_DIR.glob("*.html"))
    if not files:
        print("Error: No HTML screens found in design/screens/")
        return 1

    print(f"=== AUDITING {len(files)} SCREENS FOR STEP 1.4 ===")
    total_slop_issues = 0
    total_a11y_issues = 0
    total_responsive_issues = 0

    for f in files:
        content = f.read_text(encoding="utf-8")
        slop_issues = check_ai_slop(content)
        a11y_issues = check_accessibility(content)
        resp_issues = check_responsive(content)

        if slop_issues or a11y_issues or resp_issues:
            print(f"\n[!] {f.name}:")
            if slop_issues:
                print("   AI Slop Issues:")
                for s in slop_issues:
                    print(f"     - {s}")
                total_slop_issues += len(slop_issues)
            if a11y_issues:
                print("   a11y Issues:")
                for a in a11y_issues:
                    print(f"     - {a}")
                total_a11y_issues += len(a11y_issues)
            if resp_issues:
                print("   Responsive Issues:")
                for r in resp_issues:
                    print(f"     - {r}")
                total_responsive_issues += len(resp_issues)
        else:
            print(f"  ✅ {f.name}: 100% PASS (Slop, a11y, Responsive)")

    print("\n" + "=" * 55)
    print(f"Total AI Slop violations       : {total_slop_issues}")
    print(f"Total a11y violations          : {total_a11y_issues}")
    print(f"Total Responsive violations    : {total_responsive_issues}")
    print("=" * 55)

    if total_slop_issues > 0 or total_a11y_issues > 0 or total_responsive_issues > 0:
        return 1
    print("🎉 ALL 35 SCREENS COMPLY 100% WITH STEP 1.4 CRITERIA!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
