"""Test transaction orchestration with a simulated engine, not PostgreSQL."""

from contextlib import contextmanager
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


class Frame(list):
    @property
    def empty(self):
        return not self


class TransactionEngine:
    """Minimal transaction double: publish changes only on successful exit."""

    def __init__(self, state):
        self.state = deepcopy(state)
        self.begins = 0
        self.fail_commit = False

    @contextmanager
    def begin(self):
        self.begins += 1
        pending = deepcopy(self.state)
        yield pending
        if self.fail_commit:
            raise RuntimeError('commit failed')
        self.state = pending


def isolated_module(filename, dependencies):
    path = Path(__file__).resolve().parents[1] / 'src/ecommerce_data_warehouse' / filename
    spec = importlib.util.spec_from_file_location('_test_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, dependencies):
        spec.loader.exec_module(module)
    return module


class PipelineTests(unittest.TestCase):
    def setUp(self):
        from ecommerce_data_warehouse.datasets import DATASETS
        self.datasets = DATASETS
        self.initial = {d['table']: ['old'] for d in DATASETS.values()}
        self.initial['analytics.dim_customers'] = ['untouched']
        self.engine = TransactionEngine(self.initial)
        self.events = []
        self.frames = {d['file']: Frame([d['table'], 'new']) for d in DATASETS.values()}
        self.failure_table = None

        def truncate(table_name, connection):
            self.events.append(('truncate', table_name, connection))
            connection[table_name] = []

        def load(df, table_name, connection):
            self.events.append(('load', table_name, connection))
            # Simulate a partial write before failure.
            connection[table_name].extend(df)
            if table_name == self.failure_table:
                raise RuntimeError('insert failed')
            return len(df)

        dependencies = {}
        for name, attributes in {
            'database': {'engine': self.engine},
            'extract': {'read_csv': Mock(side_effect=lambda filename: self.frames[filename])},
            'load': {'truncate_table': Mock(side_effect=truncate), 'load_dataframe': Mock(side_effect=load)},
            'transform': {'transform_dataframe': Mock(side_effect=lambda df, table: df)},
            'validation': {'validate_dataframe': Mock()},
        }.items():
            module = types.ModuleType('ecommerce_data_warehouse.' + name)
            module.__dict__.update(attributes)
            dependencies[module.__name__] = module
        self.pipeline = isolated_module('pipeline.py', dependencies)
        self.pipeline.logger = Mock()

    def run_pipeline(self):
        return self.pipeline.execute_pipeline(self.datasets)

    def test_repeat_load_preserves_content_and_counts(self):
        first = self.run_pipeline()
        state = deepcopy(self.engine.state)
        second = self.run_pipeline()
        self.assertEqual(self.engine.state, state)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 5)
        self.assertTrue(all(result.rows == 2 for result in first))
        self.assertEqual(self.engine.state['analytics.dim_customers'], ['untouched'])

    def test_all_operations_share_one_connection(self):
        self.run_pipeline()
        self.assertEqual(self.engine.begins, 1)
        self.assertEqual([e[0] for e in self.events], ['truncate'] * 5 + ['load'] * 5)
        connection = self.events[0][2]
        self.assertTrue(all(event[2] is connection for event in self.events))

    def test_middle_failure_preserves_previous_load_and_stops(self):
        self.failure_table = 'order_items'
        with self.assertRaisesRegex(RuntimeError, 'insert failed'):
            self.run_pipeline()
        self.assertEqual(self.engine.state, self.initial)
        self.assertEqual([e[1] for e in self.events if e[0] == 'load'],
                         ['customers', 'orders', 'order_items'])

    def test_first_load_failure_keeps_tables_empty(self):
        self.engine.state = {table: [] for table in self.initial}
        before = deepcopy(self.engine.state)
        self.failure_table = 'order_items'
        with self.assertRaises(RuntimeError):
            self.run_pipeline()
        self.assertEqual(self.engine.state, before)

    def test_validation_failure_never_opens_transaction(self):
        self.pipeline.validate_dataframe.side_effect = [None] * 4 + [ValueError('bad columns')]
        with self.assertRaises(ValueError):
            self.run_pipeline()
        self.assertEqual(self.engine.begins, 0)
        self.assertEqual(self.engine.state, self.initial)

    def test_extraction_failure_never_opens_transaction(self):
        self.pipeline.read_csv.side_effect = FileNotFoundError('missing CSV')
        with self.assertRaises(FileNotFoundError):
            self.run_pipeline()
        self.assertEqual(self.engine.begins, 0)

    def test_truncate_failure_preserves_state_and_prevents_inserts(self):
        self.pipeline.truncate_table.side_effect = RuntimeError('truncate failed')
        with self.assertRaisesRegex(RuntimeError, 'truncate failed'):
            self.run_pipeline()
        self.assertEqual(self.engine.state, self.initial)
        self.pipeline.load_dataframe.assert_not_called()

    def test_empty_last_file_never_opens_transaction(self):
        self.frames['olist_order_payments_dataset.csv'] = Frame()
        with self.assertRaisesRegex(ValueError, 'empty'):
            self.run_pipeline()
        self.assertEqual(self.engine.begins, 0)

    def test_commit_failure_propagates(self):
        self.engine.fail_commit = True
        with self.assertRaisesRegex(RuntimeError, 'commit failed'):
            self.run_pipeline()
        self.assertEqual(self.engine.state, self.initial)


class LoadTests(unittest.TestCase):
    def setUp(self):
        pandas = types.ModuleType('pandas')
        pandas.DataFrame = Mock
        sqlalchemy = types.ModuleType('sqlalchemy')
        sqlalchemy.text = lambda sql: sql
        engine_module = types.ModuleType('sqlalchemy.engine')
        engine_module.Connection = Mock
        self.load = isolated_module('load.py', {
            'pandas': pandas, 'sqlalchemy': sqlalchemy, 'sqlalchemy.engine': engine_module,
        })

    def test_to_sql_receives_transaction_connection(self):
        # Use a real sequence for len(), with a mocked to_sql boundary.
        df = Frame(['row'])
        df.to_sql = Mock()
        connection = Mock()
        self.assertEqual(self.load.load_dataframe(df, 'orders', connection), 1)
        self.assertIs(df.to_sql.call_args.kwargs['con'], connection)
        self.assertEqual(df.to_sql.call_args.kwargs['if_exists'], 'append')

    def test_empty_frame_is_not_inserted(self):
        df = Frame()
        df.to_sql = Mock()
        with self.assertRaisesRegex(ValueError, 'empty'):
            self.load.load_dataframe(df, 'orders', Mock())
        df.to_sql.assert_not_called()

    def test_truncate_uses_provided_connection(self):
        connection = Mock()
        preparer = connection.dialect.identifier_preparer
        preparer.quote_schema.side_effect = lambda name: '"' + name + '"'
        preparer.quote.side_effect = lambda name: '"' + name + '"'
        self.load.truncate_table('orders', connection)
        connection.execute.assert_called_once_with('TRUNCATE TABLE "staging"."orders";')
