"""سلکتورهای صفحه‌ی web.eitaa.com.

کشف مهم: ایتاوب یک فورک از «Telegram Web K» است، پس ساختار HTML همان است
(کلاس‌هایی مثل input-field-input, btn-primary, chatlist-chat, input-message-input).

قرارداد: هر ورودی یک لیست از سلکتورهای کاندید است که به‌ترتیب امتحان می‌شوند.
سلکتورهای لاگین از روی DOM واقعی تأیید شده‌اند؛ سلکتورهای مخاطبین/ارسال بر اساس
ساختار تلگرام‌وب حدس زده شده‌اند و بعد از لاگین با دستور inspect نهایی می‌شوند.
"""

# --- فلوی لاگین (تأییدشده از DOM واقعی) ---
# فیلد شماره یک div با contenteditable است، نه input.
PHONE_INPUT = [
    'div.input-field-input[inputmode="decimal"]',
    '.input-field-input[inputmode="decimal"]',
    'input[type="tel"]',
]
PHONE_SUBMIT = [
    'button.btn-primary:has-text("ادامه")',
    'button.btn-primary',
    'button:has-text("ادامه")',
    'button:has-text("Next")',
]
# صفحه‌ی کد بعد از «ادامه» می‌آید؛ فیلد کد یک <input type="tel"> است
# با کلاس input-field-input (نه contenteditable). از روی DOM واقعی تأیید شد.
CODE_INPUT = [
    'input.input-field-input[type="tel"]',
    'input[type="tel"]',
    "input.input-field-input",
    "input[required]",
]
# ⚠️ روی صفحه‌ی کد فقط دکمه‌ی «ارسال مجدد با پیامک» هست که نباید زده شود.
# تلگرام‌وب کد را خودکار ثبت می‌کند، پس دکمه‌ای نمی‌زنیم.
CODE_SUBMIT: list = []

# --- نشانه‌های لاگین موفق ---
CHAT_LIST = [
    "#column-left",
    "#column-center",
    "#page-chats",
    ".chatlist",
    "ul.chatlist",
    ".chatlist-container",
    ".sidebar-header",
    ".input-search-input",
]

# فیلد رمز تأیید دومرحله‌ای (اگر اکانت 2FA داشته باشد)
PASSWORD_INPUT = [
    'input[type="password"]',
    '.input-field-input[type="password"]',
    'div.input-field-input[contenteditable="true"][type="password"]',
]

# --- جستجو و باز کردن چت ---
SEARCH_INPUT = [
    ".input-search-input",
    "input.input-search-input",
    '#column-left input[type="text"]',
]
SEARCH_RESULT_ITEM = [
    ".search-super .chatlist-chat",
    "#search-container .chatlist-chat",
    "ul.chatlist a.chatlist-chat",
    ".chatlist-chat",
]

# --- مخاطبین (منوی همبرگری → مخاطبین) ---
CONTACTS_MENU_BUTTON = [
    ".btn-menu-toggle",
    ".sidebar-tools-button",
    "button.btn-icon.sidebar-tools-button",
]
CONTACTS_MENU_ITEM = [
    '.btn-menu-item:has-text("مخاطبین")',
    '.btn-menu-item:has-text("Contacts")',
]
CONTACT_ITEM = [
    ".contacts-container .chatlist-chat",
    ".sidebar-slider .chatlist-chat",
    "ul.chatlist li.chatlist-chat",
    ".chatlist-chat",
]
CONTACT_NAME = [
    ".peer-title",
    ".dialog-title .peer-title",
]

# --- کامپوزر پیام ---
MESSAGE_INPUT = [
    'div.input-message-input[contenteditable="true"]',
    '.input-message-container [contenteditable="true"]',
    'div[contenteditable="true"]',
]
SEND_BUTTON = [
    ".btn-send",
    "button.btn-send",
    ".btn-icon.btn-send",
]

# --- ضمیمه فایل/عکس ---
ATTACH_BUTTON = [
    ".attach-file",
    ".btn-icon.attach-file",
]
FILE_INPUT = [
    'input[type="file"]',
]
CAPTION_INPUT = [
    ".popup-new-media .input-message-input",
    ".popup .input-message-input",
    'div.input-message-input[contenteditable="true"]',
]
MEDIA_SEND_CONFIRM = [
    ".popup-new-media .btn-primary",
    ".popup .btn-primary",
    ".popup .btn-send",
    ".btn-send",
]
