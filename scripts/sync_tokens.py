"""Synchronizes design/tokens.json to frontend/src/tokens.css, tailwind.config.ts, and DESIGN.md.

Ensures that updating design tokens in design/tokens.json automatically propagates
to the entire frontend codebase and design system documentation (TC-1.2-03).
"""

import json
from pathlib import Path

TOKENS_PATH = Path("design/tokens.json")
CSS_PATH = Path("frontend/src/tokens.css")
TAILWIND_CONFIG_PATH = Path("frontend/tailwind.config.ts")
DESIGN_MD_PATH = Path("DESIGN.md")


def generate_css(tokens: dict) -> str:
    light = tokens["color"]["light"]
    dark = tokens["color"]["dark"]
    typo = tokens["typography"]
    radius = tokens["radius"]

    return f"""/* ==============================================================================
 * MATHRIX DESIGN SYSTEM: TOKENS & ATOMIC STYLES (AUTO-GENERATED)
 * Do not edit manually. Run 'python3 scripts/sync_tokens.py' to regenerate.
 * ============================================================================== */

@import "@fontsource/be-vietnam-pro/400.css";
@import "@fontsource/be-vietnam-pro/500.css";
@import "@fontsource/be-vietnam-pro/600.css";
@import "@fontsource/be-vietnam-pro/700.css";
@import "@fontsource/space-grotesk/500.css";
@import "@fontsource/space-grotesk/600.css";
@import "@fontsource/space-grotesk/700.css";
@import "@fontsource/jetbrains-mono/400.css";
@import "@fontsource/jetbrains-mono/500.css";
@import "@fontsource/jetbrains-mono/600.css";
@import "katex/dist/katex.min.css";

:root {{
  /* Fonts */
  --font-sans: {typo["fonts"]["sans"]};
  --font-display: {typo["fonts"]["display"]};
  --font-mono: {typo["fonts"]["mono"]};
  --font-math: {typo["fonts"]["math"]};

  /* Light Theme */
  --bg-canvas: {light["bg"]["canvas"]};
  --bg-surface: {light["bg"]["surface"]};
  --bg-elevated: {light["bg"]["elevated"]};
  --bg-subtle-accent: {light["bg"]["subtleAccent"]};

  --text-primary: {light["text"]["primary"]};
  --text-secondary: {light["text"]["secondary"]};
  --text-muted: {light["text"]["muted"]};

  --border-subtle: {light["border"]["subtle"]};
  --border-strong: {light["border"]["strong"]};
  --border-accent: {light["border"]["accent"]};

  --brand-primary: {light["brand"]["primary"]};
  --brand-hover: {light["brand"]["hover"]};
  --brand-glow: {light["brand"]["glow"]};

  --status-correct-bg: {light["status"]["correct"]["bg"]};
  --status-correct-border: {light["status"]["correct"]["border"]};
  --status-correct-text: {light["status"]["correct"]["text"]};

  --status-wrong-bg: {light["status"]["wrong"]["bg"]};
  --status-wrong-border: {light["status"]["wrong"]["border"]};
  --status-wrong-text: {light["status"]["wrong"]["text"]};

  --status-flag-bg: {light["status"]["flag"]["bg"]};
  --status-flag-border: {light["status"]["flag"]["border"]};
  --status-flag-text: {light["status"]["flag"]["text"]};

  --timer-normal-text: {light["timer"]["normal"]["text"]};
  --timer-normal-border: {light["timer"]["normal"]["border"]};
  --timer-normal-bg: {light["timer"]["normal"]["bg"]};
  --timer-normal-dot: {light["timer"]["normal"]["dot"]};

  --timer-warning-text: {light["timer"]["warning"]["text"]};
  --timer-warning-border: {light["timer"]["warning"]["border"]};
  --timer-warning-bg: {light["timer"]["warning"]["bg"]};
  --timer-warning-dot: {light["timer"]["warning"]["dot"]};

  --timer-critical-text: {light["timer"]["critical"]["text"]};
  --timer-critical-border: {light["timer"]["critical"]["border"]};
  --timer-critical-bg: {light["timer"]["critical"]["bg"]};
  --timer-critical-dot: {light["timer"]["critical"]["dot"]};

  /* Radii */
  --radius-xs: {radius["xs"]};
  --radius-sm: {radius["sm"]};
  --radius-md: {radius["md"]};
  --radius-lg: {radius["lg"]};
  --radius-xl: {radius["xl"]};
}}

.dark {{
  /* Dark Theme */
  --bg-canvas: {dark["bg"]["canvas"]};
  --bg-surface: {dark["bg"]["surface"]};
  --bg-elevated: {dark["bg"]["elevated"]};
  --bg-subtle-accent: {dark["bg"]["subtleAccent"]};

  --text-primary: {dark["text"]["primary"]};
  --text-secondary: {dark["text"]["secondary"]};
  --text-muted: {dark["text"]["muted"]};

  --border-subtle: {dark["border"]["subtle"]};
  --border-strong: {dark["border"]["strong"]};
  --border-accent: {dark["border"]["accent"]};

  --brand-primary: {dark["brand"]["primary"]};
  --brand-hover: {dark["brand"]["hover"]};
  --brand-glow: {dark["brand"]["glow"]};

  --status-correct-bg: {dark["status"]["correct"]["bg"]};
  --status-correct-border: {dark["status"]["correct"]["border"]};
  --status-correct-text: {dark["status"]["correct"]["text"]};

  --status-wrong-bg: {dark["status"]["wrong"]["bg"]};
  --status-wrong-border: {dark["status"]["wrong"]["border"]};
  --status-wrong-text: {dark["status"]["wrong"]["text"]};

  --status-flag-bg: {dark["status"]["flag"]["bg"]};
  --status-flag-border: {dark["status"]["flag"]["border"]};
  --status-flag-text: {dark["status"]["flag"]["text"]};

  --timer-normal-text: {dark["timer"]["normal"]["text"]};
  --timer-normal-border: {dark["timer"]["normal"]["border"]};
  --timer-normal-bg: {dark["timer"]["normal"]["bg"]};
  --timer-normal-dot: {dark["timer"]["normal"]["dot"]};

  --timer-warning-text: {dark["timer"]["warning"]["text"]};
  --timer-warning-border: {dark["timer"]["warning"]["border"]};
  --timer-warning-bg: {dark["timer"]["warning"]["bg"]};
  --timer-warning-dot: {dark["timer"]["warning"]["dot"]};

  --timer-critical-text: {dark["timer"]["critical"]["text"]};
  --timer-critical-border: {dark["timer"]["critical"]["border"]};
  --timer-critical-bg: {dark["timer"]["critical"]["bg"]};
  --timer-critical-dot: {dark["timer"]["critical"]["dot"]};
}}

/* Typography Ergonomics */
.question-prose {{
  font-family: var(--font-sans);
  font-size: 1.0625rem;
  line-height: 1.8;
  color: var(--text-primary);
  letter-spacing: -0.005em;
}}

.question-prose .katex {{
  font-size: 1.08em !important;
  color: inherit !important;
}}

.question-prose .katex-display {{
  margin: 1.25rem 0;
  padding: 0.75rem 1rem;
  background-color: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow-x: auto;
}}

.tabular-nums {{
  font-variant-numeric: tabular-nums;
}}
"""


def generate_tailwind_config(tokens: dict) -> str:
    return """import type { Config } from 'tailwindcss';

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        canvas: 'var(--bg-canvas)',
        surface: 'var(--bg-surface)',
        elevated: 'var(--bg-elevated)',
        'subtle-accent': 'var(--bg-subtle-accent)',

        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-muted': 'var(--text-muted)',

        'line-subtle': 'var(--border-subtle)',
        'line-strong': 'var(--border-strong)',
        'line-accent': 'var(--border-accent)',

        brand: {
          DEFAULT: 'var(--brand-primary)',
          hover: 'var(--brand-hover)',
          glow: 'var(--brand-glow)',
        },

        status: {
          correct: {
            bg: 'var(--status-correct-bg)',
            border: 'var(--status-correct-border)',
            text: 'var(--status-correct-text)',
          },
          wrong: {
            bg: 'var(--status-wrong-bg)',
            border: 'var(--status-wrong-border)',
            text: 'var(--status-wrong-text)',
          },
          flag: {
            bg: 'var(--status-flag-bg)',
            border: 'var(--status-flag-border)',
            text: 'var(--status-flag-text)',
          },
        },

        timer: {
          normal: {
            text: 'var(--timer-normal-text)',
            border: 'var(--timer-normal-border)',
            bg: 'var(--timer-normal-bg)',
            dot: 'var(--timer-normal-dot)',
          },
          warning: {
            text: 'var(--timer-warning-text)',
            border: 'var(--timer-warning-border)',
            bg: 'var(--timer-warning-bg)',
            dot: 'var(--timer-warning-dot)',
          },
          critical: {
            text: 'var(--timer-critical-text)',
            border: 'var(--timer-critical-border)',
            bg: 'var(--timer-critical-bg)',
            dot: 'var(--timer-critical-dot)',
          },
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
        display: ['var(--font-display)'],
        mono: ['var(--font-mono)'],
        math: ['var(--font-math)'],
      },
      borderRadius: {
        xs: 'var(--radius-xs)',
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
    },
  },
  plugins: [],
} satisfies Config;
"""


def generate_design_md(tokens: dict) -> str:
    brand = tokens["brand"]
    light = tokens["color"]["light"]
    dark = tokens["color"]["dark"]
    typo = tokens["typography"]

    return f"""# {brand["name"]} DESIGN SYSTEM (DESIGN.md)

> **Archetype:** {brand["archetype"]}  
> **Aesthetic Theme:** {brand["theme"]}  
> **Source of Truth:** `design/tokens.json` (Đồng bộ qua `python3 scripts/sync_tokens.py`)

---

## 1. THIẾT LẬP THƯƠNG HIỆU & ĐỊNH HƯỚNG CỐT LÕI

- **Thương hiệu:** **{brand["name"]}** (Không sử dụng slogan).
- **Mục tiêu thị giác:** Tập trung cao độ cho bài thi Toán (nhiều công thức $\\LaTeX$) và Tin học (khối mã nguồn), đảm bảo công thái học chống mỏi mắt cho bài thi kéo dài tới 90 phút.
- **Quy tắc Chống AI Slop:**
  - Không đổ bóng mờ nhạt (loại bỏ `shadow-lg`, `shadow-xl`). Phân tách giao diện bằng **độ tương phản màu nền** và **viền sắc nét `1px solid`**.
  - Không bo góc quá đà (giới hạn tối đa `rounded-lg` 8px hoặc `rounded-xl` 12px).
  - Không sử dụng gradient tím/hồng mặc định.
  - Không dùng radio button hoặc checkbox mặc định của trình duyệt; thay thế bằng **Interactive Selectable Cards**.

---

## 2. BẢNG MÀU CHUẨN (COLOR PALETTE)

### 2.1. Dark Mode (Chủ đạo cho phòng thi & làm bài đêm)
- **Nền tổng thể (Canvas):** `{dark["bg"]["canvas"]}`
- **Bề mặt Card (Surface):** `{dark["bg"]["surface"]}`
- **Bề mặt Nâng cao (Elevated):** `{dark["bg"]["elevated"]}`
- **Màu chữ chính (Text Primary):** `{dark["text"]["primary"]}`
- **Màu chữ phụ (Text Secondary):** `{dark["text"]["secondary"]}`
- **Viền mặc định (Border Subtle):** `{dark["border"]["subtle"]}`
- **Điểm nhấn thương hiệu (Brand Emerald):** `{dark["brand"]["primary"]}` (Hover: `{dark["brand"]["hover"]}`)

### 2.2. Light Mode (Phòng học sáng ban ngày)
- **Nền tổng thể (Canvas):** `{light["bg"]["canvas"]}`
- **Bề mặt Card (Surface):** `{light["bg"]["surface"]}`
- **Bề mặt Nâng cao (Elevated):** `{light["bg"]["elevated"]}`
- **Màu chữ chính (Text Primary):** `{light["text"]["primary"]}`
- **Màu chữ phụ (Text Secondary):** `{light["text"]["secondary"]}`
- **Viền mặc định (Border Subtle):** `{light["border"]["subtle"]}`
- **Điểm nhấn thương hiệu (Brand Emerald):** `{light["brand"]["primary"]}` (Hover: `{light["brand"]["hover"]}`)

---

## 3. TYPOGRAPHY & ĐỒNG BỘ ĐA NGÔN NGỮ

1. **Văn bản Tiếng Việt (`--font-sans`):** `{typo["fonts"]["sans"]}`
2. **Số liệu & Nhãn kỹ thuật (`--font-display`):** `{typo["fonts"]["display"]}`
3. **Mã nguồn Tin học & Ô nhập số (`--font-mono`):** `{typo["fonts"]["mono"]}` (`tabular-nums`)
4. **Công thức Toán học (`--font-math`):** `{typo["fonts"]["math"]}` (Render bằng KaTeX)

---

## 4. BỘ 3 TRẠNG THÁI ĐỒNG HỒ ĐẾM NGƯỢC (ACCESSIBLE TIMER PILL)

| Trạng thái | Điều kiện kích hoạt | Màu sắc (Dark/Light) | Icon Lucide | Nhãn văn bản | Chống mù màu |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Bình thường** | Thời gian $\\ge 5$ phút | Emerald (`#10B981` / `#065F46`) | `clock` | "Bình thường" | Phân biệt bằng Icon đồng hồ + Chữ |
| **Cảnh báo** | $1 \\le$ Thời gian $< 5$ phút | Amber (`#F59E0B` / `#92400E`) | `alert-triangle` | "Sắp hết giờ" | Nhấp nháy nhẹ + Icon tam giác |
| **Khẩn cấp** | Thời gian $< 1$ phút | Red (`#EF4444` / `#991B1B`) | `alert-circle` | "Khẩn cấp" | Nhấp nháy nhanh + Icon tròn cảnh báo |

---

## 5. THÀNH PHẦN GIAO DIỆN ĐẶC THÙ

1. **Selectable Option Cards (Trắc nghiệm 4 lựa chọn):** Card viền `1px`, huy hiệu phím tắt `[A]`, `[B]`, `[C]`, `[D]`. Khi chọn, viền chuyển sang `var(--border-accent)` và nền sang `var(--bg-subtle-accent)`.
2. **Structured Table Card (Đúng/Sai 4 mệnh đề):** 4 hàng ngang riêng biệt, bên phải là cụm Segmented Toggle `[Đúng]` / `[Sai]`.
3. **Terminal Input (Trả lời ngắn):** Ô nhập số lớn font `JetBrains Mono` cỡ 1.25rem kèm hướng dẫn định dạng số rõ ràng.
4. **Bento Question Palette (Cột phải):** Lưới 5 cột `grid-cols-5`, mỗi ô vuông 40px biểu thị câu hỏi, phân biệt rõ trạng thái Đang xem, Đã làm, Chưa làm, và Đánh dấu xem lại.
"""


def main():
    with open(TOKENS_PATH, encoding="utf-8") as f:
        tokens = json.load(f)

    # 1. Write tokens.css
    css_content = generate_css(tokens)
    with open(CSS_PATH, "w", encoding="utf-8") as f:
        f.write(css_content)
    print(f"✅ Generated {CSS_PATH}")

    # 2. Write tailwind.config.ts
    tailwind_content = generate_tailwind_config(tokens)
    with open(TAILWIND_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(tailwind_content)
    print(f"✅ Generated {TAILWIND_CONFIG_PATH}")

    # 3. Write DESIGN.md
    design_md_content = generate_design_md(tokens)
    with open(DESIGN_MD_PATH, "w", encoding="utf-8") as f:
        f.write(design_md_content)
    print(f"✅ Generated {DESIGN_MD_PATH}")

    # Also keep a copy in design/DESIGN.md
    with open("design/DESIGN.md", "w", encoding="utf-8") as f:
        f.write(design_md_content)
    print("✅ Generated design/DESIGN.md")


if __name__ == "__main__":
    main()
