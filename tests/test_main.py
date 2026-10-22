"""Test ingestion orchestration without importing database dependencies."""

import importlib
import sys
import types
import unittest
from unittest.mock import Mock, patch


class MainTests(unittest.TestCase):
    def setUp(self):
        # Replace only the ingestion boundary; no pandas, SQLAlchemy or DB required.
        pipeline = types.ModuleType("ecommerce_data_warehouse.pipeline")
        pipeline.execute_pipeline = Mock()
        with patch.dict(sys.modules, {pipeline.__name__: pipeline}):
            self.module = importlib.import_module("ecommerce_data_warehouse.main")

        self.datasets = {
            "customers": {"table": "customers", "file": "customers.csv"},
            "orders": {"table": "orders", "file": "orders.csv"},
        }
        self.execute = Mock()
        self.logger = Mock()
        for name, value in (
            ("DATASETS", self.datasets),
            ("execute_pipeline", self.execute),
            ("logger", self.logger),
        ):
            patcher = patch.object(self.module, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_success_returns_zero_and_reports_each_count(self):
        self.execute.side_effect = [12, 34]

        self.assertEqual(self.module.main(), 0)

        self.logger.warning.assert_not_called()
        self.logger.info.assert_any_call('Pipeline finished successfully.')
        self.assert_summary("customers", "SUCCESS", 12)
        self.assert_summary("orders", "SUCCESS", 34)

    def test_first_failure_returns_one_and_continues(self):
        error = RuntimeError("source unavailable")
        self.execute.side_effect = [error, 34]

        self.assertEqual(self.module.main(), 1)

        self.assert_summary("customers", "FAILED", 0)
        self.assert_summary("orders", "SUCCESS", 34)
        self.assertEqual(self.execute.call_args_list, [
            unittest.mock.call(dataset=dataset)
            for dataset in self.datasets.values()
        ])
        self.logger.exception.assert_called_once_with("Failed to load %s", "customers")
        self.logger.warning.assert_called_once_with('Pipeline finished with failures.')

    def test_failure_after_success_does_not_reuse_previous_count(self):
        self.execute.side_effect = [12, RuntimeError("load failed")]

        self.assertEqual(self.module.main(), 1)

        self.assert_summary("customers", "SUCCESS", 12)
        self.assert_summary("orders", "FAILED", 0)
        self.logger.warning.assert_called_once_with('Pipeline finished with failures.')

    def test_all_failures_are_reported(self):
        self.execute.side_effect = [RuntimeError("first"), RuntimeError("second")]

        self.assertEqual(self.module.main(), 1)

        self.assertEqual(self.execute.call_count, 2)
        self.assertEqual(self.logger.exception.call_count, 2)
        self.assert_summary("customers", "FAILED", 0)
        self.assert_summary("orders", "FAILED", 0)

    def assert_summary(self, table, status, rows):
        self.logger.info.assert_any_call("%-15s %-8s %d rows", table, status, rows)


if __name__ == "__main__":
    unittest.main()
