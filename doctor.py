"""Оффлайн-проверка структуры и зависимостей. Запуск: python server.py --doctor."""
from __future__ import annotations
import ast
from pathlib import Path
import sys

from bootstrap import missing_requirements

ROOT = Path(__file__).resolve().parent
ENTRYPOINTS = ("server.py", "bot.py", "start.bat", "start.sh", "requirements.txt")


def main() -> int:
    print(f"[Python] {sys.version.split()[0]} ({sys.executable})")
    print(f"[Корень] {ROOT}")
    errors = []
    for path in ENTRYPOINTS:
        if not (ROOT / path).is_file():
            errors.append(f"Отсутствует обязательный файл: {path}")
    count = 0
    for path in ROOT.rglob("*.py"):
        if any(x in ("__pycache__", ".venv", "venv") for x in path.relative_to(ROOT).parts):
            continue
        count += 1
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")
    print(f"[Код] Проверено файлов: {count}; синтаксических ошибок: {len(errors)}")
    for err in errors:
        print(f"[ОШИБКА] {err}")
    if sys.version_info[:2] != (3, 12):
        print("[ПРЕДУПРЕЖДЕНИЕ] Рекомендуется Python 3.12.x")
    missing = missing_requirements(ROOT / "requirements.txt")
    if missing:
        print("[Зависимости] Требуют установки:", ", ".join(missing))
        print("  python -m pip install -r requirements.txt")
    else:
        print("[Зависимости] OK")
    print("[Важно] API Playerok и Telegram без действительных данных здесь не проверяются.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
