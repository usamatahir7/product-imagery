"""One-time script to generate the placeholder template image."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "template_image.png"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    width, height = 1024, 768
    img = Image.new("RGB", (width, height), color=(30, 41, 59))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(40, 40), (width - 40, height - 40)], outline=(148, 163, 184), width=3)

    title = "Template Image"
    subtitle = "Replace with real image generation"
    try:
        font_title = ImageFont.truetype("arial.ttf", 48)
        font_sub = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=font_sub)

    title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
    title_y = height // 2 - 40
    subtitle_x = (width - (subtitle_bbox[2] - subtitle_bbox[0])) // 2
    subtitle_y = title_y + 60

    draw.text((title_x, title_y), title, fill=(226, 232, 240), font=font_title)
    draw.text((subtitle_x, subtitle_y), subtitle, fill=(148, 163, 184), font=font_sub)

    img.save(OUTPUT)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()
