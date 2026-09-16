"""
تولید عکس تبلیغاتی برای سرویس خواب سوین چوب
شماره تلفن، آیدی کانال و اینستاگرام روی عکس قرار می‌گیرد
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_promo_image(
    title: str = "سرویس خواب سوین چوب",
    subtitle: str = "کیفیت عالی | قیمت کارخانه‌ای",
    phone: str = "09926827083",
    channel: str = "@sevinchoob",
    instagram: str = "@sevin_home.ir",
    output_path: str = "promo.jpg"
) -> str:
    width, height = 1080, 1080
    img = Image.new("RGB", (width, height), color=(25, 35, 45))
    draw = ImageDraw.Draw(img)

    accent = (212, 175, 55)  # طلایی
    white = (255, 255, 255)
    light = (200, 200, 200)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # نوار طلایی بالا
    draw.rectangle([0, 0, width, 18], fill=accent)

    # عنوان
    draw.text((width // 2, 160), title, font=font_large, fill=white, anchor="mm")
    draw.text((width // 2, 250), subtitle, font=font_medium, fill=light, anchor="mm")

    # خط جداکننده
    draw.line([(120, 320), (width - 120, 320)], fill=accent, width=3)

    features = [
        "✓ تولید مستقیم از کارگاه",
        "✓ فروش عمده و خرده",
        "✓ طراحی مدرن و کلاسیک",
        "✓ ارسال به سراسر کشور",
    ]
    y = 390
    for feat in features:
        draw.text((width // 2, y), feat, font=font_medium, fill=white, anchor="mm")
        y += 65

    # باکس اطلاعات تماس
    draw.rectangle([60, 700, width - 60, 1000], fill=(40, 50, 60), outline=accent, width=3)

    draw.text((width // 2, 760), f"📞 {phone}", font=font_medium, fill=accent, anchor="mm")
    draw.text((width // 2, 840), f"📢 {channel}", font=font_medium, fill=white, anchor="mm")
    draw.text((width // 2, 920), f"📷 {instagram}", font=font_medium, fill=white, anchor="mm")

    # نوار طلایی پایین
    draw.rectangle([0, height - 18, width, height], fill=accent)

    img.save(output_path, quality=95)
    return output_path


if __name__ == "__main__":
    path = create_promo_image(output_path="test_promo.jpg")
    print(f"عکس تست ساخته شد: {path}")
