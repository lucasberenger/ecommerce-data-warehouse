"""Check CLI reporting without importing database dependencies."""

import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

from ecommerce_data_warehouse.types import PipelineResponse, PipelineStatus


class MainTests(unittest.TestCase):
    def setUp(self):
        pipeline = types.ModuleType('ecommerce_data_warehouse.pipeline')
        pipeline.execute_pipeline = Mock()
        path = Path(__file__).resolve().parents[1] / 'src/ecommerce_data_warehouse/main.py'
        spec = importlib.util.spec_from_file_location('_test_main', path)
        self.module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {pipeline.__name__: pipeline}):
            spec.loader.exec_module(self.module)
        self.execute = pipeline.execute_pipeline
        self.logger = Mock()
        self.module.logger = self.logger

    def test_reports_success_after_pipeline_returns(self):
        self.execute.return_value = [PipelineResponse('customers', PipelineStatus.SUCCESS, 12)]
        self.assertEqual(self.module.main(), 0)
        self.execute.assert_called_once_with(datasets=self.module.DATASETS)
        self.logger.info.assert_any_call('Staging refresh committed successfully.')
        self.logger.info.assert_any_call('%-15s %-8s %d rows', 'customers', 'SUCCESS', 12)
        self.logger.exception.assert_not_called()

    def test_failure_returns_nonzero_without_success_summary(self):
        self.execute.side_effect = RuntimeError('load failed')
        self.assertEqual(self.module.main(), 1)
        self.logger.exception.assert_called_once()
        self.assertFalse(any('SUCCESS' in call.args for call in self.logger.info.call_args_list))
        self.assertFalse(any('committed successfully' in str(call) for call in self.logger.info.call_args_list))
