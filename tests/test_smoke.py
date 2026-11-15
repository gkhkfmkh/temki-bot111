"""Автономные smoke-тесты — не обращаются к Telegram или Playerok."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class StartupSmokeTests(unittest.TestCase):
    def test_required_entrypoints(self):
        self.assertTrue((ROOT / "server.py").is_file())
        self.assertTrue((ROOT / "bot.py").is_file())
        self.assertIn('CMD ["python", "server.py"]', (ROOT / "Dockerfile").read_text("utf-8"))

    def test_doctor_exits_normally_without_credentials(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "server.py"), "--doctor"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=25,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("синтаксических ошибок: 0", result.stdout)

    def test_noninteractive_env_configuration(self):
        spec = importlib.util.spec_from_file_location("standalone_playerok", ROOT / "bot.py")
        bot = importlib.util.module_from_spec(spec)
        assert spec.loader
        spec.loader.exec_module(bot)
        sys.path.insert(0, str(ROOT))
        from settings import Settings

        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {
                "TELEGRAM_BOT_TOKEN": "123456:fake-token-not-for-network",
                "PLAYEROK_COOKIES": "token=fake==; other=123",
            }, clear=False):
                old_cwd = Path.cwd()
                try:
                    os.chdir(tmp)
                    bot.apply_environment_config()
                    config = Settings.get("config")
                    self.assertEqual(
                        config["telegram"]["api"]["token"],
                        "123456:fake-token-not-for-network",
                    )
                    self.assertEqual(
                        config["playerok"]["api"]["cookies"],
                        "token=fake==; other=123",
                    )
                    self.assertTrue((Path(tmp) / "bot_settings" / "config.json").is_file())
                finally:
                    os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
