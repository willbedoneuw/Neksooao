"""کلاینت اتوماسیون ایتاوب با Playwright.

هر نمونه یک اکانت را مدیریت می‌کند و سشِن آن را جدا نگه می‌دارد.

متدهای اصلی:
    - start() / close()            : باز و بسته کردن مرورگر
    - is_logged_in()               : بررسی لاگین بودن
    - request_login_code(phone)    : وارد کردن شماره و درخواست کد
    - submit_code(code)            : وارد کردن کد و ذخیره سشِن
    - list_contacts()              : لیست نام مخاطبین
    - get_contact_count()          : تعداد مخاطبین
    - send_to_contact(...)         : ارسال به یک مخاطب
    - broadcast(...)               : ارسال به همه مخاطبین
"""

import asyncio
import logging
import random
from datetime import datetime
from typing import Awaitable, Callable, List, Optional, Sequence, Tuple

from playwright.async_api import (
    BrowserContext,
    Page,
    TimeoutError as PWTimeout,
    async_playwright,
)

from . import config
from . import selectors as S

logger = logging.getLogger(__name__)

# نتیجه‌ی ارسال به هر مخاطب: (نام، موفق؟، پیام خطا)
SendResult = Tuple[str, bool, Optional[str]]


def normalize_iran_phone(raw: str) -> str:
    """شماره را به فرمت ملی ۱۰رقمی (9xxxxxxxxx) تبدیل می‌کند.

    فیلد شماره از قبل +98 دارد، پس فقط بخش ملی را تایپ می‌کنیم.
    """
    p = raw.strip().replace(" ", "").replace("-", "").replace("+", "")
    if p.startswith("0098"):
        p = p[4:]
    if p.startswith("98") and len(p) > 10:
        p = p[2:]
    if p.startswith("0"):
        p = p[1:]
    return p


class EitaaClient:
    def __init__(
        self,
        account_id: str,
        phone: Optional[str] = None,
        headless: Optional[bool] = None,
    ):
        self.account_id = account_id
        self.phone = phone
        self.headless = config.HEADLESS if headless is None else headless
        self.storage_path = config.session_path(account_id)

        self._pw = None
        self._browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    # ------------------------------------------------------------------ #
    # چرخه‌ی حیات مرورگر
    # ------------------------------------------------------------------ #
    async def start(self) -> "EitaaClient":
        self._pw = await async_playwright().start()

        launch_kwargs = {"headless": self.headless, "args": config.BROWSER_ARGS}
        if config.BROWSER_EXECUTABLE_PATH:
            launch_kwargs["executable_path"] = config.BROWSER_EXECUTABLE_PATH
            logger.info("استفاده از مرورگر سیستمی: %s", config.BROWSER_EXECUTABLE_PATH)
        self._browser = await self._pw.chromium.launch(**launch_kwargs)

        context_kwargs = {
            "locale": "fa-IR",
            "viewport": {"width": 1280, "height": 800},
        }
        if self.storage_path.exists():
            context_kwargs["storage_state"] = str(self.storage_path)
            logger.info("سشِن قبلی بارگذاری شد: %s", self.storage_path)

        self.context = await self._browser.new_context(**context_kwargs)
        self.context.set_default_timeout(config.DEFAULT_TIMEOUT)
        self.page = await self.context.new_page()
        await self.page.goto(config.EITAA_WEB_URL, wait_until="domcontentloaded")
        return self

    async def close(self) -> None:
        for closer in (
            getattr(self.context, "close", None),
            getattr(self._browser, "close", None),
            getattr(self._pw, "stop", None),
        ):
            if closer is None:
                continue
            try:
                await closer()
            except Exception:  # noqa: BLE001 - بستن نباید کرش کند
                pass

    async def save_session(self) -> None:
        if self.context:
            await self.context.storage_state(path=str(self.storage_path))
            logger.info("سشِن ذخیره شد: %s", self.storage_path)

    async def __aenter__(self) -> "EitaaClient":
        return await self.start()

    async def __aexit__(self, *exc) -> None:
        await self.close()

    # ------------------------------------------------------------------ #
    # کمک‌کننده‌ها
    # ------------------------------------------------------------------ #
    async def _find(self, candidates: Sequence[str], timeout: Optional[int] = None, state: str = "visible"):
        """اولین سلکتوری که پیدا شود را به‌صورت Locator برمی‌گرداند."""
        timeout = timeout or config.DEFAULT_TIMEOUT
        per = max(1000, int(timeout / len(candidates)))
        for sel in candidates:
            # وقتی دنبال المان قابل‌مشاهده‌ایم، المان‌های مخفی (باقی‌مانده از
            # صفحات قبلیِ تلگرام‌وب) را نادیده بگیر تا روی هیچ گیر نکنیم.
            effective = f"{sel} >> visible=true" if state == "visible" else sel
            loc = self.page.locator(effective).first
            try:
                await loc.wait_for(state=state, timeout=per)
                return loc
            except PWTimeout:
                continue
        raise PWTimeout(f"هیچ‌کدام از سلکتورها پیدا نشد: {list(candidates)}")

    async def _resolve(self, candidates: Sequence[str], timeout: int = 8000) -> Optional[str]:
        """اولین رشته‌ی سلکتوری که حداقل یک المان دارد را برمی‌گرداند."""
        per = max(800, int(timeout / len(candidates)))
        for sel in candidates:
            try:
                await self.page.locator(sel).first.wait_for(state="attached", timeout=per)
                return sel
            except PWTimeout:
                continue
        return None

    async def dump_debug(self, label: str = "error") -> Optional[str]:
        """هنگام خطا از صفحه اسکرین‌شات و HTML می‌گیرد تا دیباگ سلکتورها راحت شود.

        مسیرِ پایه‌ی فایل‌ها را برمی‌گرداند (بدون پسوند).
        """
        if not config.DEBUG_ON_ERROR or self.page is None:
            return None
        safe = "".join(c for c in label if c.isalnum() or c in ("-", "_"))[:40]
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = config.DEBUG_DIR / f"{self.account_id}_{safe}_{stamp}"
        try:
            await self.page.screenshot(path=f"{base}.png", full_page=True)
            html = await self.page.content()
            with open(f"{base}.html", "w", encoding="utf-8") as fh:
                fh.write(html)
            logger.warning("دیباگ ذخیره شد: %s.png و %s.html", base, base)
            return str(base)
        except Exception as exc:  # noqa: BLE001
            logger.error("ذخیره‌ی دیباگ ناموفق بود: %s", exc)
            return None

    async def describe_page(self) -> str:
        """ساختار المان‌های قابل‌مشاهده‌ی صفحه‌ی فعلی را متنی برمی‌گرداند (برای تنظیم سلکتور)."""
        if self.page is None:
            return "(no page)"
        lines: List[str] = []
        try:
            lines.append(f"URL   : {self.page.url}")
            lines.append(f"TITLE : {await self.page.title()}")
        except Exception:  # noqa: BLE001
            pass

        async def _grab(selector: str, js: str, header: str) -> None:
            try:
                items = await self.page.eval_on_selector_all(selector, js)
                lines.append(f"\n[{header} = {len(items)}]")
                lines.extend(str(x) for x in items)
            except Exception as exc:  # noqa: BLE001
                lines.append(f"\n[{header}] خطا: {exc}")

        vis = "els => els.filter(e => e.offsetParent !== null)"
        await _grab("input", f"{vis}.map(e => e.outerHTML)", "VISIBLE INPUTS")
        await _grab(
            "[contenteditable='true']",
            f"{vis}.map(e => e.outerHTML.slice(0, 220))",
            "VISIBLE CONTENTEDITABLE",
        )
        await _grab(
            "button",
            f"{vis}.map(e => ((e.innerText||e.getAttribute('aria-label')||'').trim()) + '  ||  class=' + e.className)",
            "VISIBLE BUTTONS",
        )
        await _grab(
            "h1,h2,h3,h4,label,.subtitle,.i18n,.input-field",
            f"{vis}.map(e => (e.innerText||'').trim()).filter(t => t).slice(0, 40)",
            "VISIBLE TEXT",
        )
        return "\n".join(lines)

    async def _pause(self, a: float = 0.3, b: float = 1.0) -> None:
        await asyncio.sleep(random.uniform(a, b))

    async def _send_delay(self) -> None:
        await asyncio.sleep(random.uniform(config.MIN_SEND_DELAY, config.MAX_SEND_DELAY))

    # ------------------------------------------------------------------ #
    # لاگین
    # ------------------------------------------------------------------ #
    async def is_logged_in(self) -> bool:
        try:
            await self._find(S.CHAT_LIST, timeout=8000)
            return True
        except PWTimeout:
            return False

    async def request_login_code(self, phone: Optional[str] = None) -> bool:
        """شماره را وارد و کد تأیید را درخواست می‌کند.

        اگر از قبل لاگین باشد False برمی‌گرداند، در غیر این صورت True.
        """
        phone = phone or self.phone
        if not phone:
            raise ValueError("شماره لازم است.")

        logger.info("① باز کردن صفحه‌ی ایتاوب ...")
        await self.page.goto(config.EITAA_WEB_URL, wait_until="domcontentloaded")
        if await self.is_logged_in():
            logger.info("قبلاً لاگین بوده؛ نیازی به کد نیست.")
            return False

        # فیلد شماره یک contenteditable است که از قبل +98 دارد؛
        # کلیک می‌کنیم، مکان‌نما را به آخر می‌بریم و بخش ملی شماره را تایپ می‌کنیم.
        national = normalize_iran_phone(phone)
        logger.info("② وارد کردن شماره (+98 %s) ...", national)
        phone_field = await self._find(S.PHONE_INPUT)
        await phone_field.click()
        await self.page.keyboard.press("End")
        await self.page.keyboard.type(national, delay=90)
        await self._pause(0.6, 1.3)

        logger.info("③ زدن دکمه‌ی «ادامه» ...")
        submit = await self._find(S.PHONE_SUBMIT)
        await submit.click()

        # کمی صبر تا انیمیشن گذار به صفحه‌ی کد تمام شود
        await self._pause(1.0, 2.0)
        logger.info("④ منتظر ظاهر شدن فیلد کد ...")
        await self._find(S.CODE_INPUT, timeout=25000)
        logger.info("✅ فیلد کد پیدا شد. حالا کد ارسالی ایتا را وارد کن.")
        return True

    async def submit_code(self, code: str) -> bool:
        """کد تأیید را وارد و در صورت موفقیت سشِن را ذخیره می‌کند."""
        code_field = await self._find(S.CODE_INPUT)
        await code_field.click()
        # تلگرام‌وب کد را رقم‌به‌رقم می‌خواند و اغلب خودکار ثبت می‌کند.
        await self.page.keyboard.type(code, delay=140)
        await self._pause(0.6, 1.2)

        # اگر دکمه‌ای بود بزن، وگرنه Enter (هر دو بی‌ضررند).
        try:
            submit = await self._find(S.CODE_SUBMIT, timeout=4000)
            await submit.click()
        except PWTimeout:
            try:
                await self.page.keyboard.press("Enter")
            except Exception:  # noqa: BLE001
                pass

        # منتظر لیست چت‌ها (نشانه‌ی لاگین موفق). اگر رمز دومرحله‌ای فعال باشد
        # این‌جا تایم‌اوت می‌خورد و اسکرین‌شات دیباگ ذخیره می‌شود.
        await self._find(S.CHAT_LIST, timeout=45000)
        await self.save_session()
        logger.info("لاگین موفق برای اکانت %s", self.account_id)
        return True

    # ------------------------------------------------------------------ #
    # مخاطبین
    # ------------------------------------------------------------------ #
    async def open_contacts(self) -> None:
        # منوی همبرگری بالا-چپ را باز کن، بعد آیتم «مخاطبین» را بزن.
        menu = await self._find(S.CONTACTS_MENU_BUTTON)
        await menu.click()
        await self._pause(0.4, 0.9)
        item = await self._find(S.CONTACTS_MENU_ITEM)
        await item.click()
        await self._find(S.CONTACT_ITEM, timeout=15000)

    async def list_contacts(self, max_scroll: int = 80) -> List[str]:
        """لیست نام مخاطبین را با اسکرول تدریجی جمع‌آوری می‌کند."""
        await self.open_contacts()
        item_sel = await self._resolve(S.CONTACT_ITEM, timeout=15000)
        if not item_sel:
            logger.warning("آیتم مخاطب پیدا نشد؛ سلکتورها را در selectors.py چک کن.")
            return []

        names: List[str] = []
        seen = set()
        prev_total = -1
        stable = 0

        for _ in range(max_scroll):
            items = self.page.locator(item_sel)
            count = await items.count()
            for i in range(count):
                item = items.nth(i)
                try:
                    text = (await item.inner_text()).strip().splitlines()[0].strip()
                except Exception:  # noqa: BLE001
                    continue
                if text and text not in seen:
                    seen.add(text)
                    names.append(text)

            if len(names) == prev_total:
                stable += 1
                if stable >= 3:  # چند بار پشت‌سرهم بدون تغییر → تمام شد
                    break
            else:
                stable = 0
                prev_total = len(names)

            if count:
                try:
                    await items.nth(count - 1).scroll_into_view_if_needed()
                except Exception:  # noqa: BLE001
                    pass
            await self._pause(0.3, 0.7)

        logger.info("تعداد مخاطبین یافت‌شده: %d", len(names))
        return names

    async def get_contact_count(self) -> int:
        return len(await self.list_contacts())

    # ------------------------------------------------------------------ #
    # ارسال
    # ------------------------------------------------------------------ #
    async def open_chat(self, query: str) -> None:
        """با جستجو، چت یک مخاطب را باز می‌کند."""
        search = await self._find(S.SEARCH_INPUT)
        await search.click()
        await search.fill("")
        await search.type(query, delay=40)
        await self._pause(0.8, 1.6)

        result_sel = await self._resolve(S.SEARCH_RESULT_ITEM, timeout=10000)
        if not result_sel:
            raise RuntimeError(f"نتیجه‌ای برای «{query}» پیدا نشد.")
        await self.page.locator(result_sel).first.click()
        await self._find(S.MESSAGE_INPUT, timeout=15000)

    async def send_text(self, text: str) -> None:
        box = await self._find(S.MESSAGE_INPUT)
        await box.click()
        await box.fill(text)
        await self._pause(0.3, 0.8)
        try:
            btn = await self._find(S.SEND_BUTTON, timeout=4000)
            await btn.click()
        except PWTimeout:
            await box.press("Enter")

    async def send_media(self, media_path: str, caption: Optional[str] = None) -> None:
        media_path = str(media_path)

        file_sel = await self._resolve(S.FILE_INPUT, timeout=4000)
        if not file_sel:
            # شاید لازم است اول دکمه‌ی ضمیمه کلیک شود تا input ساخته شود
            try:
                attach = await self._find(S.ATTACH_BUTTON, timeout=4000)
                await attach.click()
            except PWTimeout:
                pass
            file_sel = await self._resolve(S.FILE_INPUT, timeout=6000)
        if not file_sel:
            raise RuntimeError("input[type=file] پیدا نشد؛ سلکتورهای ATTACH/FILE را چک کن.")

        await self.page.locator(file_sel).first.set_input_files(media_path)

        if caption:
            try:
                cap = await self._find(S.CAPTION_INPUT, timeout=6000)
                await cap.click()
                await cap.fill(caption)
            except PWTimeout:
                logger.warning("فیلد کپشن پیدا نشد؛ بدون کپشن ارسال می‌شود.")

        await self._pause(0.4, 1.0)
        confirm = await self._find(S.MEDIA_SEND_CONFIRM)
        await confirm.click()

    async def send_to_contact(
        self,
        query: str,
        text: Optional[str] = None,
        media_path: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> None:
        """به یک مخاطب پیام می‌فرستد. اگر media_path باشد فایل/عکس (با کپشن) وگرنه متن."""
        if not text and not media_path:
            raise ValueError("چیزی برای ارسال داده نشده (نه متن نه فایل).")

        await self.open_chat(query)
        if media_path:
            await self.send_media(media_path, caption=caption or text)
        else:
            await self.send_text(text)
        await self._pause(0.5, 1.2)

    async def broadcast(
        self,
        text: Optional[str] = None,
        media_path: Optional[str] = None,
        caption: Optional[str] = None,
        contacts: Optional[List[str]] = None,
        progress: Optional[Callable[[int, int, str, bool], Awaitable[None]]] = None,
    ) -> List[SendResult]:
        """به همه‌ی مخاطبین (یا لیست داده‌شده) ارسال می‌کند."""
        if contacts is None:
            contacts = await self.list_contacts()

        results: List[SendResult] = []
        total = len(contacts)
        for index, name in enumerate(contacts, start=1):
            try:
                await self.send_to_contact(name, text=text, media_path=media_path, caption=caption)
                results.append((name, True, None))
                logger.info("[%d/%d] ارسال شد → %s", index, total, name)
                ok = True
            except Exception as exc:  # noqa: BLE001
                results.append((name, False, str(exc)))
                logger.error("[%d/%d] ناموفق → %s: %s", index, total, name, exc)
                await self.dump_debug(f"broadcast_{index}_{name}")
                ok = False

            if progress:
                await progress(index, total, name, ok)

            if index < total:
                await self._send_delay()  # مکث تصادفی ضد بن

        return results
