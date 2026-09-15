"""
تولید عکس تبلیغاتی ساده برای سرویس خواب سوینجوب
با استفاده از Pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

def create_promo_image(
    title: str = "سرویس خواب سوینجوب",
    subtitle: str = "کیفیت عالی | قیمت کارخانه‌ای",
    phone: str = "0912XXXXXXX",
    channel: str = "@sevinjob",
    output_path: str = "promo.jpg"
) -> str:
    """
    یک عکس تبلیغاتی ساده با پس‌زمینه تیره و متن سفید می‌سازد.
    شماره تلفن و آیدی کانال حتماً روی عکس قرار می‌گیرد.
    """
    width, height = 1080, 1080
    img = Image.new("RGB", (width, height), color=(25, 35, 45))
    draw = ImageDraw.Draw(img)

    # رنگ‌های برند (می‌توانید تغییر دهید)
    accent = (212, 175, 55)  # طلایی
    white = (255, 255, 255)
    light = (200, 200, 200)

    # فونت‌ها (اگر فونت فارسی سیستم ندارید، از پیش‌فرض استفاده می‌شود)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except Exception:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # نوار طلایی بالا
    draw.rectangle([0, 0, width, 20], fill=accent)

    # عنوان اصلی
    draw.text((width // 2, 180), title, font=font_large, fill=white, anchor="mm")

    # زیرعنوان
    draw.text((width // 2, 280), subtitle, font=font_medium, fill=light, anchor="mm")

    # خط جداکننده
    draw.line([(150, 360), (width - 150, 360)], fill=accent, width=3)

    # متن‌های ویژگی
    features = [
        "✓ تولید مستقیم از کارگاه",
        "✓ فروش عمده و خرده",
        "✓ طراحی مدرن و کلاسیک",
        "✓ ارسال به سراسر کشور",
    ]
    y = 430
    for feat in features:
        draw.text((width // 2, y), feat, font=font_medium, fill=white, anchor="mm")
        y += 70

    # باکس پایین برای شماره و کانال
    draw.rectangle([80, 780, width - 80, 980], fill=(40, 50, 60), outline=accent, width=3)

    draw.text((width // 2, 840), f"📞 {phone}", font=font_medium, fill=accent, anchor="mm")
    draw.text((width // 2, 920), f"📢 {channel}", font=font_medium, fill=white, anchor="mm")

    # نوار طلایی پایین
    draw.rectangle([0, height - 20, width, height], fill=accent)

    img.save(output_path, quality=95)
    return output_path


if __name__ == "__main__":
    # تست تولید عکس
    path = create_promo_image(
        phone="09121234567",
        channel="@sevinjob",
        output_path="test_promo.jpg"
    )
    print(f"عکس تست ساخته شد: {path}")
