"""Главная точка входа Playerok Universal.

Windows: start.bat / python bot.py
Linux/хостинг: python server.py (эквивалент python bot.py)

Основная бизнес-логика осталась в core/, plbot/, playerokapi/, tgbot/.
Это сохраняет интерфейсы модулей и существующие настройки.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parent
# Пути пользовательских данных исторически относительны. Поэтому переход в
# корень проекта должен происходить ДО импорта settings.py и data.py.
os.chdir(ROOT)


def apply_environment_config() -> None:
    """Переносит секреты из переменных окружения в существующий JSON-конфиг.

    Полезно для хостингов, на которых нет интерактивной консоли.
    Пустое значение окружения НЕ стирает сохранённое значение.
    """
    from settings import Settings

    values = {
        ("telegram", "api", "token"): (
            "TELEGRAM_BOT_TOKEN", "TG_BOT_TOKEN", "BOT_TOKEN"
        ),
        ("telegram", "api", "proxy"): ("TELEGRAM_PROXY",),
        ("telegram", "api", "custom_api_url"): ("TELEGRAM_API_URL",),
        ("playerok", "api", "cookies"): ("PLAYEROK_COOKIES",),
        ("playerok", "api", "user_agent"): ("PLAYEROK_USER_AGENT",),
        ("playerok", "api", "proxy"): ("PLAYEROK_PROXY",),
    }
    config = Settings.get("config")
    changed = False
    for (section, group, key), names in values.items():
        value = next((os.environ[n] for n in names if os.environ.get(n)), None)
        if value is not None and config[section][group][key] != value:
            config[section][group][key] = value
            changed = True
    if changed:
        Settings.set("config", config)


def main() -> int:
    # Диагностика не требует aiogram, curl_cffi или Telegram-токена.
    if "--doctor" in sys.argv or "--check" in sys.argv:
        from doctor import main as doctor_main
        return doctor_main()

    # Проверяем ДО импорта любых частей бота, где нужны сторонние пакеты.
    from bootstrap import ensure_requirements
    try:
        ensure_requirements()
    except (OSError, RuntimeError) as exc:
        print(f"[Ошибка окружения] {exc}", file=sys.stderr, flush=True)
        return 2

    import logging
    from threading import Thread
    from colorama import Fore, init as init_colorama

    from __init__ import ACCENT_COLOR, VERSION
    from core import bootreport
    from core.utils import (
        acquire_instance_lock, init_main_loop, patch_requests,
        release_instance_locks, set_title, setup_logger,
    )
    from core.modules import get_modules
    from core.handlers import call_bot_event
    from core.startup import (
        diagnose, enter_setup_mode, start_modules,
        start_telegram_bot, start_playerok_bot,
    )
    from updater import check_for_updates, check_new_releases_task
    from utils import configure_config

    logger = logging.getLogger("universal")
    init_colorama(convert=False, strip=not sys.stdout.isatty())

    # Не запускаем два экземпляра из одной директории — это может привести
    # к повторной выдаче товаров и повторной обработке заказов.
    existing_pid = acquire_instance_lock()
    if existing_pid is not None:
        print(f"Бот уже запущен (PID {existing_pid}). Завершите первый экземпляр.", file=sys.stderr)
        return 1

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    init_main_loop(loop)

    try:
        patch_requests()
        setup_logger()
        bootreport.start_capture()
        apply_environment_config()

        set_title(f"Playerok Universal v{VERSION}")
        from core.console import print_panel
        print_panel(
            f"{ACCENT_COLOR}Playerok Universal {Fore.WHITE}v{VERSION}",
            [
                ("Управление", "Telegram"),
                ("Работа", "Playerok"),
                ("Запуск", "bot.py / server.py"),
            ],
            color="yellow", width=72,
        )

        # Не заменяйте исправленный код автоматически, если требуется сохранение
        # этой сборки: для новых установок auto_update по умолчанию выключен.
        if os.environ.get("PLAYEROK_SKIP_UPDATE_CHECK") != "1":
            check_for_updates()
        configure_config()  # валидирует токен Telegram, выводит ссылку владельца

        logger.info("Проверяю подключение Playerok...")
        problem = diagnose()
        if problem:
            # Нет cookies или проблема с сетью: запускаем только Telegram,
            # настройки Playerok пользователь сможет исправить через меню.
            loop.run_until_complete(start_telegram_bot())
            enter_setup_mode(problem)
        else:
            # Все существующие плагины и их события остаются доступными.
            start_modules()
            loop.run_until_complete(start_telegram_bot())
            loop.run_until_complete(start_playerok_bot())
            loop.run_until_complete(call_bot_event("ON_INIT"))
            Thread(target=bootreport.send_report,
                   args=(get_modules(),), daemon=True).start()

        loop.create_task(clear_logs_task(), name="clear_logs")
        loop.create_task(check_new_releases_task(), name="release_notifications")
        loop.run_forever()
        return 0
    except KeyboardInterrupt:
        logger.info("Остановка по Ctrl+C")
        return 0
    except Exception:
        trace = traceback.format_exc()
        logger.exception("Ошибка при запуске или работе бота")
        try:
            bootreport.notify_crash(trace)
        except Exception:
            logger.exception("Не удалось уведомить владельца об ошибке")
        return 1
    finally:
        # Не допускаем утечки lock-файлов после штатной остановки.
        try:
            if not loop.is_closed():
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                loop.close()
        finally:
            release_instance_locks()


async def clear_logs_task() -> None:
    """Ограничивает объём локального файла логов согласно настройкам."""
    from settings import Settings
    path = ROOT / "logs" / "latest.log"
    while True:
        try:
            max_size_mb = Settings.get("config")["logs"]["max_file_size"]
            if max_size_mb > 0 and path.is_file() and path.stat().st_size > max_size_mb * 1024 * 1024:
                # Совместимость с предыдущим поведением: не трогаем прочие логи.
                path.write_text("", encoding="utf-8")
        except (OSError, KeyError, TypeError, ValueError):
            pass  # очистка логов не должна останавливать самого бота
        await asyncio.sleep(30)


if __name__ == "__main__":
    raise SystemExit(main())
