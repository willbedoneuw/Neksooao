# پنل مدیریت اکانت‌های ایتا (فاز ۱ — بخش ایتا)

مدیریت چند اکانت ایتا از طریق اتوماسیون نسخه‌ی وب (`web.eitaa.com`) با Playwright.
این فاز فقط **بخش ایتا** است: لاگین، شمردن مخاطبین، و ارسال (متن/عکس/فایل/کپشن).
پنل تلگرام در فاز بعدی اضافه می‌شود.

> ⚠️ **درباره‌ی تست:** این کد باید روی **سیستم/سرور خودت** اجرا و تست شود، چون
> نیاز به اینترنت، شماره‌ی واقعی و کد تأیید ایتا دارد.
>
> ⚠️ **درباره‌ی سلکتورها:** ساختار HTML ایتاوب رسماً مستند نیست. سلکتورهای فایل
> `eitaa_panel/selectors.py` حدس‌های منطقی هستند و ممکن است لازم باشد بعد از
> اجرا با کمک DevTools تنظیمشان کنیم. این طبیعی است.

---

## نصب

نیاز: پایتون ۳.۹ به بالا.

```bash
cd eitaa-telegram-panel

# محیط مجازی
python3 -m venv .venv
source .venv/bin/activate        # ویندوز: .venv\Scripts\activate

# وابستگی‌ها
pip install -r requirements.txt

# نصب مرورگر Playwright
python -m playwright install chromium
# روی لینوکس سرور، اگر لازم شد:
# python -m playwright install-deps chromium

# فایل تنظیمات
cp .env.example .env
```

روی **سرور بدون گرافیک (headless)** برای دیدن مرورگر هنگام لاگین اول، یا از
`xvfb-run` استفاده کن یا موقتاً روی سیستم گرافیکی لاگین کن و پوشه‌ی `sessions/`
را به سرور منتقل کن.

---

## استفاده (تست دستی بخش ایتا)

هر اکانت یک شناسه‌ی دلخواه دارد (مثل `acc1`). سشِن هر اکانت جدا در `sessions/`
ذخیره می‌شود.

### ۱) لاگین (یک‌بار برای هر اکانت)
```bash
python -m eitaa_panel.cli login --account acc1 --phone 98912xxxxxxx
```
مرورگر باز می‌شود، شماره وارد می‌شود، بعد کدی که ایتا فرستاده را در ترمینال وارد
می‌کنی. سشِن ذخیره می‌شود تا دفعات بعد لاگین لازم نباشد.

### ۲) بررسی وضعیت
```bash
python -m eitaa_panel.cli status --account acc1
```

### ۳) تعداد و لیست مخاطبین
```bash
python -m eitaa_panel.cli contacts --account acc1
```

### ۴) ارسال به یک مخاطب (برای تست)
```bash
# متن
python -m eitaa_panel.cli send --account acc1 --to "علی" --text "سلام"

# عکس/فایل با کپشن
python -m eitaa_panel.cli send --account acc1 --to "علی" \
    --file ./media/pic.jpg --caption "این یک عکس است"
```

### ۵) ارسال به همه‌ی مخاطبین
```bash
python -m eitaa_panel.cli broadcast --account acc1 --text "پیام همگانی"
python -m eitaa_panel.cli broadcast --account acc1 --file ./media/file.pdf --caption "فایل"
```

---

## تنظیمات (`.env`)

| کلید | توضیح |
|------|-------|
| `HEADLESS` | مرورگر بدون نمایش. برای لاگین اول `false`. |
| `MIN_SEND_DELAY` / `MAX_SEND_DELAY` | مکث تصادفی بین ارسال‌ها (ضد بن). |
| `EITAA_WEB_URL` | آدرس ایتاوب. |
| `SESSIONS_DIR` / `MEDIA_DIR` | مسیر سشِن‌ها و فایل‌ها. |
| `DEFAULT_TIMEOUT_MS` | تایم‌اوت عملیات‌ها. |

---

## ساختار پروژه

```
eitaa-telegram-panel/
├── eitaa_panel/
│   ├── config.py         # تنظیمات از .env
│   ├── selectors.py      # سلکتورهای ایتاوب (اینجا تنظیم می‌شوند)
│   ├── eitaa_client.py   # منطق اتوماسیون (لاگین/مخاطب/ارسال)
│   └── cli.py            # ابزار تست خط فرمان
├── requirements.txt
├── .env.example
└── README.md
```

---

## نکات و محدودیت‌ها

- اتوماسیون احتمالاً خلاف قوانین ایتاست؛ ریسک محدودیت اکانت وجود دارد. برای هر
  اکانت مکث‌های معقول بگذار و از تعداد زیاد در IP یکسان خودداری کن.
- اگر آیتمی پیدا نشد، خطا می‌گوید کدام سلکتور را در `selectors.py` اصلاح کنی.
- فاز بعد: پنل تلگرام برای افزودن/مدیریت اکانت‌ها و اجرای این کارها از داخل چت.
