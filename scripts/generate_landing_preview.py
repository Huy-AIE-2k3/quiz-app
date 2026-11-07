#!/usr/bin/env python3
"""Generate a preview PNG for SC-00-landing.html matching the minimal stage:
Only the image content + 1 Login button (no top navbar, no stats 450+, no docker sandbox, no bento cards).
"""

from pathlib import Path
from PIL import Image, ImageDraw

OUTPUT_PATH = Path("design/screens/SC-00-landing.png")

def create_landing_preview():
    width = 1920
    height = 1080
    img = Image.new("RGB", (width, height), "#090D16")
    draw = ImageDraw.Draw(img)

    # 1. Subtle Dotted Grid
    grid_spacing = 28
    for x in range(0, width, grid_spacing):
        for y in range(0, height, grid_spacing):
            draw.point((x, y), fill=(35, 48, 68))

    # 2. Spotlight glow on canvas
    center_x, center_y = 650, 480
    for r in range(450, 0, -20):
        alpha = int(16 * (1 - r / 450))
        draw.ellipse(
            [center_x - r, center_y - r, center_x + r, center_y + r],
            outline=(16, 185, 129, alpha)
        )

    # 3. Left Stage: Category Pill
    draw.rectangle([140, 220, 560, 256], fill="#111726", outline="#1E293B")
    draw.ellipse([156, 234, 164, 242], fill="#10B981")
    draw.text((176, 230), "NỀN TẢNG KHẢO THÍ TOÁN & TIN HỌC CHUYÊN SÂU", fill="#10B981")

    # Headline
    draw.text((140, 300), "Test đến đâu,", fill="#F9FAFB")
    draw.text((140, 380), "hiểu mình đến đó", fill="#10B981")

    # Subtext (matching image text exactly)
    draw.text(
        (140, 480),
        "Đo lường năng lực chuẩn xác với hệ thống 4 dạng thức thi mới, phân tích phổ điểm",
        fill="#94A3B8"
    )
    draw.text(
        (140, 510),
        "thời gian thực và sandbox chấm mã nguồn tự động.",
        fill="#94A3B8"
    )

    # ONLY 1 LOGIN BUTTON (Theo đúng chỉ đạo của người dùng)
    draw.rectangle([140, 570, 420, 630], fill="#10B981")
    draw.text((175, 592), "Đăng nhập hệ thống  ->", fill="#090D16")

    # 4. Right Stage: 3D Rubik's Cube Cluster (Red, Emerald, Black)
    cube_base_x = 1380
    cube_base_y = 520

    colors = [
        ("#10B981", "#EF4444", "#1E293B"),
        ("#EF4444", "#1E293B", "#10B981"),
        ("#1E293B", "#10B981", "#EF4444")
    ]

    # Draw main Rubik cube
    for layer in range(3):
        ly = cube_base_y - (layer * 85)
        for row in range(3):
            for col in range(3):
                cx = cube_base_x + (col - 1) * 80 - (row - 1) * 40
                cy = ly + (row - 1) * 40 + (col - 1) * 22
                c_top, c_left, c_right = colors[(layer + row + col) % 3]

                # Top rhombus
                draw.polygon([
                    (cx, cy - 35),
                    (cx + 45, cy - 12),
                    (cx, cy + 12),
                    (cx - 45, cy - 12)
                ], fill=c_top, outline="#090D16")

                # Left side
                draw.polygon([
                    (cx - 45, cy - 12),
                    (cx, cy + 12),
                    (cx, cy + 55),
                    (cx - 45, cy + 32)
                ], fill=c_left, outline="#090D16")

                # Right side
                draw.polygon([
                    (cx, cy + 12),
                    (cx + 45, cy - 12),
                    (cx + 45, cy + 32),
                    (cx, cy + 55)
                ], fill=c_right, outline="#090D16")

    # Draw satellite floating mini cubes (as shown in user image)
    # Satellite 1: Red mini cube (top left)
    s1_x, s1_y = 1180, 240
    draw.polygon([(s1_x, s1_y - 20), (s1_x + 25, s1_y - 8), (s1_x, s1_y + 8), (s1_x - 25, s1_y - 8)], fill="#EF4444", outline="#090D16")
    draw.polygon([(s1_x - 25, s1_y - 8), (s1_x, s1_y + 8), (s1_x, s1_y + 36), (s1_x - 25, s1_y + 20)], fill="#B91C1C", outline="#090D16")
    draw.polygon([(s1_x, s1_y + 8), (s1_x + 25, s1_y - 8), (s1_x + 25, s1_y + 20), (s1_x, s1_y + 36)], fill="#1E293B", outline="#090D16")

    # Satellite 2: Emerald mini cube (bottom left)
    s2_x, s2_y = 1210, 680
    draw.polygon([(s2_x, s2_y - 22), (s2_x + 28, s2_y - 9), (s2_x, s2_y + 9), (s2_x - 28, s2_y - 9)], fill="#10B981", outline="#090D16")
    draw.polygon([(s2_x - 28, s2_y - 9), (s2_x, s2_y + 9), (s2_x, s2_y + 40), (s2_x - 28, s2_y + 22)], fill="#047857", outline="#090D16")
    draw.polygon([(s2_x, s2_y + 9), (s2_x + 28, s2_y - 9), (s2_x + 28, s2_y + 22), (s2_x, s2_y + 40)], fill="#1E293B", outline="#090D16")

    # Satellite 3: Black mini cube (bottom right)
    s3_x, s3_y = 1560, 640
    draw.polygon([(s3_x, s3_y - 18), (s3_x + 22, s3_y - 7), (s3_x, s3_y + 7), (s3_x - 22, s3_y - 7)], fill="#1E293B", outline="#090D16")
    draw.polygon([(s3_x - 22, s3_y - 7), (s3_x, s3_y + 7), (s3_x, s3_y + 32), (s3_x - 22, s3_y + 18)], fill="#0F172A", outline="#090D16")
    draw.polygon([(s3_x, s3_y + 7), (s3_x + 22, s3_y - 7), (s3_x + 22, s3_y + 18), (s3_x, s3_y + 32)], fill="#020617", outline="#090D16")

    # 5. Centered single footer line
    draw.rectangle([0, height - 60, width, height], fill="#090D16", outline="#1E293B")
    draw.text((width // 2 - 180, height - 38), "Hệ thống nội bộ, vui lòng không chia sẻ ra bên ngoài", fill="#64748B")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT_PATH)
    print(f"Successfully generated minimal {OUTPUT_PATH}")

if __name__ == "__main__":
    create_landing_preview()
