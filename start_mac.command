#!/bin/bash

chmod +x "$0" 2>/dev/null

cd "$(dirname "$0")"

echo ""
echo "🚀 Запуск Playerok Universal..."
echo ""

$(command -v python3.12 || command -v python3) server.py
STATUS=$?

echo ""
if [ $STATUS -ne 0 ]; then
  read -n 1 -s -r -p "Нажмите любую клавишу для выхода..."
fi
