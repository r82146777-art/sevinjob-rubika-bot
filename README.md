# ربات تبلیغاتی سوین چوب (خصوصی)

ربات ارسال خودکار ۲ پست تبلیغاتی روزانه (عکس + متن) به کانال روبیکا سوین چوب.

**مخزن خصوصی است** – توکن و اطلاعات حساس فقط برای مالک قابل مشاهده است.

## زمان‌بندی
- هر روز ساعت **۱۱:۰۰ صبح** (وقت ایران)
- هر روز ساعت **۲۰:۰۰ شب** (وقت ایران)

## محتوا
هر پست شامل:
- عکس تبلیغاتی با شماره تلفن، آیدی کانال و اینستاگرام
- متن تبلیغاتی جذاب در مورد سرویس خواب
- در انتهای متن: شماره تلفن + آیدی کانال + لینک اینستاگرام + لینک کانال

## اجرا برای ۶ ماه (و بیشتر)

برای اینکه ربات ۶ ماه مداوم کار کند باید روی یک سرور (VPS یا کامپیوتر روشن) اجرا شود.

### روش پیشنهادی (systemd روی لینوکس):

```bash
# نصب وابستگی‌ها
pip install -r requirements.txt

# تست دستی
python bot.py

# ساخت سرویس systemd (مثال)
sudo nano /etc/systemd/system/sevinchoob-bot.service
```

محتوای سرویس:
```ini
[Unit]
Description=Sevin Choob Rubika Promo Bot
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/path/to/sevinjob-rubika-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

سپس:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sevinchoob-bot
sudo systemctl start sevinchoob-bot
sudo systemctl status sevinchoob-bot
```

### نکات امنیتی
- این مخزن **خصوصی** است.
- توکن ربات و اطلاعات تماس فقط در `config.py` قرار دارد.
- هرگز این مخزن را عمومی نکنید.

ساخته شده برای شرکت سوین چوب 🛏️
