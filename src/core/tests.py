import os
import stat
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from django.test import SimpleTestCase

from core.launcher import default_data_dir, prepare_environment

ENV_KEYS = (
    "PFASIMPLU_DATA_DIR",
    "PFASIMPLU_DB_DIR",
    "PFASIMPLU_MEDIA_ROOT",
    "PFASIMPLU_LOG_DIR",
    "PFASIMPLU_STATIC_ROOT",
    "PFASIMPLU_SECRET_KEY",
    "PFASIMPLU_DEBUG",
    "PFASIMPLU_ALLOWED_HOSTS",
    "PFASIMPLU_SECURE_COOKIES",
    "XDG_DATA_HOME",
    "LOCALAPPDATA",
    "APPDATA",
)


class LauncherTests(SimpleTestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ, {}, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)
        for key in ENV_KEYS:
            os.environ.pop(key, None)

    def test_prepare_environment_sets_data_paths(self):
        with TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "PFASimplu"
            paths = prepare_environment(data_dir)

            self.assertEqual(paths["db"], data_dir / "db")
            self.assertEqual(os.environ["PFASIMPLU_DB_DIR"], str(data_dir / "db"))
            self.assertEqual(
                os.environ["PFASIMPLU_MEDIA_ROOT"], str(data_dir / "files")
            )
            self.assertEqual(os.environ["PFASIMPLU_LOG_DIR"], str(data_dir / "logs"))
            self.assertEqual(
                os.environ["PFASIMPLU_STATIC_ROOT"], str(data_dir / "staticfiles")
            )
            self.assertEqual(os.environ["PFASIMPLU_DEBUG"], "0")
            self.assertEqual(
                os.environ["PFASIMPLU_ALLOWED_HOSTS"], "127.0.0.1,localhost"
            )
            self.assertEqual(os.environ["PFASIMPLU_SECURE_COOKIES"], "0")
            for path in paths.values():
                self.assertTrue(path.is_dir())

    def test_secret_key_is_persisted_and_reused(self):
        with TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "PFASimplu"
            prepare_environment(data_dir)
            secret_file = data_dir / "secret_key"
            secret = secret_file.read_text(encoding="utf-8").strip()

            self.assertGreaterEqual(len(secret), 48)
            self.assertEqual(os.environ["PFASIMPLU_SECRET_KEY"], secret)
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(secret_file.stat().st_mode), 0o600)

            os.environ.pop("PFASIMPLU_SECRET_KEY")
            prepare_environment(data_dir)
            self.assertEqual(os.environ["PFASIMPLU_SECRET_KEY"], secret)
            self.assertEqual(secret_file.read_text(encoding="utf-8").strip(), secret)

    def test_data_dir_honors_explicit_override(self):
        os.environ["PFASIMPLU_DATA_DIR"] = "/tmp/pfasimplu-test"
        self.assertEqual(default_data_dir(), Path("/tmp/pfasimplu-test"))

    def test_data_dir_uses_platform_location(self):
        with mock.patch("core.launcher.sys.platform", "linux"):
            os.environ["XDG_DATA_HOME"] = "/tmp/xdg"
            self.assertEqual(default_data_dir(), Path("/tmp/xdg/pfasimplu"))

        with mock.patch("core.launcher.sys.platform", "win32"):
            os.environ["LOCALAPPDATA"] = "/tmp/localappdata"
            self.assertEqual(
                default_data_dir(), Path("/tmp/localappdata") / "PFASimplu"
            )
