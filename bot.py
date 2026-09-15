"""
ربات ارسال خودکار محتوای تبلیغاتی سرویس خواب سوینجوب به کانال روبیکا
"""

import time
import requests
import schedule
from pathlib import Path

from config import (
    BOT_TOKEN,
    CHANNEL_ID,
    CHANNEL_USERNAME,
    PHONE_NUMBER,
    POST_INTERVAL_HOURS,
    SEND_IMAGE,
)
from contents import get_random_promo
from image_generator import create_promo_image

BASE_URL = f"https://botapi.rubika.ir/v3/{BOT_TOKEN}"


def api_call(method: str, data: dict = None) -> dict:
    """ارسال درخواست به API روبیکا"""
    url = f"{BASE_URL}/{method}"
    try:
        resp = requests.post(url, json=data or {}, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] API call {method} failed: {e}")
        return {}


def send_message(chat_id: str, text: str) -> dict:
    """ارسال پیام متنی"""
    return api_call("sendMessage", {
        "chat_id": chat_id,
        "text": text,
    })


def request_send_file(file_type: str = "Image") -> dict:
    """درخواست URL آپلود فایل"""
    return api_call("requestSendFile", {"type": file_type})


def upload_file(upload_url: str, file_path: str) -> str | None:
    """آپلود فایل به سرور روبیکا و برگرداندن file_id"""
    try:
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f)}
            resp = requests.post(upload_url, files=files, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            # ساختار پاسخ ممکن است کمی متفاوت باشد
            if "data" in result and "file_id" in result["data"]:
                return result["data"]["file_id"]
            if "file_id" in result:
                return result["file_id"]
            print(f"[WARN] Unexpected upload response: {result}")
            return None
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        return None


def send_file(chat_id: str, file_id: str, text: str = None) -> dict:
    """ارسال فایل با file_id"""
    payload = {
        "chat_id": chat_id,
        "file_id": file_id,
    }
    if text:
        payload["text"] = text
    return api_call("sendFile", payload)


def send_promo_post():
    """ارسال یک پست تبلیغاتی کامل (متن + عکس)"""
    print("[INFO] در حال آماده‌سازی پست تبلیغاتی...")

    # متن تبلیغاتی
    text = get_random_promo(PHONE_NUMBER, CHANNEL_USERNAME)

    if not SEND_IMAGE:
        result = send_message(CHANNEL_ID, text)
        print(f"[INFO] پیام متنی ارسال شد: {result}")
        return

    # تولید عکس تبلیغاتی
    image_path = "temp_promo.jpg"
    try:
        create_promo_image(
            title="سرویس خواب سوینجوب",
            subtitle="تولید و فروش عمده و خرده",
            phone=PHONE_NUMBER,
            channel=CHANNEL_USERNAME,
            output_path=image_path,
        )
        print(f"[INFO] عکس تبلیغاتی ساخته شد: {image_path}")

        # درخواست آپلود
        req = request_send_file("Image")
        upload_url = None
        if "data" in req and "upload_url" in req["data"]:
            upload_url = req["data"]["upload_url"]
        elif "upload_url" in req:
            upload_url = req["upload_url"]

        if not upload_url:
            print("[WARN] نتوانست upload_url بگیرد. فقط متن ارسال می‌شود.")
            send_message(CHANNEL_ID, text)
            return

        file_id = upload_file(upload_url, image_path)
        if file_id:
            result = send_file(CHANNEL_ID, file_id, text)
            print(f"[INFO] پست با عکس ارسال شد: {result}")
        else:
            print("[WARN] آپلود عکس ناموفق. فقط متن ارسال می‌شود.")
            send_message(CHANNEL_ID, text)

    except Exception as e:
        print(f"[ERROR] خطا در ارسال پست: {e}")
        # fallback به متن ساده
        send_message(CHANNEL_ID, text)
    finally:
        # پاک کردن فایل موقت
        if Path(image_path).exists():
            Path(image_path).unlink(missing_ok=True)


def main():
    print("=" * 50)
    print("ربات تبلیغاتی سوینجوب راه‌اندازی شد")
    print(f"کانال: {CHANNEL_USERNAME} | فاصله ارسال: هر {POST_INTERVAL_HOURS} ساعت")
    print("=" * 50)

    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHANNEL_ID == "YOUR_CHANNEL_ID_HERE":
        print("[ERROR] لطفاً ابتدا فایل config.py را با اطلاعات واقعی پر کنید!")
        return

    # تست اتصال
    me = api_call("getMe")
    print(f"[INFO] اطلاعات ربات: {me}")

    # ارسال اولین پست فوری
    send_promo_post()

    # زمان‌بندی ارسال‌های بعدی
    schedule.every(POST_INTERVAL_HOURS).hours.do(send_promo_post)

    print("[INFO] ربات در حال اجراست. برای توقف Ctrl+C بزنید.")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
