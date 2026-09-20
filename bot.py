"""
ربات تبلیغاتی سوین چوب

حالت‌ها:
  python bot.py --smart     → ارسال زمان‌بندی‌شده هوشمند (فقط متن)
  python bot.py --once      → یک پست متنی اجباری
  python bot.py --listen    → گوش دادن به پیام‌ها (افزودن عکس و دستورات)
  python bot.py             → حلقه محلی ساده
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
    ADMIN_IDS,
)
from contents import get_random_promo, get_caption_for_photo

BASE_URL = f"https://botapi.rubika.ir/v3/{BOT_TOKEN}"
TZ = ZoneInfo(TIMEZONE)
LAST_SUCCESS_FILE = Path("last_success.txt")
PHOTO_QUEUE_FILE = Path("photo_queue.json")
STATE_FILE = Path("user_states.json")

# اسلات‌های روزانه (بازه‌های وسیع برای تحمل تأخیر GitHub Actions)
# morning: یک پست در روز بین ساعت ۱۰ تا ۱۶ ایران
# evening: یک پست در روز بین ساعت ۱۹ تا ۲۳:۵۹ ایران


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


def send_file(chat_id: str, file_id: str, text: str = None) -> dict:
    payload = {"chat_id": chat_id, "file_id": file_id}
    if text:
        payload["text"] = text
    return api_call("sendFile", payload)


def get_updates(offset_id: str = None, limit: int = 50) -> dict:
    data = {"limit": limit}
    if offset_id:
        data["offset_id"] = offset_id
    return api_call("getUpdates", data)


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default
    return default


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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
        data = json.loads(raw) if raw.startswith("{") else {"date": "", "slot": ""}
        today = datetime.now(TZ).strftime("%Y-%m-%d")
        return data.get("date") == today and data.get("slot") == slot
    except Exception:
        return False


def current_slot() -> str | None:
    """تشخیص اسلات صبح/شب بر اساس ساعت ایران"""
    h = datetime.now(TZ).hour
    if 10 <= h <= 16:
        return "morning"
    if 19 <= h <= 23:
        return "evening"
    return None


def send_text_promo() -> bool:
    text = get_random_promo(
        phone=PHONE_NUMBER,
        channel=CHANNEL_USERNAME,
        instagram=INSTAGRAM_URL,
        channel_link=CHANNEL_LINK,
    )
    print(f"[INFO] ارسال متن تبلیغاتی...")
    result = send_message(CHANNEL_ID, text)
    print(f"[INFO] نتیجه: {result}")
    ok = isinstance(result, dict) and result.get("status") == "OK"
    return ok


def smart_post():
    slot = current_slot()
    now = datetime.now(TZ)
    print(f"[SMART] ساعت ایران: {now.strftime('%Y-%m-%d %H:%M')} | اسلات: {slot}")

    if not slot:
        print("[SMART] خارج از بازه صبح/شب → رد")
        return

    if already_sent_today(slot):
        print(f"[SMART] پست {slot} امروز قبلاً ارسال شده → رد")
        return

    ok = send_text_promo()
    if ok:
        mark_success(slot)
        print("[SMART] ارسال موفق")
    else:
        print("[SMART] ارسال ناموفق")


# ========== قابلیت افزودن عکس ==========

def is_admin(user_id: str) -> bool:
    if not ADMIN_IDS:
        return True
    return user_id in ADMIN_IDS


def handle_text_command(chat_id: str, user_id: str, text: str):
    text = (text or "").strip()
    states = load_json(STATE_FILE, {})
    queue = load_json(PHOTO_QUEUE_FILE, {"photos": []})

    if text in ("افزودن عکس", "/addphoto", "addphoto", "عکس"):
        if not is_admin(user_id):
            send_message(chat_id, "⛔ شما مجاز به این کار نیستید.")
            return
        states[user_id] = "waiting_photos"
        save_json(STATE_FILE, states)
        queue["photos"] = []
        save_json(PHOTO_QUEUE_FILE, queue)
        send_message(
            chat_id,
            "📸 لطفاً عکس‌ها را ارسال فرمایید.\n\n"
            "می‌توانید چند عکس پشت‌سرهم بفرستید.\n"
            "وقتی تمام شد، بنویسید: ارسال\n\n"
            "برای لغو: لغو",
        )
        return

    if text in ("لغو", "/cancel", "cancel"):
        states.pop(user_id, None)
        save_json(STATE_FILE, states)
        queue["photos"] = []
        save_json(PHOTO_QUEUE_FILE, queue)
        send_message(chat_id, "✅ عملیات لغو شد.")
        return

    if text in ("ارسال", "/send", "send", "بفرست"):
        if states.get(user_id) != "waiting_photos":
            send_message(chat_id, "ابتدا دستور «افزودن عکس» را بزنید.")
            return
        photos = queue.get("photos") or []
        if not photos:
            send_message(chat_id, "هنوز عکسی دریافت نشده. لطفاً عکس بفرستید.")
            return

        send_message(chat_id, f"⏳ در حال ارسال {len(photos)} عکس به کانال...")
        caption = get_caption_for_photo(PHONE_NUMBER, INSTAGRAM_URL, CHANNEL_LINK)
        sent = 0
        for i, fid in enumerate(photos):
            cap = caption if i == 0 else None  # کپشن فقط روی اولی
            result = send_file(CHANNEL_ID, fid, cap)
            if isinstance(result, dict) and result.get("status") == "OK":
                sent += 1
            time.sleep(1.5)

        states.pop(user_id, None)
        save_json(STATE_FILE, states)
        queue["photos"] = []
        save_json(PHOTO_QUEUE_FILE, queue)
        send_message(chat_id, f"✅ {sent} از {len(photos)} عکس به کانال ارسال شد.")
        return

    if text in ("/start", "شروع", "سلام"):
        send_message(
            chat_id,
            f"سلام 👋 ربات {BRAND_NAME}\n\n"
            "دستورات:\n"
            "• افزودن عکس → شروع دریافت عکس برای کانال\n"
            "• ارسال → انتشار عکس‌های دریافت‌شده در کانال\n"
            "• لغو → لغو عملیات\n",
        )
        return


def handle_file_message(chat_id: str, user_id: str, file_id: str):
    states = load_json(STATE_FILE, {})
    if states.get(user_id) != "waiting_photos":
        send_message(chat_id, "برای افزودن عکس ابتدا بنویسید: افزودن عکس")
        return
    if not is_admin(user_id):
        return

    queue = load_json(PHOTO_QUEUE_FILE, {"photos": []})
    queue.setdefault("photos", []).append(file_id)
    save_json(PHOTO_QUEUE_FILE, queue)
    count = len(queue["photos"])
    send_message(
        chat_id,
        f"✅ عکس {count} دریافت شد.\n"
        f"عکس بعدی را بفرستید یا بنویسید: ارسال",
    )


def extract_message_info(update: dict):
    """استخراج اطلاعات از آپدیت روبیکا"""
    # ساختارهای مختلف احتمالی
    msg = None
    if "new_message" in update:
        msg = update["new_message"]
        chat_id = update.get("chat_id")
    elif "message" in update:
        msg = update["message"]
        chat_id = msg.get("chat_id") or update.get("chat_id")
    else:
        return None

    if not msg:
        return None

    text = msg.get("text") or ""
    sender = msg.get("sender_id") or msg.get("author_id") or ""
    file_id = None

    # فایل / عکس
    file_inline = msg.get("file_inline") or msg.get("file") or {}
    if isinstance(file_inline, dict):
        file_id = file_inline.get("file_id") or file_inline.get("id")
    if not file_id:
        file_id = msg.get("file_id")

    return {
        "chat_id": chat_id or sender,
        "user_id": sender,
        "text": text,
        "file_id": file_id,
    }


def listen_loop():
    """حلقه دریافت پیام برای دستور افزودن عکس"""
    print("[LISTEN] شروع گوش دادن به پیام‌ها...")
    print("دستورات: افزودن عکس | ارسال | لغو")
    offset = None

    while True:
        try:
            data = get_updates(offset_id=offset)
            updates = []
            if isinstance(data, dict):
                inner = data.get("data") or data
                updates = inner.get("updates") or inner.get("new_message") and [inner] or []
                if not isinstance(updates, list):
                    updates = []
                # offset بعدی
                offset = inner.get("next_offset_id") or inner.get("offset_id") or offset

            for upd in updates:
                # ممکن است ساختار تو در تو باشد
                if "update" in upd:
                    upd = upd["update"]
                info = extract_message_info(upd)
                if not info:
                    continue
                if info.get("file_id"):
                    handle_file_message(info["chat_id"], info["user_id"], info["file_id"])
                elif info.get("text"):
                    handle_text_command(info["chat_id"], info["user_id"], info["text"])

            time.sleep(2)
        except Exception as e:
            print(f"[LISTEN ERROR] {e}")
            time.sleep(5)


def main():
    smart = "--smart" in sys.argv
    once = "--once" in sys.argv
    listen = "--listen" in sys.argv

    print("=" * 55)
    print(f"ربات {BRAND_NAME} | کانال {CHANNEL_USERNAME}")
    print("=" * 55)

    me = api_call("getMe")
    print(f"[INFO] ربات: {me}")

    if smart:
        smart_post()
        return

    if once:
        ok = send_text_promo()
        if ok:
            slot = current_slot() or "manual"
            mark_success(slot)
        return

    if listen:
        listen_loop()
        return

    # پیش‌فرض: یک بار هوشمند
    smart_post()


if __name__ == "__main__":
    main()
