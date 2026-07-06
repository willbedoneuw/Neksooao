"""ابزار خط فرمان برای تست دستی بخش ایتا (فاز ۱).

نمونه‌ها:
    python -m eitaa_panel.cli login    --account acc1 --phone 98912xxxxxxx
    python -m eitaa_panel.cli status   --account acc1
    python -m eitaa_panel.cli contacts --account acc1
    python -m eitaa_panel.cli send      --account acc1 --to "علی" --text "سلام"
    python -m eitaa_panel.cli send      --account acc1 --to "علی" --file ./media/pic.jpg --caption "عکس"
    python -m eitaa_panel.cli broadcast --account acc1 --text "پیام همگانی"
"""

import argparse
import asyncio
import logging

from . import config
from .eitaa_client import EitaaClient


def _setup_logging() -> None:
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    root = logging.getLogger()
    root.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))
    root.handlers.clear()

    # کنسول
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)

    # فایل (همه‌ی اجراها اینجا ذخیره می‌شوند)
    log_file = config.LOG_DIR / "eitaa.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    logging.getLogger(__name__).info("لاگ در این فایل ذخیره می‌شود: %s", log_file)


async def _ainput(prompt: str) -> str:
    """input بدون بلاک کردن حلقه‌ی asyncio."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)


async def cmd_login(args: argparse.Namespace) -> None:
    # لاگین همیشه با مرورگر قابل‌مشاهده تا کد را راحت وارد کنی
    client = EitaaClient(args.account, phone=args.phone, headless=False)
    await client.start()
    try:
        if await client.is_logged_in():
            print("این اکانت از قبل لاگین است؛ سشِن معتبر ذخیره شد. ✅")
            await client.save_session()
            return

        phone = args.phone or (await _ainput("شماره (با کد کشور، مثل 98912xxxxxxx): ")).strip()
        requested = await client.request_login_code(phone)
        if not requested:
            print("در همین حین لاگین شناسایی شد. ✅")
            return

        code = (await _ainput("کدی که ایتا فرستاد را وارد کن: ")).strip()
        await client.submit_code(code)
        print("لاگین موفق بود و سشِن ذخیره شد. ✅")
    except Exception as exc:  # noqa: BLE001
        base = await client.dump_debug("login")
        print(f"خطا در لاگین: {exc}")
        if base:
            print(f"برای دیباگ این فایل‌ها ذخیره شد: {base}.png و {base}.html")
        raise
    finally:
        await client.close()


async def _with_client(args: argparse.Namespace):
    client = EitaaClient(args.account, headless=config.HEADLESS)
    await client.start()
    return client


async def cmd_status(args: argparse.Namespace) -> None:
    client = await _with_client(args)
    try:
        ok = await client.is_logged_in()
        print("وضعیت:", "لاگین ✅" if ok else "لاگین نیست ❌ (اول login بزن)")
    finally:
        await client.close()


async def cmd_contacts(args: argparse.Namespace) -> None:
    client = await _with_client(args)
    try:
        if not await client.is_logged_in():
            print("اول باید login کنی. ❌")
            return
        names = await client.list_contacts()
        print(f"تعداد مخاطبین: {len(names)}")
        for name in names:
            print("  -", name)
    except Exception as exc:  # noqa: BLE001
        base = await client.dump_debug("contacts")
        print(f"خطا: {exc}")
        if base:
            print(f"دیباگ ذخیره شد: {base}.png و {base}.html")
        raise
    finally:
        await client.close()


async def cmd_send(args: argparse.Namespace) -> None:
    client = await _with_client(args)
    try:
        if not await client.is_logged_in():
            print("اول باید login کنی. ❌")
            return
        await client.send_to_contact(
            args.to, text=args.text, media_path=args.file, caption=args.caption
        )
        print(f"ارسال به «{args.to}» انجام شد. ✅")
    except Exception as exc:  # noqa: BLE001
        base = await client.dump_debug("send")
        print(f"خطا در ارسال: {exc}")
        if base:
            print(f"دیباگ ذخیره شد: {base}.png و {base}.html")
        raise
    finally:
        await client.close()


async def cmd_broadcast(args: argparse.Namespace) -> None:
    client = await _with_client(args)
    try:
        if not await client.is_logged_in():
            print("اول باید login کنی. ❌")
            return
        results = await client.broadcast(
            text=args.text, media_path=args.file, caption=args.caption
        )
        ok = sum(1 for _, success, _ in results if success)
        print(f"\nتمام شد. موفق: {ok}/{len(results)}")
        for name, success, err in results:
            if not success:
                print(f"  ❌ {name}: {err}")
    except Exception as exc:  # noqa: BLE001
        base = await client.dump_debug("broadcast")
        print(f"خطا: {exc}")
        if base:
            print(f"دیباگ ذخیره شد: {base}.png و {base}.html")
        raise
    finally:
        await client.close()


async def cmd_inspect(args: argparse.Namespace) -> None:
    """صفحه‌ی فعلی را باز می‌کند و همه‌ی input/button ها را چاپ می‌کند تا سلکتورها را تنظیم کنیم."""
    client = await _with_client(args)
    try:
        await client.page.wait_for_timeout(args.wait * 1000)
        print("URL   :", client.page.url)
        try:
            print("TITLE :", await client.page.title())
        except Exception:  # noqa: BLE001
            pass

        inputs = await client.page.eval_on_selector_all(
            "input", "els => els.map(e => e.outerHTML)"
        )
        print(f"\n===== INPUTS ({len(inputs)}) =====")
        for html in inputs:
            print(html)

        buttons = await client.page.eval_on_selector_all(
            "button",
            "els => els.map(e => (e.innerText || e.getAttribute('aria-label') || '') "
            "+ '  ||  ' + e.outerHTML.slice(0, 160))",
        )
        print(f"\n===== BUTTONS ({len(buttons)}) =====")
        for line in buttons:
            print(line)

        contenteditables = await client.page.eval_on_selector_all(
            "[contenteditable='true']", "els => els.map(e => e.outerHTML.slice(0, 200))"
        )
        print(f"\n===== CONTENTEDITABLE ({len(contenteditables)}) =====")
        for html in contenteditables:
            print(html)

        base = await client.dump_debug("inspect")
        if base:
            print(f"\nاسکرین‌شات و HTML کامل اینجا ذخیره شد:\n  {base}.png\n  {base}.html")
    finally:
        await client.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eitaa_panel.cli", description="تست بخش ایتا")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_inspect = sub.add_parser("inspect", help="بازرسی صفحه برای تنظیم سلکتورها")
    p_inspect.add_argument("--account", required=True)
    p_inspect.add_argument("--wait", type=int, default=7, help="ثانیه صبر تا صفحه کامل بارگذاری شود")
    p_inspect.set_defaults(func=cmd_inspect)

    p_login = sub.add_parser("login", help="لاگین و ذخیره‌ی سشِن (تعاملی)")
    p_login.add_argument("--account", required=True, help="شناسه‌ی دلخواه اکانت، مثل acc1")
    p_login.add_argument("--phone", help="شماره با کد کشور")
    p_login.set_defaults(func=cmd_login)

    p_status = sub.add_parser("status", help="بررسی لاگین بودن")
    p_status.add_argument("--account", required=True)
    p_status.set_defaults(func=cmd_status)

    p_contacts = sub.add_parser("contacts", help="نمایش تعداد و نام مخاطبین")
    p_contacts.add_argument("--account", required=True)
    p_contacts.set_defaults(func=cmd_contacts)

    p_send = sub.add_parser("send", help="ارسال به یک مخاطب (برای تست)")
    p_send.add_argument("--account", required=True)
    p_send.add_argument("--to", required=True, help="نام یا آیدی مخاطب برای جستجو")
    p_send.add_argument("--text", help="متن پیام")
    p_send.add_argument("--file", help="مسیر عکس/فایل")
    p_send.add_argument("--caption", help="کپشن برای عکس/فایل")
    p_send.set_defaults(func=cmd_send)

    p_bc = sub.add_parser("broadcast", help="ارسال به همه‌ی مخاطبین")
    p_bc.add_argument("--account", required=True)
    p_bc.add_argument("--text", help="متن پیام")
    p_bc.add_argument("--file", help="مسیر عکس/فایل")
    p_bc.add_argument("--caption", help="کپشن برای عکس/فایل")
    p_bc.set_defaults(func=cmd_broadcast)

    return parser


def main(argv=None) -> None:
    _setup_logging()
    args = build_parser().parse_args(argv)
    asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
