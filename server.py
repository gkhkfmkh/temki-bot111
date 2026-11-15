"""Точка входа для Linux-хостингов, ожидающих /app/server.py.

Это Telegram/Playerok worker, а не HTTP-сервер. На веб-хостинге выберите
Background Worker (без требования отвечать на HTTP-запросы).
"""
from bot import main

if __name__ == "__main__":
    raise SystemExit(main())
