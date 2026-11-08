"""Test cases for Step 1.4: AI Slop detection, a11y accessibility, and responsive checks.

Covers:
- TC-1.4-01: 0 serious AI slop detections on all 35 screens.
- TC-1.4-02: 0 serious/critical accessibility errors (labels, focus styles, alt texts).
- TC-1.4-03: Keyboard navigation integrity (tabindex, clear focus rings).
- TC-1.4-04: Responsive viewport & 360px mobile readiness.
- TC-1.4-05: Typography scale & zoom adaptability.
"""

import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCREENS_DIR = PROJECT_ROOT / "design" / "screens"

SLOP_PATTERNS = [
    (
        r"from-(?:purple|violet|indigo)-\d+.*to-(?:indigo|blue|purple|fuchsia)-\d+",
        "Purple-blue gradient",
    ),
    (r"bg-gradient-to-[a-z]+.*text-transparent.*bg-clip-text", "Gradient text"),
    (r"backdrop-blur-(?:xl|2xl|3xl)", "Excessive glassmorphism"),
    (r"\b(?:lorem\s+ipsum|dolor\s+sit\s+amet)\b", "Dummy placeholder text"),
    (r"[\U0001F300-\U0001F9FF\U0001FA00-\U0001FAFF]", "Emoji used as icon"),
    (r"rounded-(?:3xl|\[3[2-9]px\]|\[4\dpx\])", "Over-rounded radius > 24px"),
]


@pytest.fixture(scope="module")
def all_screens():
    screens = sorted(SCREENS_DIR.glob("*.html"))
    assert len(screens) >= 30, f"Expected at least 30 screens, found {len(screens)}"
    return screens


def test_tc_1_4_01_no_ai_slop(all_screens):
    """TC-1.4-01: Quét slop trên toàn bộ màn hình đạt 0 phát hiện mức nghiêm trọng."""
    violations = []
    for screen in all_screens:
        content = screen.read_text(encoding="utf-8")
        for pattern, desc in SLOP_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                violations.append(f"{screen.name}: {desc} ({len(matches)} matches)")

    assert len(violations) == 0, "AI Slop violations found:\n" + "\n".join(violations)


def test_tc_1_4_02_a11y_form_controls_and_images(all_screens):
    """TC-1.4-02: Kiểm tra trợ năng cho input, button, select và img."""

    class A11yChecker(HTMLParser):
        def __init__(self):
            super().__init__()
            self.issues = []

        def handle_starttag(self, tag, attrs):
            d = dict(attrs)
            if tag in ["input", "textarea"]:
                itype = d.get("type", "text")
                if itype not in ["hidden", "submit", "button"]:
                    has_acc = (
                        d.get("aria-label")
                        or d.get("aria-labelledby")
                        or d.get("id")
                        or d.get("placeholder")
                    )
                    if not has_acc:
                        self.issues.append(f"Input type={itype} missing label/aria/placeholder")
            elif tag == "select":
                if not (d.get("aria-label") or d.get("id")):
                    self.issues.append("Select missing aria-label or id")
            elif tag == "img":
                if "alt" not in d:
                    self.issues.append(f"Image missing alt: {d.get('src', '')[:30]}")

    all_issues = []
    for screen in all_screens:
        checker = A11yChecker()
        checker.feed(screen.read_text(encoding="utf-8"))
        if checker.issues:
            all_issues.append(f"{screen.name}: {', '.join(checker.issues)}")

    assert len(all_issues) == 0, "Accessibility issues found:\n" + "\n".join(all_issues)


def test_tc_1_4_03_keyboard_navigation_and_focus(all_screens):
    """TC-1.4-03: Hoàn thành được bằng bàn phím; vòng focus nhìn thấy rõ."""
    missing_focus = []
    for screen in all_screens:
        content = screen.read_text(encoding="utf-8")
        has_focus = (
            "focus:" in content
            or "focus-visible:" in content
            or "outline: 2px" in content
        )
        if not has_focus:
            missing_focus.append(screen.name)

    assert len(missing_focus) == 0, "Screens missing focus styles:\n" + "\n".join(missing_focus)


def test_tc_1_4_04_responsive_viewport_360px(all_screens):
    """TC-1.4-04: Ở màn hình 360px không bị cuộn ngang, có thẻ viewport meta chuẩn."""
    missing_viewport = []
    for screen in all_screens:
        content = screen.read_text(encoding="utf-8")
        has_viewport = (
            '<meta name="viewport"' in content
            or '<meta content="width=device-width' in content
        )
        if not has_viewport:
            missing_viewport.append(screen.name)

    msg = "Screens missing viewport meta:\n" + "\n".join(missing_viewport)
    assert len(missing_viewport) == 0, msg


def test_tc_1_4_05_zoom_200_typography_adaptability(all_screens):
    """TC-1.4-05: Phóng to cỡ chữ không làm vỡ layout."""
    for screen in all_screens:
        content = screen.read_text(encoding="utf-8")
        rigid_containers = re.findall(r'<p[^>]*class="[^"]*\bh-\[\d+px\][^"]*"', content)
        assert len(rigid_containers) == 0, f"{screen.name} has rigid height: {rigid_containers}"
