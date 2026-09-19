"""
ربات ارسال خودکار محتوای تبلیغاتی سرویس خواب سوین چوب به کانال روبیکا

حالت‌ها:
  python bot.py --smart   → ارسال هوشمند (فقط اگر در بازه زمانی مجاز باشد و پست اخیر نرفته باشد)
  python bot.py --once    → اجبار به ارسال یک پست (تست دستی)
  python bot.py           → حلقه مداوم محلی
"""

import sys
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from config import (
    BOT_TOKEN,
    CHANNEL_ID,
    CHANNEL_USERNAME,
    CHANNEL_LINK,
    PHONE_NUMBER,
    INSTAGRAM_URL,
    BRAND_NAME,
    SEND_IMAGE,
    TIMEZONE,
)
from contents import get_random_promo
from image_generator import create_promo_image

BASE_URL = f"https://botapi.rubika.ir/v3/{BOT_TOKEN}"
TZ = ZoneInfo(TIMEZONE)
LAST_SUCCESS_FILE = Path("last_success.txt")

# اگر در این مدت (دقیقه) پست موفق داشته باشیم، دوباره نمی‌فرستیم
COOLDOWN_MINUTES = 90

# بازه‌های مجاز ارسال به وقت ایران (ساعت، دقیقه شروع) تا (ساعت، دقیقه پایان)
# صبح: ۱۰:۴۵ تا ۱۱:۴۵ | شب: ۱۹:۴۵ تا ۲۰:۴۵
ALLOWED_WINDOWS = [
    ((10, 45), (11, 45)),
    ((19, 45), (20, 45)),
]


def api_call(method: str, data: dict = None) -> dict:
    url = f"{BASE_URL}/{method}"
    try:
        resp = requests.post(url, json=data or {}, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] {method}: {e}")
        return {}


def send_message(chat_id: str, text: str) -> dict:
    return api_call("sendMessage", {"chat_id": chat_id, "text": text})


def request_send_file(file_type: str = "Image") -> dict:
    return api_call("requestSendFile", {"type": file_type})


def upload_file(upload_url: str, file_path: str) -> str | None:
    try:
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f)}
            resp = requests.post(upload_url, files=files, timeout=90)
            resp.raise_for_status()
            result = resp.json()
            if isinstance(result, dict):
                if "data" in result and isinstance(result["data"], dict) and "file_id" in result["data"]:
                    return result["data"]["file_id"]
                if "file_id" in result:
                    return result["file_id"]
            print(f"[WARN] پاسخ آپلود غیرمنتظره: {result}")
            return None
    except Exception as e:
        print(f"[ERROR] آپلود: {e}")
        return None


def send_file(chat_id: str, file_id: str, text: str = None) -> dict:
    payload = {"chat_id": chat_id, "file_id": file_id}
    if text:
        payload["text"] = text
    return api_call("sendFile", payload)


def mark_success():
    now = datetime.now(TZ).isoformat()
    LAST_SUCCESS_FILE.write_text(now, encoding="utf-8")
    print(f"[INFO] زمان موفقیت ثبت شد: {now}")


def minutes_since_last_success() -> float | None:
    if not LAST_SUCCESS_FILE.exists():
        return None
    try:
        raw = LAST_SUCCESS_FILE.read_text(encoding="utf-8").strip()
        last = datetime.fromisoformat(raw)
        if last.tzinfo is None:
            last = last.replace(tzinfo=TZ)
        return (datetime.now(TZ) - last).total_seconds() / 60
    except Exception as e:
        print(f"[WARN] خواندن last_success: {e}")
        return None


def in_allowed_window(now: datetime | None = None) -> bool:
    now = now or datetime.now(TZ)
    minutes = now.hour * 60 + now.minute
    for (sh, sm), (eh, em) in ALLOWED_WINDOWS:
        start = sh * 60 + sm
        end = eh * 60 + em
        if start <= minutes <= end:
            return True
    return False


def should_send_smart() -> bool:
    """آیا الان باید پست بفرستیم؟"""
    now = datetime.now(TZ)
    print(f"[SMART] ساعت ایران الان: {now.strftime('%Y-%m-%d %H:%M')}")

    if not in_allowed_window(now):
        print("[SMART] خارج از بازه مجاز ارسال → رد")
        return False

    delta = minutes_since_last_success()
    if delta is not None and delta < COOLDOWN_MINUTES:
        print(f"[SMART] پست اخیر {delta:.0f} دقیقه پیش موفق بوده → نیازی به ارسال مجدد نیست")
        return False

    print("[SMART] شرایط برقرار است → ارسال انجام می‌شود")
    return True


def send_promo_post() -> bool:
    now_str = datetime.now(TZ).strftime('%Y-%m-%d %H:%M')
    print(f"[{now_str}] در حال آماده‌سازی پست تبلیغاتی سوین چوب...")

    text = get_random_promo(
        phone=PHONE_NUMBER,
        channel=CHANNEL_USERNAME,
        instagram=INSTAGRAM_URL,
        channel_link=CHANNEL_LINK,
    )

    success = False

    if not SEND_IMAGE:
        result = send_message(CHANNEL_ID, text)
        print(f"[INFO] متن ارسال شد: {result}")
        success = isinstance(result, dict) and result.get("status") == "OK"
    else:
        image_path = "temp_promo.jpg"
        try:
            create_promo_image(
                title=f"سرویس خواب {BRAND_NAME}",
                subtitle="تولید و فروش عمده و خرده",
                phone=PHONE_NUMBER,
                channel=CHANNEL_USERNAME,
                instagram="sevin_home.ir",
                output_path=image_path,
            )

            req = request_send_file("Image")
            upload_url = None
            if isinstance(req, dict):
                if "data" in req and isinstance(req["data"], dict):
                    upload_url = req["data"].get("upload_url")
                upload_url = upload_url or req.get("upload_url")

            if not upload_url:
                print("[WARN] upload_url دریافت نشد → فقط متن")
                result = send_message(CHANNEL_ID, text)
                success = isinstance(result, dict) and result.get("status") == "OK"
            else:
                file_id = upload_file(upload_url, image_path)
                if file_id:
                    result = send_file(CHANNEL_ID, file_id, text)
                    print(f"[INFO] پست با عکس ارسال شد: {result}")
                    success = isinstance(result, dict) and result.get("status") == "OK"
                else:
                    print("[WARN] آپلود عکس ناموفق → فقط متن")
                    result = send_message(CHANNEL_ID, text)
                    success = isinstance(result, dict) and result.get("status") == "OK"

        except Exception as e:
            print(f"[ERROR] خطا در پست: {e}")
            result = send_message(CHANNEL_ID, text)
            success = isinstance(result, dict) and result.get("status") == "OK"
        finally:
            p = Path(image_path)
            if p.exists():
                p.unlink(missing_ok=True)

    if success:
        mark_success()
    else:
        print("[WARN] ارسال ناموفق بود، last_success به‌روز نشد")
    return success


def main():
    smart = "--smart" in sys.argv
    once = "--once" in sys.argv

    print("=" * 55)
    print(f"ربات تبلیغاتی {BRAND_NAME}")
    print(f"کانال: {CHANNEL_USERNAME}")
    if smart:
        print("حالت: هوشمند (بازه زمانی + جلوگیری از تکرار)")
    elif once:
        print("حالت: ارسال اجباری یک‌بار")
    else:
        print("حالت: حلقه مداوم محلی")
    print("=" * 55)

    me = api_call("getMe")
    print(f"[INFO] ربات: {me}")

    if smart:
        if should_send_smart():
            send_promo_post()
        else:
            print("[SMART] این اجرا رد شد.")
        return

    if once:
        send_promo_post()
        return

    # حالت محلی
    while True:
        now = datetime.now(TZ)
        if in_allowed_window(now) and should_send_smart():
            send_promo_post()
            time.sleep(600)
        else:
            time.sleep(60)


if __name__ == "__main__":
    main()
