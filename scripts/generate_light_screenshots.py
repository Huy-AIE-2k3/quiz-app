#!/usr/bin/env python3
"""Generate high-fidelity Light Mode PNG previews for all screens.

Preserves hue and saturation while transforming value (brightness) into light mode palette.
"""

from pathlib import Path
from PIL import Image, ImageOps
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

def main():
    screens_dir = Path("design/screens")
    generated = 0

    print("Generating Light Mode PNG screenshots...")
    for base_name in BASE_SCREENS:
        dark_png = screens_dir / f"{base_name}.png"
        light_png = screens_dir / f"{base_name}-light.png"

        if not dark_png.exists():
            print(f"Warning: {dark_png} not found, skipping.")
            continue

        try:
            img = Image.open(dark_png).convert("RGB")
            h, s, v = img.convert("HSV").split()

            # Transform V: Dark background (low V) -> Light background (high V)
            # Dark text (high V) -> Dark text (low V)
            # Reduce contrast slightly on extreme edges for soft academic aesthetics
            v_transformed = v.point(lambda p: int(248 - p * 0.88))
            
            # Slightly adjust saturation for light mode clarity
            s_adjusted = s.point(lambda p: min(255, int(p * 1.05)))

            light_hsv = Image.merge("HSV", (h, s_adjusted, v_transformed))
            light_rgb = light_hsv.convert("RGB")
            light_rgb.save(light_png, optimize=True)
            print(f"  -> Generated {light_png.name}")
            generated += 1
        except Exception as e:
            print(f"Error processing {base_name}: {e}")

    print(f"\nSuccessfully generated {generated} Light Mode PNGs!")
    return 0

if __name__ == "__main__":
    sys.exit(main())

