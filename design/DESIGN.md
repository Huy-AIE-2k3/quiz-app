# Mathrix DESIGN SYSTEM (DESIGN.md)

> **Archetype:** Modern Academic Technical Assessment (Math & CS)  
> **Aesthetic Theme:** Emerald Precision  
> **Source of Truth:** `design/tokens.json` (Đồng bộ qua `python3 scripts/sync_tokens.py`)

---

## 1. THIẾT LẬP THƯƠNG HIỆU & ĐỊNH HƯỚNG CỐT LÕI

- **Thương hiệu:** **Mathrix** (Không sử dụng slogan).
- **Mục tiêu thị giác:** Tập trung cao độ cho bài thi Toán (nhiều công thức $\LaTeX$) và Tin học (khối mã nguồn), đảm bảo công thái học chống mỏi mắt cho bài thi kéo dài tới 90 phút.
- **Quy tắc Chống AI Slop:**
  - Không đổ bóng mờ nhạt (loại bỏ `shadow-lg`, `shadow-xl`). Phân tách giao diện bằng **độ tương phản màu nền** và **viền sắc nét `1px solid`**.
  - Không bo góc quá đà (giới hạn tối đa `rounded-lg` 8px hoặc `rounded-xl` 12px).
  - Không sử dụng gradient tím/hồng mặc định.
  - Không dùng radio button hoặc checkbox mặc định của trình duyệt; thay thế bằng **Interactive Selectable Cards**.

---

## 2. BẢNG MÀU CHUẨN (COLOR PALETTE)

### 2.1. Dark Mode (Chủ đạo cho phòng thi & làm bài đêm)
- **Nền tổng thể (Canvas):** `#090D16`
- **Bề mặt Card (Surface):** `#111726`
- **Bề mặt Nâng cao (Elevated):** `#1A2234`
- **Màu chữ chính (Text Primary):** `#F1F5F9`
- **Màu chữ phụ (Text Secondary):** `#94A3B8`
- **Viền mặc định (Border Subtle):** `#1E293B`
- **Điểm nhấn thương hiệu (Brand Emerald):** `#10B981` (Hover: `#34D399`)

### 2.2. Light Mode (Phòng học sáng ban ngày)
- **Nền tổng thể (Canvas):** `#F8FAFC`
- **Bề mặt Card (Surface):** `#FFFFFF`
- **Bề mặt Nâng cao (Elevated):** `#F1F5F9`
- **Màu chữ chính (Text Primary):** `#0F172A`
- **Màu chữ phụ (Text Secondary):** `#475569`
- **Viền mặc định (Border Subtle):** `#E2E8F0`
- **Điểm nhấn thương hiệu (Brand Emerald):** `#059669` (Hover: `#047857`)

---

## 3. TYPOGRAPHY & ĐỒNG BỘ ĐA NGÔN NGỮ

1. **Văn bản Tiếng Việt (`--font-sans`):** `'Be Vietnam Pro', 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif`
2. **Số liệu & Nhãn kỹ thuật (`--font-display`):** `'Space Grotesk', system-ui, sans-serif`
3. **Mã nguồn Tin học & Ô nhập số (`--font-mono`):** `'JetBrains Mono', 'Fira Code', monospace` (`tabular-nums`)
4. **Công thức Toán học (`--font-math`):** `'KaTeX_Main', 'Times New Roman', serif` (Render bằng KaTeX)

---

## 4. BỘ 3 TRẠNG THÁI ĐỒNG HỒ ĐẾM NGƯỢC (ACCESSIBLE TIMER PILL)

| Trạng thái | Điều kiện kích hoạt | Màu sắc (Dark/Light) | Icon Lucide | Nhãn văn bản | Chống mù màu |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Bình thường** | Thời gian $\ge 5$ phút | Emerald (`#10B981` / `#065F46`) | `clock` | "Bình thường" | Phân biệt bằng Icon đồng hồ + Chữ |
| **Cảnh báo** | $1 \le$ Thời gian $< 5$ phút | Amber (`#F59E0B` / `#92400E`) | `alert-triangle` | "Sắp hết giờ" | Nhấp nháy nhẹ + Icon tam giác |
| **Khẩn cấp** | Thời gian $< 1$ phút | Red (`#EF4444` / `#991B1B`) | `alert-circle` | "Khẩn cấp" | Nhấp nháy nhanh + Icon tròn cảnh báo |

---

## 5. THÀNH PHẦN GIAO DIỆN ĐẶC THÙ

1. **Selectable Option Cards (Trắc nghiệm 4 lựa chọn):** Card viền `1px`, huy hiệu phím tắt `[A]`, `[B]`, `[C]`, `[D]`. Khi chọn, viền chuyển sang `var(--border-accent)` và nền sang `var(--bg-subtle-accent)`.
2. **Structured Table Card (Đúng/Sai 4 mệnh đề):** 4 hàng ngang riêng biệt, bên phải là cụm Segmented Toggle `[Đúng]` / `[Sai]`.
3. **Terminal Input (Trả lời ngắn):** Ô nhập số lớn font `JetBrains Mono` cỡ 1.25rem kèm hướng dẫn định dạng số rõ ràng.
4. **Bento Question Palette (Cột phải):** Lưới 5 cột `grid-cols-5`, mỗi ô vuông 40px biểu thị câu hỏi, phân biệt rõ trạng thái Đang xem, Đã làm, Chưa làm, và Đánh dấu xem lại.
