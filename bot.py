"""
ربات ارسال خودکار محتوای تبلیغاتی سرویس خواب سوین چوب به کانال روبیکا
زمان‌بندی: هر روز ساعت ۱۱:۰۰ صبح و ۲۰:۰۰ شب (به وقت ایران)
"""

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
    INSTAGRAM_HANDLE,
    INSTAGRAM_URL,
    BRAND_NAME,
    SEND_IMAGE,
    TIMEZONE,
)
from contents import get_random_promo
from image_generator import create_promo_image

BASE_URL = f"https://botapi.rubika.ir/v3/{BOT_TOKEN}"
TZ = ZoneInfo(TIMEZONE)

# ساعات ارسال روزانه (ساعت محلی ایران)
POST_TIMES = [11, 20]  # ۱۱ صبح و ۸ شب


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


def send_promo_post():
    print(f"[{datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}] در حال آماده‌سازی پست تبلیغاتی...")

    text = get_random_promo(
        phone=PHONE_NUMBER,
        channel=CHANNEL_USERNAME,
        instagram=INSTAGRAM_HANDLE,
        channel_link=CHANNEL_LINK,
    )

    if not SEND_IMAGE:
        result = send_message(CHANNEL_ID, text)
        print(f"[INFO] متن ارسال شد: {result}")
        return

    image_path = "temp_promo.jpg"
    try:
        create_promo_image(
            title=f"سرویس خواب {BRAND_NAME}",
            subtitle="تولید و فروش عمده و خرده",
            phone=PHONE_NUMBER,
            channel=CHANNEL_USERNAME,
            instagram=INSTAGRAM_HANDLE,
            output_path=image_path,
        )

        req = request_send_file("Image")
        upload_url = None
        if isinstance(req, dict):
            if "data" in req and isinstance(req["data"], dict):
                upload_url = req["data"].get("upload_url")
            upload_url = upload_url or req.get("upload_url")

        if not upload_url:
            print("[WARN] upload_url دریافت نشد → فقط متن ارسال می‌شود")
            send_message(CHANNEL_ID, text)
            return

        file_id = upload_file(upload_url, image_path)
        if file_id:
            result = send_file(CHANNEL_ID, file_id, text)
            print(f"[INFO] پست با عکس ارسال شد: {result}")
        else:
            print("[WARN] آپلود عکس ناموفق → فقط متن")
            send_message(CHANNEL_ID, text)

    except Exception as e:
        print(f"[ERROR] خطا در پست: {e}")
        send_message(CHANNEL_ID, text)
    finally:
        p = Path(image_path)
        if p.exists():
            p.unlink(missing_ok=True)


def seconds_until_next_post() -> float:
    """محاسبه ثانیه تا نزدیک‌ترین ساعت ارسال بعدی (۱۱ یا ۲۰)"""
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
    print("=" * 55)
    print(f"ربات تبلیغاتی {BRAND_NAME} راه‌اندازی شد")
    print(f"کانال: {CHANNEL_USERNAME}")
    print(f"زمان‌بندی: هر روز ساعت ۱۱:۰۰ و ۲۰:۰۰ (وقت ایران)")
    print("=" * 55)

    me = api_call("getMe")
    print(f"[INFO] ربات: {me}")

    # ارسال یک پست فوری برای تست (اختیاری - می‌توانید کامنت کنید)
    # send_promo_post()

    while True:
        wait = seconds_until_next_post()
        time.sleep(wait)
        try:
            send_promo_post()
        except Exception as e:
            print(f"[ERROR] خطای غیرمنتظره در ارسال: {e}")
            time.sleep(60)  # کمی صبر و ادامه


if __name__ == "__main__":
    main()
