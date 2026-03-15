"""
Generate placeholder cover images for Pick-TW articles.
1200x630 banners with category color, icon, and title text.
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = "static/images/posts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# (filename, bg_color, icon, title_zh)
IMAGES = [
    ("air-purifier-2026.jpg",   "#1a7a4a", "🌿", "空氣清淨機推薦"),
    ("credit-card-2026.jpg",    "#1a3a7a", "💳", "信用卡推薦"),
    ("laptop-2026.jpg",         "#2a1a7a", "💻", "筆電推薦"),
    ("robot-vacuum-2026.jpg",   "#7a1a1a", "🤖", "掃地機器人推薦"),
    ("etf-guide-2026.jpg",      "#7a5a1a", "📈", "ETF 投資指南"),
    ("keyboard-2026.jpg",       "#1a5a7a", "⌨️", "機械鍵盤推薦"),
]

W, H = 1200, 630

def make_banner(filename, bg_hex, icon, title):
    img = Image.new("RGB", (W, H), bg_hex)
    draw = ImageDraw.Draw(img)

    # Slightly lighter overlay strip
    overlay_color = tuple(min(255, c + 30) for c in img.getpixel((0, 0)))
    draw.rectangle([0, H - 120, W, H], fill=overlay_color)

    # Brand text bottom-left
    try:
        font_sm = ImageFont.truetype("C:/Windows/Fonts/msjh.ttc", 28)
        font_lg = ImageFont.truetype("C:/Windows/Fonts/msjhbd.ttc", 80)
        font_icon = ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", 140)
    except Exception:
        font_sm = ImageFont.load_default()
        font_lg = font_sm
        font_icon = font_sm

    # Icon center
    draw.text((W // 2, H // 2 - 80), icon, font=font_icon, anchor="mm", embedded_color=True)

    # Title
    draw.text((W // 2, H - 65), f"Pick-TW | {title}", font=font_sm, anchor="mm", fill="#ffffff")

    # Year badge top-right
    draw.rectangle([W - 160, 20, W - 20, 65], fill="#ffffff30")
    draw.text((W - 90, 42), "2026 精選", font=font_sm, anchor="mm", fill="#ffffff")

    path = os.path.join(OUTPUT_DIR, filename)
    img.save(path, "JPEG", quality=90)
    print("OK: " + path)

for args in IMAGES:
    try:
        make_banner(*args)
    except Exception as e:
        print("ERR: " + args[0] + " " + str(e))

print("\nDone!")
