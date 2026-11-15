FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYEROK_AUTO_INSTALL=0

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . ./

# Бот работает через Telegram polling: HTTP-порт ему не требуется.
CMD ["python", "server.py"]
