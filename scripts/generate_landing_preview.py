#!/usr/bin/env python3
"""Generate a preview PNG for SC-00-landing.html matching the Dark theme, Rubik cube colors, and dotted grid."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_PATH = Path("design/screens/SC-00-landing.png")

def create_landing_preview():
    width = 1920
    height = 1080
    img = Image.new("RGB", (width, height), "#090D16")
    draw = ImageDraw.Draw(img)

    # 1. Draw subtle dot grid
    grid_spacing = 28
    for x in range(0, width, grid_spacing):
        for y in range(0, height, grid_spacing):
            draw.point((x, y), fill=(30, 41, 59))

    # 2. Draw spotlight glow on canvas
    center_x, center_y = 600, 500
    for r in range(400, 0, -20):
        alpha_intensity = int(18 * (1 - r / 400))
        # subtle radial rings
        draw.ellipse(
            [center_x - r, center_y - r, center_x + r, center_y + r],
            outline=(16, 185, 129, alpha_intensity)
        )

    # 3. Header bar
    draw.rectangle([0, 0, width, 80], fill="#0A0F1D", outline="#1E293B")
    draw.rectangle([60, 22, 96, 58], fill="#111726", outline="#10B981")
    # Draw M logo
    draw.text((72, 28), "M", fill="#10B981")
    draw.text((112, 30), "Mathrix", fill="#F9FAFB")
    draw.text((width - 320, 30), "Đăng nhập", fill="#94A3B8")
    draw.rectangle([width - 200, 20, width - 60, 60], fill="#10B981", outline="#10B981")
    draw.text((width - 170, 32), "Vào phòng thi", fill="#090D16")

    # 4. Hero Content (Left)
    draw.rectangle([60, 180, 480, 212], fill="#111726", outline="#1E293B")
    draw.text((80, 188), "NỀN TẢNG KHẢO THÍ TOÁN & TIN HỌC CHUYÊN SÂU", fill="#10B981")

    # Headline
    draw.text((60, 260), "Test đến đâu,", fill="#F9FAFB")
    draw.text((60, 340), "hiểu mình đến đó", fill="#10B981")

    # Subtext
    draw.text((60, 440), "Đánh giá chuẩn xác năng lực tư duy, định vị lỗ hổng kiến thức", fill="#94A3B8")
    draw.text((60, 470), "thông qua hệ sinh thái đề thi Toán học & Lập trình chuẩn hóa.", fill="#94A3B8")

    # Action Buttons
    draw.rectangle([60, 530, 260, 585], fill="#10B981")
    draw.text((95, 548), "Bắt đầu khảo sát ->", fill="#090D16")

    draw.rectangle([280, 530, 480, 585], fill="#111726", outline="#334155")
    draw.text((320, 548), "Đăng nhập hệ thống", fill="#F9FAFB")

    # 5. Right side: 3D Rubik Cube cluster (Red, Emerald, Black)
    cube_base_x = 1350
    cube_base_y = 480
    size = 72

    # Draw isometric rubik mini cubes (red #EF4444, emerald #10B981, black #1E293B)
    colors = [
        ("#10B981", "#EF4444", "#1E293B"),
        ("#EF4444", "#1E293B", "#10B981"),
        ("#1E293B", "#10B981", "#EF4444")
    ]

    for layer in range(3):
        ly = cube_base_y - (layer * 80)
        for row in range(3):
            for col in range(3):
                cx = cube_base_x + (col - 1) * 75 - (row - 1) * 35
                cy = ly + (row - 1) * 35 + (col - 1) * 20
                c_top, c_left, c_right = colors[(layer + row + col) % 3]

                # Top rhombus
                draw.polygon([
                    (cx, cy - 30),
                    (cx + 40, cy - 10),
                    (cx, cy + 10),
                    (cx - 40, cy - 10)
                ], fill=c_top, outline="#090D16")

                # Left side
                draw.polygon([
                    (cx - 40, cy - 10),
                    (cx, cy + 10),
                    (cx, cy + 50),
                    (cx - 40, cy + 30)
                ], fill=c_left, outline="#090D16")

                # Right side
                draw.polygon([
                    (cx, cy + 10),
                    (cx + 40, cy - 10),
                    (cx + 40, cy + 30),
                    (cx, cy + 50)
                ], fill=c_right, outline="#090D16")

    # 6. Bottom Bento Cards
    bento_y = 780
    card_w = 400
    for idx, (title, color) in enumerate([("Đa dạng dạng bài Toán & Tin", "#10B981"), ("Báo cáo phổ điểm & Phân tích", "#EF4444"), ("Trải nghiệm thi tập trung", "#10B981")]):
        bx = 60 + idx * (card_w + 30)
        draw.rectangle([bx, bento_y, bx + card_w, bento_y + 160], fill="#111726", outline="#1E293B")
        draw.rectangle([bx + 20, bento_y + 20, bx + 60, bento_y + 60], fill=color)
        draw.text((bx + 20, bento_y + 80), title, fill="#F9FAFB")

    # 7. Footer
    draw.rectangle([0, height - 60, width, height], fill="#090D16", outline="#1E293B")
    draw.text((width // 2 - 180, height - 40), "Hệ thống nội bộ, vui lòng không chia sẻ ra bên ngoài", fill="#64748B")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT_PATH)
    print(f"Successfully generated {OUTPUT_PATH}")

if __name__ == "__main__":
    create_landing_preview()

