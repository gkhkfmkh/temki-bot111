#!/usr/bin/env bash
# Publish the complete project at repository root via Git (Linux/macOS).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO='https://github.com/gkhkfmkh/playerok_universal_fixed.git'
for path in server.py bot.py requirements.txt tgbot core playerokapi; do
  if [[ ! -e "$ROOT/$path" ]]; then echo "Missing $path: extract the whole ZIP" >&2; exit 1; fi
done
command -v git >/dev/null || { echo 'Install git first' >&2; exit 1; }
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
# Use a real temporary path that does not exist for git clone.
rmdir "$TMP"
git clone "$REPO" "$TMP"
# Only delete files in temporary clone; original files remain untouched.
find "$TMP" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf -- {} +
# Copy source, excluding environment-specific and secret runtime data.
for path in "$ROOT"/* "$ROOT"/.[!.]* "$ROOT"/..?*; do
  [[ -e "$path" ]] || continue
  name="$(basename "$path")"
  case "$name" in .git|.env|.venv|venv|__pycache__|bot_settings|bot_data|modules|logs|.temp|.idea|.vscode) continue ;; esac
  cp -a "$path" "$TMP/$name"
done
git -C "$TMP" add -A
if git -C "$TMP" diff --cached --quiet; then
  echo 'No changes; repository already up to date.'
  exit 0
fi
git -C "$TMP" commit -m 'Deploy Playerok Universal at repository root'
git -C "$TMP" push origin HEAD:main
echo 'SUCCESS. Hosting startup filename: server.py'
