"""
ربات ارسال خودکار محتوای تبلیغاتی سرویس خواب سوین چوب به کانال روبیکا

حالت‌ها:
  python bot.py --once       → ارسال عادی یک پست
  python bot.py --heartbeat  → قلب تپنده: فقط اگر پست اخیر ارسال نشده باشد، ارسال می‌کند
  python bot.py              → حلقه مداوم (اجرای محلی)
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
POST_TIMES = [11, 20]
LAST_SUCCESS_FILE = Path("last_success.txt")
# اگر در ۴۵ دقیقه اخیر پست موفق داشته باشیم، قلب تپنده چیزی نمی‌فرستد
HEARTBEAT_WINDOW_MINUTES = 45


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
    """ثبت زمان موفقیت ارسال"""
    now = datetime.now(TZ).isoformat()
    LAST_SUCCESS_FILE.write_text(now, encoding="utf-8")
    print(f"[INFO] زمان موفقیت ثبت شد: {now}")


def was_recently_successful() -> bool:
    """آیا در پنجره زمانی اخیر پست موفق داشته‌ایم؟"""
    if not LAST_SUCCESS_FILE.exists():
        print("[HEARTBEAT] فایل last_success وجود ندارد → نیاز به ارسال")
        return False
    try:
        raw = LAST_SUCCESS_FILE.read_text(encoding="utf-8").strip()
        last = datetime.fromisoformat(raw)
        if last.tzinfo is None:
            last = last.replace(tzinfo=TZ)
        now = datetime.now(TZ)
        delta = (now - last).total_seconds() / 60
        print(f"[HEARTBEAT] آخرین موفقیت: {last.strftime('%Y-%m-%d %H:%M')} ({delta:.0f} دقیقه پیش)")
        if delta <= HEARTBEAT_WINDOW_MINUTES:
            print("[HEARTBEAT] پست اخیر موفق بوده → نیازی به ارسال مجدد نیست")
            return True
        print("[HEARTBEAT] پست اخیر قدیمی است → ارسال انجام می‌شود")
        return False
    except Exception as e:
        print(f"[HEARTBEAT] خطا در خواندن وضعیت: {e} → ارسال انجام می‌شود")
        return False


def send_promo_post() -> bool:
    """ارسال پست. در صورت موفقیت True برمی‌گرداند."""
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
        success = bool(result)
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
                success = bool(result)
            else:
                file_id = upload_file(upload_url, image_path)
                if file_id:
                    result = send_file(CHANNEL_ID, file_id, text)
                    print(f"[INFO] پست با عکس ارسال شد: {result}")
                    success = bool(result)
                else:
                    print("[WARN] آپلود عکس ناموفق → فقط متن")
                    result = send_message(CHANNEL_ID, text)
                    success = bool(result)

        except Exception as e:
            print(f"[ERROR] خطا در پست: {e}")
            result = send_message(CHANNEL_ID, text)
            success = bool(result)
        finally:
            p = Path(image_path)
            if p.exists():
                p.unlink(missing_ok=True)

    if success:
        mark_success()
    return success


def seconds_until_next_post() -> float:
    now = datetime.now(TZ)
    candidates = []
    for hour in POST_TIMES:
        candidate = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        candidates.append(candidate)
    next_time = min(candidates)
    delta = (next_time - now).total_seconds()
    print(f"[INFO] پست بعدی در {next_time.strftime('%Y-%m-%d %H:%M')} (حدود {delta/3600:.1f} ساعت دیگر)")
    return max(delta, 5)


def main():
    once = "--once" in sys.argv
    heartbeat = "--heartbeat" in sys.argv

    print("=" * 55)
    print(f"ربات تبلیغاتی {BRAND_NAME}")
    print(f"کانال: {CHANNEL_USERNAME}")
    if heartbeat:
        print("حالت: قلب تپنده (بررسی و ارسال در صورت نیاز)")
    elif once:
        print("حالت: ارسال یک‌بار (اصلی)")
    else:
        print("حالت: حلقه مداوم | ۱۱:۰۰ و ۲۰:۰۰")
    print("=" * 55)

    me = api_call("getMe")
    print(f"[INFO] ربات: {me}")

    if heartbeat:
        if was_recently_successful():
            print("[HEARTBEAT] همه چیز درست است. خروج.")
            return
        print("[HEARTBEAT] پست اخیر یافت نشد → در حال ارسال...")
        send_promo_post()
        return

    if once:
        send_promo_post()
        print("[INFO] ارسال یک پست تمام شد.")
        return

    while True:
        wait = seconds_until_next_post()
        time.sleep(wait)
        try:
            send_promo_post()
        except Exception as e:
            print(f"[ERROR] خطای غیرمنتظره: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
