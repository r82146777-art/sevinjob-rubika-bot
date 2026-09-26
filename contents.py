# ============================================
# متن‌های تبلیغاتی پویا و غیرتکراری سوین چوب
# ادغام با مشخصات مدل محصول
# ============================================

import random
from datetime import datetime
from zoneinfo import ZoneInfo

OPENINGS = [
    "🛏️ طراحی و خلاقیت هنر ماست",
    "✨ زیبایی اتاق خواب با سوین چوب",
    "🔥 سرویس خوابی که حال خانه را عوض می‌کند",
    "💤 آرامش واقعی از خواب شروع می‌شود",
    "🏭 تولید مستقیم از کارگاه سوین چوب",
    "🌟 کیفیت کارخانه‌ای، ظاهر لوکس",
    "💎 انتخاب خاص برای خانه‌های خاص",
    "🌙 اتاق خواب رویایی در دسترس شماست",
    "🪵 چوب مرغوب + طراحی دقیق",
    "🏠 جهیزیه و نوسازی با خیال راحت",
    "📦 عمده و خرده؛ مستقیم از تولیدکننده",
    "🎁 فرصتی برای خرید هوشمندانه",
    "😴 خواب عمیق با سرویس استاندارد",
    "🚚 از کارگاه تا درب منزل شما",
    "💪 زیبا بخرید، سال‌ها استفاده کنید",
]

BODIES_GENERIC = [
    "هر قطعه با دقت ساخته می‌شود تا هم زیبا باشد و هم بادوام.\nفروش عمده و خرده در سراسر کشور.",
    "بدون واسطه بخرید؛ قیمت کارخانه‌ای و کیفیت تضمینی.\nمناسب جهیزیه، آپارتمان، هتل و فروشگاه‌ها.",
    "طراحی مدرن و کلاسیک، متریال مرغوب، ارسال به تمام ایران.\nیک تماس برای مشاوره رایگان کافی است.",
    "سوین چوب یعنی انتخاب هوشمند برای کسانی که کیفیت می‌خواهند.\nپشتیبانی واقعی بعد از خرید.",
]

CLOSINGS = [
    "فرصت را از دست ندهید؛ کیفیت همیشه ارزشش را دارد.",
    "با یک تماس، مشاوره و لیست قیمت دریافت کنید.",
    "ما آماده‌ایم بهترین مدل را به شما پیشنهاد دهیم.",
    "همین امروز اقدام کنید و تفاوت را ببینید.",
    "سوین چوب؛ همراه مطمئن خواب راحت شما.",
]


def build_product_promo(
    product: dict,
    phone: str,
    instagram: str,
    channel_link: str,
) -> str:
    """ساخت متن تبلیغاتی یکتا برای یک مدل محصول"""
    name = product.get("name", "")
    tagline = product.get("tagline", "طراحی و خلاقیت هنر ماست")
    parts = product.get("parts", "")

    opening = random.choice(OPENINGS)
    # گاهی از تگ‌لاین خود محصول استفاده کن
    if random.random() < 0.45:
        opening = f"✨ {tagline}"

    body_extra = random.choice(BODIES_GENERIC)
    closing = random.choice(CLOSINGS)

    parts_line = f"اجزاء شامل: {parts}" if parts else ""

    text = f"""{opening}

🛏️ سرویس خواب مدل {name}

{parts_line}

{body_extra}

{closing}

📞 تماس: {phone}
📷 اینستاگرام: {instagram}
🔗 کانال: {channel_link}"""
    return text


def get_random_promo(phone: str, channel: str, instagram: str, channel_link: str) -> str:
    """متن عمومی وقتی محصولی در دسترس نیست"""
    opening = random.choice(OPENINGS)
    body = random.choice(BODIES_GENERIC)
    closing = random.choice(CLOSINGS)
    return f"""{opening}

{body}

{closing}

📞 تماس: {phone}
📷 اینستاگرام: {instagram}
🔗 کانال: {channel_link}"""


def get_caption_for_photo(phone: str, instagram: str, channel_link: str) -> str:
    return f"""🛏️ سرویس خواب سوین چوب
کیفیت کارخانه‌ای | فروش عمده و خرده

📞 {phone}
📷 {instagram}
🔗 {channel_link}"""
