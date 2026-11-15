#!/usr/bin/env sh
# Installs only local dependencies. Never downloads new application sources.
set -eu
cd "$(dirname "$0")"
if command -v python3.12 >/dev/null 2>&1; then PY=python3.12; else PY=python3; fi
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)'; then
    echo "Required Python 3.12.x; found: $("$PY" --version)" >&2
    exit 2
fi
if [ ! -x .venv/bin/python ]; then "$PY" -m venv .venv; fi
.venv/bin/python -m pip install -r requirements.txt
printf '
Start bot: .venv/bin/python server.py
'
