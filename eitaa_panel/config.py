"""تنظیمات مرکزی برنامه. مقادیر از فایل .env خوانده می‌شوند."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # dotenv اختیاری است
    pass


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


BASE_DIR = Path(__file__).resolve().parent.parent

SESSIONS_DIR = Path(os.getenv("SESSIONS_DIR", str(BASE_DIR / "sessions"))).expanduser()
MEDIA_DIR = Path(os.getenv("MEDIA_DIR", str(BASE_DIR / "media"))).expanduser()
LOG_DIR = Path(os.getenv("LOG_DIR", str(BASE_DIR / "logs"))).expanduser()
# محل ذخیره‌ی اسکرین‌شات و HTML هنگام خطا (برای دیباگ سلکتورها)
DEBUG_DIR = Path(os.getenv("DEBUG_DIR", str(BASE_DIR / "debug"))).expanduser()

EITAA_WEB_URL = os.getenv("EITAA_WEB_URL", "https://web.eitaa.com").rstrip("/")

HEADLESS = _as_bool(os.getenv("HEADLESS"), default=False)

# اگر مرورگر پلی‌رایت دانلود نشد، مسیر chromium سیستمی را اینجا بده
# مثال: /usr/bin/chromium یا /usr/bin/chromium-browser
BROWSER_EXECUTABLE_PATH = os.getenv("BROWSER_EXECUTABLE_PATH") or None

# آرگومان‌های راه‌اندازی مرورگر. --no-sandbox برای اجرا با کاربر root لازم است.
_default_browser_args = "--no-sandbox,--disable-dev-shm-usage"
BROWSER_ARGS = [
    a.strip() for a in os.getenv("BROWSER_ARGS", _default_browser_args).split(",") if a.strip()
]

MIN_SEND_DELAY = float(os.getenv("MIN_SEND_DELAY", "3"))
MAX_SEND_DELAY = float(os.getenv("MAX_SEND_DELAY", "9"))

DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT_MS", "30000"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
# هنگام خطا اسکرین‌شات و HTML ذخیره شود؟
DEBUG_ON_ERROR = _as_bool(os.getenv("DEBUG_ON_ERROR"), default=True)

# ساخت پوشه‌ها اگر وجود ندارند
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def session_path(account_id: str) -> Path:
    """مسیر فایل سشِنِ یک اکانت."""
    safe = "".join(c for c in account_id if c.isalnum() or c in ("-", "_"))
    return SESSIONS_DIR / f"{safe}.json"
