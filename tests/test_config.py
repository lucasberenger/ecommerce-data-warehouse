"""Check configuration defaults and environment overrides without loading secrets."""

import importlib.util
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class ConfigTests(unittest.TestCase):
    def load_settings(self, environment):
        dotenv = types.ModuleType("dotenv")
        dotenv.load_dotenv = Mock()
        path = Path(__file__).resolve().parents[1] / "src/ecommerce_data_warehouse/config.py"
        spec = importlib.util.spec_from_file_location("_test_config", path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, environment, clear=True), patch.dict(
            sys.modules, {"dotenv": dotenv, spec.name: module}
        ):
            spec.loader.exec_module(module)
        dotenv.load_dotenv.assert_called_once_with()
        return module.settings

    def test_local_defaults(self):
        settings = self.load_settings({})

        self.assertEqual(settings.postgres_host, "localhost")
        self.assertEqual(settings.postgres_port, 5432)
        self.assertEqual(settings.postgres_db, "ecomm_db")
        self.assertEqual(settings.postgres_user, "ecomm_admin")
        self.assertEqual(settings.postgres_password, "ecomm_passwd")

    def test_environment_overrides_all_defaults(self):
        settings = self.load_settings({
            "POSTGRES_HOST": "db.example",
            "POSTGRES_PORT": "5433",
            "POSTGRES_DB": "test_db",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_password",
        })

        self.assertEqual(settings.postgres_host, "db.example")
        self.assertEqual(settings.postgres_port, 5433)
        self.assertEqual(settings.postgres_db, "test_db")
        self.assertEqual(settings.postgres_user, "test_user")
        self.assertEqual(settings.postgres_password, "test_password")
