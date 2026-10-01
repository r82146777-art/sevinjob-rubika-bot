"""
ربات تبلیغاتی سوین چوب
ارسال روزانه صبح و شب: عکس مدل + متن تبلیغاتی غیرتکراری

  python bot.py --smart   → ارسال هوشمند زمان‌بندی‌شده
  python bot.py --once    → یک پست اجباری
"""

import sys
import time
import json
import requests
from datetime import datetime
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
    TIMEZONE,
    SEND_PRODUCT_IMAGE,
    END_DATE,
)
from contents import build_product_promo, get_random_promo

BASE_URL = f"https://botapi.rubika.ir/v3/{BOT_TOKEN}"
TZ = ZoneInfo(TIMEZONE)
LAST_SUCCESS_FILE = Path("last_success.txt")
PRODUCT_INDEX_FILE = Path("product_index.json")
CATALOG_FILE = Path("products/catalog.json")


def api_call(method: str, data: dict = None, retries: int = 3) -> dict:
    url = f"{BASE_URL}/{method}"
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, json=data or {}, timeout=45)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            print(f"[ERROR] {method} تلاش {attempt}/{retries}: {e}")
            if attempt < retries:
                time.sleep(5 * attempt)
    print(f"[ERROR] {method} نهایی ناموفق: {last_err}")
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
            print(f"[WARN] پاسخ آپلود: {result}")
            return None
    except Exception as e:
        print(f"[ERROR] آپلود: {e}")
        return None


def send_file(chat_id: str, file_id: str, text: str = None) -> dict:
    payload = {"chat_id": chat_id, "file_id": file_id}
    if text:
        payload["text"] = text
    return api_call("sendFile", payload)


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_catalog() -> list:
    data = load_json(CATALOG_FILE, [])
    return data if isinstance(data, list) else []


def next_product() -> dict | None:
    """چرخش روی مدل‌ها تا تکراری سریع نشود"""
    catalog = load_catalog()
    if not catalog:
        return None
    state = load_json(PRODUCT_INDEX_FILE, {"index": 0})
    idx = int(state.get("index", 0)) % len(catalog)
    product = catalog[idx]
    state["index"] = idx + 1
    save_json(PRODUCT_INDEX_FILE, state)
    return product


def mark_success(slot: str):
    now = datetime.now(TZ)
    data = {"slot": slot, "date": now.strftime("%Y-%m-%d"), "time": now.isoformat()}
    LAST_SUCCESS_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"[INFO] موفقیت ثبت شد: {data}")


def already_sent_today(slot: str) -> bool:
    if not LAST_SUCCESS_FILE.exists():
        return False
    try:
        raw = LAST_SUCCESS_FILE.read_text(encoding="utf-8").strip()
        data = json.loads(raw) if raw.startswith("{") else {}
        today = datetime.now(TZ).strftime("%Y-%m-%d")
        return data.get("date") == today and data.get("slot") == slot
    except Exception:
        return False


def current_slot() -> str | None:
    h = datetime.now(TZ).hour
    if 10 <= h <= 16:
        return "morning"
    if 19 <= h <= 23:
        return "evening"
    return None


def period_ended() -> bool:
    if not END_DATE:
        return False
    try:
        end = datetime.strptime(END_DATE, "%Y-%m-%d").date()
        return datetime.now(TZ).date() > end
    except Exception:
        return False


def is_ok(result: dict) -> bool:
    return isinstance(result, dict) and result.get("status") == "OK"


def send_product_post() -> bool:
    product = next_product()
    if product:
        text = build_product_promo(
            product=product,
            phone=PHONE_NUMBER,
            instagram=INSTAGRAM_URL,
            channel_link=CHANNEL_LINK,
        )
        image_path = product.get("image")
    else:
        text = get_random_promo(
            phone=PHONE_NUMBER,
            channel=CHANNEL_USERNAME,
            instagram=INSTAGRAM_URL,
            channel_link=CHANNEL_LINK,
        )
        image_path = None

    print(f"[INFO] متن آماده شد | مدل: {product.get('name') if product else 'عمومی'}")

    if SEND_PRODUCT_IMAGE and image_path and Path(image_path).exists():
        req = request_send_file("Image")
        upload_url = None
        if isinstance(req, dict):
            if "data" in req and isinstance(req["data"], dict):
                upload_url = req["data"].get("upload_url")
            upload_url = upload_url or req.get("upload_url")

        if upload_url:
            file_id = upload_file(upload_url, image_path)
            if file_id:
                result = send_file(CHANNEL_ID, file_id, text)
                print(f"[INFO] پست با عکس: {result}")
                return is_ok(result)
            print("[WARN] آپلود عکس ناموفق → فقط متن")
        else:
            print("[WARN] upload_url نبود → فقط متن")

    result = send_message(CHANNEL_ID, text)
    print(f"[INFO] پست متنی: {result}")
    return is_ok(result)


def smart_post():
    if period_ended():
        print(f"[SMART] دوره تا {END_DATE} تمام شده → توقف")
        return None

    slot = current_slot()
    now = datetime.now(TZ)
    print(f"[SMART] {now.strftime('%Y-%m-%d %H:%M')} | اسلات: {slot}")

    if not slot:
        print("[SMART] خارج از بازه صبح/شب → رد")
        return None

    if already_sent_today(slot):
        print(f"[SMART] پست {slot} امروز قبلاً رفته → رد")
        return None

    ok = send_product_post()
    if ok:
        mark_success(slot)
        print("[SMART] ارسال موفق")
        return True
    print("[SMART] ارسال ناموفق")
    return False


def main():
    smart = "--smart" in sys.argv
    once = "--once" in sys.argv

    print("=" * 55)
    print(f"ربات {BRAND_NAME} | {CHANNEL_USERNAME}")
    print("=" * 55)

    me = api_call("getMe")
    print(f"[INFO] ربات: {me}")

    if smart:
        ok = smart_post()
        if ok is False:
            sys.exit(1)
        return

    if once:
        ok = send_product_post()
        if ok:
            mark_success(current_slot() or "manual")
        else:
            sys.exit(1)
        return

    smart_post()


if __name__ == "__main__":
    main()
