"""
تولید عکس تبلیغاتی طبیعی و حرفه‌ای برای سرویس خواب سوین چوب
طراحی تمیز، بدون ظاهر هوش‌مصنوعی، شبیه کار گرافیست انسانی
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import random

def create_promo_image(
    title: str = "سرویس خواب سوین چوب",
    subtitle: str = "تولید و فروش عمده و خرده",
    phone: str = "09926827083",
    channel: str = "@sevinchoob",
    instagram: str = "sevin_home.ir",
    output_path: str = "promo.jpg"
) -> str:
    width, height = 1080, 1080

    # پس‌زمینه گرم و طبیعی (قهوه‌ای تیره مایل به چوب)
    bg_color = (42, 32, 28)
    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # رنگ‌های طبیعی و حرفه‌ای
    cream = (245, 235, 220)
    soft_gold = (196, 164, 110)
    light_cream = (230, 220, 205)
    dark_wood = (55, 42, 36)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_contact = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_contact = ImageFont.load_default()

    # نوار نازک طلایی بالا (ظریف)
    draw.rectangle([0, 0, width, 8], fill=soft_gold)

    # عنوان اصلی
    draw.text((width // 2, 150), title, font=font_title, fill=cream, anchor="mm")

    # زیرعنوان
    draw.text((width // 2, 230), subtitle, font=font_sub, fill=light_cream, anchor="mm")

    # خط ظریف جداکننده
    draw.line([(180, 290), (width - 180, 290)], fill=soft_gold, width=2)

    # ویژگی‌ها با ظاهر تمیز
    features = [
        "تولید مستقیم از کارگاه",
        "فروش عمده و خرده",
        "طراحی مدرن و کلاسیک",
        "ارسال به سراسر کشور",
    ]
    y = 360
    for feat in features:
        # نقطه کوچک طلایی به جای تیک شلوغ
        draw.ellipse([width//2 - 220, y - 8, width//2 - 204, y + 8], fill=soft_gold)
        draw.text((width // 2 - 180, y), feat, font=font_body, fill=cream, anchor="lm")
        y += 70

    # باکس اطلاعات تماس (تمیز و مینیمال)
    box_top = 680
    box_bottom = 980
    draw.rounded_rectangle(
        [70, box_top, width - 70, box_bottom],
        radius=18,
        fill=dark_wood,
        outline=soft_gold,
        width=2
    )

    draw.text((width // 2, box_top + 70), f"📞  {phone}", font=font_contact, fill=soft_gold, anchor="mm")
    draw.text((width // 2, box_top + 150), f"📢  {channel}", font=font_contact, fill=cream, anchor="mm")
    draw.text((width // 2, box_top + 230), f"📷  {instagram}", font=font_contact, fill=cream, anchor="mm")

    # نوار نازک پایین
    draw.rectangle([0, height - 8, width, height], fill=soft_gold)

    # کمی نویز بسیار ملایم برای ظاهر طبیعی‌تر (اختیاری و خیلی کم)
    # این کار عکس را از ظاهر کاملاً دیجیتال خارج می‌کند
    noise = Image.effect_noise((width, height), 8).convert("L")
    noise = noise.point(lambda x: 128 + (x - 128) // 12)
    img = Image.blend(img, Image.merge("RGB", [noise, noise, noise]), 0.04)

    img.save(output_path, quality=92, optimize=True)
    return output_path


if __name__ == "__main__":
    path = create_promo_image(output_path="test_promo.jpg")
    print(f"عکس تست ساخته شد: {path}")
