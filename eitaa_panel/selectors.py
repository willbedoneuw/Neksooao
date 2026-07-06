"""سلکتورهای متمرکز صفحه‌ی web.eitaa.com.

⚠️ مهم:
    ساختار HTML ایتاوب به‌صورت رسمی مستند نشده و ممکن است با این حدس‌ها فرق
    داشته باشد یا در آینده تغییر کند. بعد از باز کردن سایت با DevTools
    (کلیک راست → Inspect / بازرسی) سلکتور درست را پیدا و اینجا اصلاح کن.

قرارداد:
    هر ورودی یک «لیست» از سلکتورهای کاندید است که به‌ترتیب امتحان می‌شوند تا
    اولین موردی که پیدا شود استفاده شود. برای تنظیم، سلکتور درست را به ابتدای
    لیست اضافه کن.
"""

# --- فلوی لاگین ---
PHONE_INPUT = [
    'input[type="tel"]',
    'input[name="phone"]',
    'input[inputmode="tel"]',
    'input[autocomplete="tel"]',
]
PHONE_SUBMIT = [
    'button:has-text("بعدی")',
    'button:has-text("ادامه")',
    'button:has-text("Next")',
    'button[type="submit"]',
]
CODE_INPUT = [
    'input[name="code"]',
    'input[autocomplete="one-time-code"]',
    'input[inputmode="numeric"]',
    'input[type="tel"]',
]
CODE_SUBMIT = [
    'button:has-text("ورود")',
    'button:has-text("تایید")',
    'button:has-text("تأیید")',
    'button[type="submit"]',
]

# --- نشانه‌های لاگین موفق (لیست چت‌ها دیده می‌شود) ---
CHAT_LIST = [
    "#chatlist",
    ".chatlist",
    '[class*="chatlist" i]',
    '[class*="ChatList" i]',
    '[class*="chat-list" i]',
]

# --- جستجو و باز کردن چت ---
SEARCH_INPUT = [
    'input[type="search"]',
    "input.input-search",
    'input[placeholder*="جستجو"]',
    'input[placeholder*="Search"]',
]
SEARCH_RESULT_ITEM = [
    ".search-super .chatlist-chat",
    "ul.chatlist li",
    '[class*="search"] [class*="chatlist-chat"]',
    '[class*="search"] li',
]

# --- مخاطبین ---
# دکمه/آیتم منو برای باز کردن لیست مخاطبین
CONTACTS_MENU_BUTTON = [
    'button:has-text("مخاطبین")',
    'button:has-text("Contacts")',
    '.btn-menu-item:has-text("مخاطبین")',
    '[class*="menu"] :text("مخاطبین")',
]
CONTACT_ITEM = [
    ".contacts-container li.chatlist-chat",
    '[class*="contacts" i] li',
    "ul.contacts li",
    '[class*="contact" i][class*="item" i]',
]
# نام مخاطب داخل هر آیتم (نسبی به CONTACT_ITEM)
CONTACT_NAME = [
    ".peer-title",
    '[class*="title" i]',
    ".contact-name",
]

# --- کامپوزر پیام ---
MESSAGE_INPUT = [
    'div.input-message-input[contenteditable="true"]',
    'div[contenteditable="true"][data-placeholder]',
    'div[contenteditable="true"]',
    "textarea",
]
SEND_BUTTON = [
    "button.send",
    'button[class*="send" i]',
    'button:has-text("ارسال")',
    'button[aria-label*="Send"]',
]

# --- ضمیمه کردن فایل/عکس ---
ATTACH_BUTTON = [
    "button.attach",
    '[class*="attach" i]',
    'button[title*="ضمیمه"]',
    'button[aria-label*="Attach"]',
]
FILE_INPUT = [
    'input[type="file"]',
]
# فیلد کپشن در دیالوگ ارسال مدیا (اغلب همان کامپوزر است)
CAPTION_INPUT = [
    'div.popup-send-photo div[contenteditable="true"]',
    'div[contenteditable="true"][data-placeholder]',
    'div[contenteditable="true"]',
    "textarea",
]
# دکمه‌ی تأیید نهایی ارسال مدیا در دیالوگ
MEDIA_SEND_CONFIRM = [
    ".popup-send-photo button.send",
    'button:has-text("ارسال")',
    "button.send",
    'button[class*="send" i]',
]
