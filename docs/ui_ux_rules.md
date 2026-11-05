# DESIGN SYSTEM & UI/UX SPECIFICATION: MATH & CS QUIZ PLATFORM
> **Document Role:** Master UI/UX Directive & Anti-AI Slop Guardrails for AI Coding Agents.
> **Aesthetic Archetype:** "Emerald Precision" — Inspired by `datathon.site`, Supabase UI, Linear, and Brilliant.org.
> **Target Domain:** High-focus Academic Assessment Platform for Mathematics ($\LaTeX$-heavy) and Computer Science (Code-heavy), tailored for Vietnamese students & educators.

---

## 1. TRIẾT LÝ THIẾT KẾ CỐT LÕI (CORE DESIGN PHILOSOPHY)

1. **Precision & Technical Elegance (Sự chuẩn xác kỹ thuật):** Giao diện mang hơi hướng công nghệ hiện đại (Bento Grid, viền `1px` sắc nét, nền tối sâu có chiều sâu tinh tế, điểm nhấn màu xanh Emerald), tạo cảm hứng học tập như một nền tảng Developer/Data Science chuyên nghiệp.
2. **Zero Eye-Strain Ergonomics (Công thái học thị giác cho bài thi 90 phút):** Đề thi Toán và Tin đòi hỏi học sinh đọc hàng ngàn ký tự công thức $\LaTeX$ nhỏ và các khối mã nguồn. **Tuyệt đối không** dùng màu xanh lá neon chói lóa trên nền đen tuyền gây hiện tượng lóa chữ (halation). Độ tương phản phải dịu mắt nhưng rõ nét.
3. **Keyboard-First & Low-Latency UX:** Tối ưu hóa cho thao tác nhanh bằng cả chuột và bàn phím, phản hồi tức thì dưới `100ms`, không có hiệu ứng chuyển cảnh rườm rà làm gián đoạn luồng suy nghĩ.

---

## 2. QUY TẮC CHỐNG "AI SLOP" (STRICT ANTI-AI SLOP GUARDRAILS)

AI Agent **BẮT BUỘC TUÂN THỦ** các lệnh cấm dưới đây khi sinh mã HTML/CSS/Tailwind/React. Vi phạm bất kỳ điều nào đều bị coi là lỗi thiết kế nghiêm trọng:

### ❌ NHỮNG ĐIỀU TUYỆT ĐỐI CẤM (NEVER DO):
* **CẤM Gradient Tím/Hồng/Xanh Dương mặc định của AI:** Không bao giờ sử dụng `from-indigo-500 via-purple-500 to-pink-500` hoặc bất kỳ màu xanh tím nào ngoài bảng màu Emerald/Slate đã quy định.
* **CẤM Đổ bóng mờ nhạt kiểu cũ (Muddy Shadows):** Không dùng `shadow-lg`, `shadow-xl`, `shadow-2xl` mặc định của Tailwind trên các thẻ câu hỏi. Sự phân tách giữa các lớp bề mặt (surfaces) phải được thực hiện bằng **độ lệch màu nền (luminance stepping)** và **viền `1px solid` sắc nét**.
* **CẤM Bo góc quá đà (Over-rounding):** Không dùng `rounded-2xl` hay `rounded-3xl` cho khung đề bài hoặc đáp án. Giới hạn tối đa ở `rounded-lg` (`8px`) hoặc `rounded-xl` (`12px`) để giữ nét kỹ thuật cứng cáp như `datathon.site` và Supabase.
* **CẤM Glassmorphism lạm dụng:** Không rải `backdrop-blur-md bg-white/10` tràn lan trên vùng đọc đề bài vì làm giảm độ sắc nét của công thức $\LaTeX$. Chỉ cho phép `backdrop-blur` ở thanh Sticky Header trên cùng.
* **CẤM Radio Button / Checkbox mặc định của trình duyệt:** Các lựa chọn A, B, C, D phải được thiết kế thành **Interactive Selectable Cards** có chỉ báo phím tắt (`[A]`, `[B]`, `[C]`, `[D]`).
* **CẤM lạm dụng Emoji & Icon vô nghĩa:** Không chèn icon tên lửa 🚀, tia sét ⚡, hay pháo hoa 🎉 vào giao diện làm bài. Chỉ sử dụng bộ icon nét mảnh kỹ thuật (`Lucide Icons` hoặc `Phosphor Icons` với `stroke-width: 1.75px`).
* **CẤM nhảy bố cục (Layout Shift):** Khi chọn đáp án hoặc mở rộng lời giải, kích thước khung viền không được giật cục (không đổi `border` từ `1px` sang `2px` làm đẩy dòng chữ; hãy dùng `ring-1` hoặc đổi màu `border`).

---

## 3. HỆ THỐNG MÀU SẮC (COLOR TOKENS & THEMING)

Sử dụng hệ biến CSS (CSS Custom Properties) kết hợp Tailwind CSS. Hỗ trợ chuyển đổi mượt mà giữa **Light Mode** (Mặc định cho phòng học sáng) và **Dark Mode** (Phong cách Datathon/Supabase cho tự học ban đêm).

### 3.1. Bảng mã màu chuẩn (CSS Variables)

```css
:root {
  /* === LIGHT MODE (Sáng, Sạch, Chuẩn học thuật như Brilliant.org) === */
  --bg-canvas: #F8FAFC;          /* Slate 50 - Nền tổng thể của trang */
  --bg-surface: #FFFFFF;         /* Trắng tinh - Nền Card câu hỏi, Sidebar */
  --bg-elevated: #F1F5F9;        /* Slate 100 - Nền khối Code, Hover nhẹ */
  --bg-subtle-accent: #ECFDF5;   /* Emerald 50 - Nền của đáp án đang được chọn */

  --text-primary: #0F172A;       /* Slate 900 - Chữ đề bài, Công thức LaTeX chính */
  --text-secondary: #475569;     /* Slate 600 - Chữ phụ, chú thích, nhãn */
  --text-muted: #94A3B8;         /* Slate 400 - Placeholder, trạng thái vô hiệu */

  --border-subtle: #E2E8F0;      /* Slate 200 - Viền mặc định 1px */
  --border-strong: #CBD5E1;      /* Slate 300 - Viền khi hover */
  --border-accent: #059669;      /* Emerald 600 - Viền đáp án đang chọn */

  --brand-primary: #059669;      /* Emerald 600 - Nút chính, điểm nhấn chủ đạo */
  --brand-hover: #047857;        /* Emerald 700 - Hover nút chính */
  --brand-glow: rgba(5, 150, 105, 0.12);

  /* Semantic Status Colors (Light) */
  --status-correct-bg: #ECFDF5;
  --status-correct-border: #10B981;
  --status-correct-text: #065F46;

  --status-wrong-bg: #FEF2F2;
  --status-wrong-border: #EF4444;
  --status-wrong-text: #991B1B;

  --status-flag-bg: #FFFBEB;
  --status-flag-border: #F59E0B;
  --status-flag-text: #92400E;
}

.dark {
  /* === DARK MODE (Đen sâu + Xanh Emerald chuẩn Datathon.site / Supabase) === */
  --bg-canvas: #090D16;          /* Đen ánh thép cực sâu (Không dùng #000000) */
  --bg-surface: #111726;         /* Nền Card câu hỏi tách biệt rõ với Canvas */
  --bg-elevated: #1A2234;        /* Nền khối Code, ô Input, Hover nhẹ */
  --bg-subtle-accent: rgba(16, 185, 129, 0.10); /* Nền đáp án đang chọn */

  --text-primary: #F1F5F9;       /* Trắng ngà dịu mắt (Chống lóa khi đọc LaTeX) */
  --text-secondary: #94A3B8;     /* Xám bạc cho thông tin phụ */
  --text-muted: #64748B;         /* Xám tối */

  --border-subtle: #1E293B;      /* Viền 1px mảnh tạo khung Bento Grid */
  --border-strong: #334155;      /* Viền khi hover chuột qua đáp án */
  --border-accent: #10B981;      /* Emerald 500 - Viền phát sáng nhẹ khi chọn */

  --brand-primary: #10B981;      /* Emerald 500 - Xanh lá đặc trưng */
  --brand-hover: #34D399;        /* Emerald 400 - Sáng hơn khi hover trên nền tối */
  --brand-glow: rgba(16, 185, 129, 0.18);

  /* Semantic Status Colors (Dark) */
  --status-correct-bg: rgba(16, 185, 129, 0.12);
  --status-correct-border: #10B981;
  --status-correct-text: #6EE7B7;

  --status-wrong-bg: rgba(239, 68, 68, 0.12);
  --status-wrong-border: #EF4444;
  --status-wrong-text: #FCA5A5;

  --status-flag-bg: rgba(245, 158, 11, 0.12);
  --status-flag-border: #F59E0B;
  --status-flag-text: #FCD34D;
}
```

### 3.2. Hiệu ứng nền đặc trưng (Subtle Atmospheric Background)
* **Chỉ áp dụng ở trang Dashboard / Trang chờ vào thi (Lobby):** Sử dụng lưới điểm mờ (Dot Matrix hoặc Grid `24px x 24px` với đường kẻ `1px` độ mờ `3%`) kết hợp một vùng sáng Radial Gradient cực nhẹ (`radial-gradient(circle at 50% 0%, var(--brand-glow), transparent 60%)`) ở phía trên cùng.
* **Trong màn hình làm bài (Active Quiz View):** Nền phải hoàn toàn tĩnh và sạch (`var(--bg-canvas)`), không có hiệu ứng động gây mất tập trung.

---

## 4. HỆ THỐNG TYPOGRAPHY (VIỆT HÓA + $\LaTeX$ + CODE)

Đề thi Toán và Tin học tại Việt Nam có sự pha trộn mật độ cao giữa **tiếng Việt có dấu**, **công thức toán học ($\LaTeX$)** và **mã nguồn (C++, Python, Pascal, SQL)**.

### 4.1. Bộ 4 Font chữ bắt buộc
1. **UI & Văn bản Tiếng Việt (`--font-sans`):** `'Be Vietnam Pro'`, dự phòng `'Plus Jakarta Sans'`, `sans-serif`.
   * *Lý do:* Thiết kế chuyên biệt cho dấu thanh tiếng Việt (dấu sắc, nặng, hỏi, ngã gọn gàng, không va chạm vào căn bậc hai hoặc phân số ở dòng trên/dưới).
2. **Số liệu, Đồng hồ đếm ngược, Điểm số & Nhãn kỹ thuật (`--font-display`):** `'Space Grotesk'`, `sans-serif`.
   * *Lý do:* Mang lại chất "Datathon/Sci-Fi" hiện đại cho các con số thống kê, số thứ tự câu hỏi (`Câu 01/50`) và bộ đếm giờ.
3. **Mã nguồn Tin học & Ô nhập đáp số (`--font-mono`):** `'JetBrains Mono'`, `monospace`.
   * *Lý do:* Phân biệt cực rõ số `0` và chữ `O`, số `1`, chữ `l` và chữ `I`. Bật `font-variant-numeric: tabular-nums` cho mọi bộ đếm thời gian để khung giờ không bị rung lắc mỗi giây.
4. **Công thức Toán học (`--font-math`):** Render bằng thư viện **KaTeX** (`KaTeX_Main`).

### 4.2. Tinh chỉnh CSS bắt buộc cho $\LaTeX$ và Tiếng Việt
AI khi viết CSS cho vùng hiển thị câu hỏi (`.question-prose`) **phải** nạp đoạn cấu hình sau:

```css
.question-prose {
  font-family: var(--font-sans);
  font-size: 1.0625rem; /* 17px - Kích thước vàng cho đọc đề thi trên Desktop */
  line-height: 1.8;     /* Giãn dòng rộng để chứa công thức phân số inline */
  color: var(--text-primary);
  letter-spacing: -0.005em;
}

/* Đồng bộ kích thước và màu sắc của KaTeX với Be Vietnam Pro */
.question-prose .katex {
  font-size: 1.08em !important;
  color: inherit !important;
}

/* Công thức toán dạng khối (Display Math $$...$$) */
.question-prose .katex-display {
  margin: 1.25rem 0;
  padding: 0.75rem 1rem;
  background-color: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 0.5rem;
  overflow-x: auto; /* Cuộn ngang mượt trên màn hình nhỏ nếu phương trình dài */
}
```

---

## 5. KIẾN TRÚC BỐ CỤC & THÀNH PHẦN ĐẶC THÙ (COMPONENT ARCHITECTURE)

Giao diện làm bài được thiết kế hỗ trợ đầy đủ **Cấu trúc đề thi THPT Quốc gia mới của Bộ GD&ĐT Việt Nam** (gồm 3 phần: Trắc nghiệm 4 lựa chọn, Trắc nghiệm Đúng/Sai 4 mệnh đề, và Trả lời ngắn điền đáp số) cũng như bài tập lập trình.

### 5.1. Bố cục màn hình làm bài (The Assessment Workspace)
* **Top Navigation Bar (Sticky, cao `56px`):**
  * Trái: Nút thoát an toàn + Tên bài kiểm tra + Badge môn học (`TOÁN 12` / `TIN HỌC - C++`).
  * Giữa: **Countdown Timer Pill** — đặt trong khung `border: 1px solid var(--border-subtle)`, font `JetBrains Mono` (`tabular-nums`), có chấm tròn xanh lá nhấp nháy nhẹ. Khi còn dưới 5 phút, chuyển viền và chữ sang màu Amber (`#F59E0B`).
  * Phải: Nút đổi giao diện Sáng/Tối (Icon Mặt trời/Mặt trăng) + Nút **Nộp bài** (`bg-[var(--brand-primary)]`, chữ trắng/đen tùy độ tương phản, bo góc `6px`).
* **Main Workspace (Max-width `1360px`, căn giữa, chia 2 cột trên Desktop `lg:grid-cols-12`, `gap-6`, `p-6`):**
  * **Cột Trái (`lg:col-span-8` hoặc `9`):** Khu vực hiển thị câu hỏi (Focus Zone).
  * **Cột Phải (`lg:col-span-4` hoặc `3`, Sticky):** **Bento Question Palette** (Bảng điều hướng câu hỏi, tiến độ làm bài, bộ lọc câu đã đánh dấu).

### 5.2. Đặc tả chi tiết 3 Dạng Câu Hỏi (Question Component Specs)

#### Dạng 1: Trắc nghiệm 4 lựa chọn (Multiple Choice A, B, C, D)
* Không dùng Radio button tròn. Mỗi đáp án là một **Selectable Card**:
  * Cấu trúc: `[Badge Phím tắt A/B/C/D (32x32px)]` + `[Nội dung đáp án có thể chứa LaTeX hoặc Code]`.
  * Trạng thái Mặc định: `bg-[var(--bg-surface)]`, `border: 1px solid var(--border-subtle)`, `rounded-lg`, `p-4`.
  * Trạng thái Hover: `border-[var(--border-strong)]`, `bg-[var(--bg-elevated)]`.
  * Trạng thái Đang chọn (Selected): `border-[var(--border-accent)]`, `bg-[var(--bg-subtle-accent)]`, `ring-1 ring-[var(--border-accent)]`. Badge chữ cái `[A]` đổi sang nền `var(--brand-primary)` và chữ trắng/đen đậm.

#### Dạng 2: Trắc nghiệm Đúng / Sai 4 ý (a, b, c, d) — *Đặc thù đề Toán/Tin mới*
* Hiển thị dưới dạng một **Structured Table Card** liền mạch có viền `1px solid var(--border-subtle)`:
  * Mỗi hàng là một mệnh đề `a)`, `b)`, `c)`, `d)` nằm bên trái (chiếm 75% chiều rộng).
  * Bên phải mỗi hàng (25% chiều rộng) là cụm **Segmented Toggle 2 nút**: `[ Đúng ]` và `[ Sai ]`.
  * Khi học sinh chọn `Đúng` hoặc `Sai`, nút đó sáng lên với viền và nền `var(--brand-primary)`. Các hàng phân cách nhau bằng đường kẻ ngang `1px solid var(--border-subtle)`.

#### Dạng 3: Trả lời ngắn / Điền đáp số (Short Numerical Answer)
* Khu vực nhập đáp số được thiết kế giống một **Terminal Input / Scientific Box**:
  * Ô input lớn (`h-12`, `w-64`), font `JetBrains Mono` cỡ `1.25rem`, chữ căn giữa hoặc căn trái rõ ràng.
  * Kèm dòng hướng dẫn nhỏ bên dưới bằng `--text-secondary`: *"Chỉ nhập số, dấu trừ (-) và dấu phẩy (,) thập phân. Ví dụ: -12,5"*.
  * Hiển thị một khung **Preview trực quan** nhỏ bên cạnh nếu cần kiểm tra định dạng số đã nhập.

#### Khối hiển thị Code cho môn Tin học (Code Snippet Block)
* Mọi đoạn code trong đề bài hoặc đáp án phải nằm trong khung kiểu IDE tối giản:
  * Header nhỏ (`h-8`, `px-4`, `bg-[var(--bg-elevated)]`, `border-b border-[var(--border-subtle)]`): Hiển thị tên ngôn ngữ (`Python 3.10`, `C++17`, `SQL`) bằng font `JetBrains Mono` cỡ `12px` ở góc trái, kèm nút `Copy` nhỏ gọn (chỉ bật ở chế độ Ôn tập/Xem lời giải, ẩn khi đang thi).
  * Bật đánh số dòng (`line-numbers`) màu mờ `--text-muted` để đề bài có thể hỏi *"Tại dòng số 7, biến `s` có giá trị bao nhiêu?"*.

### 5.3. Bảng điều hướng câu hỏi (Bento Question Palette - Cột phải)
* Thiết kế dạng lưới `grid-cols-5 gap-2`:
  * Mỗi ô câu hỏi là một nút vuông bo góc nhẹ (`h-10`, `rounded-md`, font `Space Grotesk` cỡ `14px`, `font-medium`).
  * **Chưa trả lời:** `bg-[var(--bg-elevated)]`, `text-[var(--text-secondary)]`, `border border-[var(--border-subtle)]`.
  * **Đang xem (Active):** Có viền ngoài `ring-2 ring-[var(--text-primary)]`.
  * **Đã trả lời:** `bg-[var(--brand-primary)]`, chữ trắng (Light mode) hoặc chữ `#090D16` đậm (Dark mode), `border-transparent`.
  * **Đánh dấu xem lại (Flagged):** Có một chấm tròn màu vàng Amber (`#F59E0B`) ở góc trên bên phải của ô số, hoặc viền màu `#F59E0B`.

---

## 6. TƯƠNG TÁC VI MÔ & PHÍM TẮT (MICRO-INTERACTIONS & ACCESSIBILITY)

Để sản phẩm mang lại cảm giác "xịn" và mượt mà như Linear hay Supabase:
1. **Hỗ trợ bàn phím toàn diện (Keyboard Navigation):**
   * Phím `1`, `2`, `3`, `4` hoặc `A`, `B`, `C`, `D`: Chọn nhanh đáp án trong câu trắc nghiệm.
   * Phím `←` / `→` (Mũi tên Trái/Phải): Chuyển câu trước / câu tiếp theo.
   * Phím `F` hoặc `Space`: Đánh dấu (Flag) câu hỏi cần kiểm tra lại.
   * Hiển thị một thanh gợi ý phím tắt siêu mảnh ở dưới đáy màn hình (`[A-D] Chọn đáp án • [←/→] Chuyển câu • [F] Đánh dấu`) bằng font `JetBrains Mono` cỡ `12px`, màu `--text-muted`.
2. **Chế độ Xem Lời Giải Chi Tiết (Post-Quiz Review Mode):**
   * Sau khi nộp bài, bên dưới mỗi câu hỏi xuất hiện một khối **Solution Accordion** có viền trái dày `3px solid var(--brand-primary)`, nền `var(--bg-elevated)`, trình bày lời giải chi tiết bằng $\LaTeX$ hoặc giải thích thuật toán từng bước.

---

## 7. CHECKLIST KIỂM TRA TRƯỚC KHI XUẤT CODE (PRE-FLIGHT VERIFICATION FOR AI)

Trước khi trả kết quả code UI cho người dùng, AI phải tự đối chiếu qua 6 câu hỏi sau:
- [ ] **1.** Đã import đủ 3 Google Fonts (`Be Vietnam Pro`, `Space Grotesk`, `JetBrains Mono`) và CSS của `KaTeX` chưa?
- [ ] **2.** Giao diện Dark Mode có đúng tông `#090D16` (nền) + `#111726` (card) + `#10B981` (xanh Emerald) của phong cách Datathon/Supabase không? Có bị lẫn màu tím/xanh dương mặc định của Tailwind không?
- [ ] **3.** Các thẻ Card đã sử dụng `border: 1px solid var(--border-subtle)` thay vì đổ bóng mờ nhạt chưa?
- [ ] **4.** Công thức Toán có được căn chỉnh `line-height: 1.8` để không bị cắt dấu tiếng Việt hoặc dính vào nhau không?
- [ ] **5.** Các ô đáp án A, B, C, D đã được làm dạng Selectable Card có phím tắt thay vì `<input type="radio">` mặc định chưa?
- [ ] **6.** Giao diện đã hỗ trợ cả 3 dạng câu hỏi (4 lựa chọn, Đúng/Sai 4 ý, Trả lời ngắn) và khối Code có đánh số dòng cho môn Tin học chưa?