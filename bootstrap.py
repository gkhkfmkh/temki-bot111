"""Проверка Python и зависимостей до импортов ядра бота.

На хостинге зависимости устанавливаются при сборке (Dockerfile/Build Command).
На домашнем ПК интерактивный запуск может установить недостающие библиотеки.
"""
from __future__ import annotations

import importlib
import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def missing_requirements(path: Path) -> list[str]:
    try:
        from packaging.requirements import Requirement
    except ImportError:
        return ["packaging"]
    if not path.exists():
        return [f"не найден {path.name}"]
    missing: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        try:
            requirement = Requirement(line)
            if requirement.marker and not requirement.marker.evaluate():
                continue
            version = importlib.metadata.version(requirement.name)
            if requirement.specifier and version not in requirement.specifier:
                missing.append(f"{requirement.name} ({version}, требуется {requirement.specifier})")
        except importlib.metadata.PackageNotFoundError:
            missing.append(requirement.name)
        except ValueError as exc:
            missing.append(f"{line}: {exc}")
    return missing


def ensure_requirements() -> None:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError(
            f"Нужен Python 3.12.x, установлен {sys.version.split()[0]}. "
            "Для Docker используйте приложенный Dockerfile."
        )

    missing = missing_requirements(ROOT / "requirements.txt")
    if not missing:
        return

    auto = os.environ.get("PLAYEROK_AUTO_INSTALL")
    allow_install = (auto == "1") or (auto is None and sys.stdin.isatty())
    if not allow_install:
        raise RuntimeError(
            "Не установлены зависимости: " + ", ".join(missing) + ". "
            "Установите при сборке: python -m pip install -r requirements.txt"
        )

    print("[Установка библиотек] " + ", ".join(missing), flush=True)
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r",
            str(ROOT / "requirements.txt"),
        ])
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            "Установка зависимостей не удалась. "
            "Проверьте интернет, права и Python 3.12."
        ) from exc
    importlib.invalidate_caches()
    remains = missing_requirements(ROOT / "requirements.txt")
    if remains:
        raise RuntimeError("Библиотеки всё ещё отсутствуют: " + ", ".join(remains))
