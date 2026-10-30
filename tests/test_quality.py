"""Test quality checks with mocked connections and an in-memory SQLite database."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql.elements import TextClause

from ecommerce_data_warehouse.quality import read_checks, validate_query


class ReadChecksTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "checks.sql"

    def read_content(self, content):
        self.path.write_text(content, encoding="utf-8")
        return read_checks(self.path)

    def test_single_check_without_final_newline_is_preserved(self):
        self.assertEqual(
            self.read_content("-- check: only\nSELECT 1;"),
            [("only", "SELECT 1;")],
        )

    def test_multiple_checks_preserve_order_and_multiline_sql(self):
        content = (
            "-- check: first\nSELECT id\nFROM example\nWHERE id IS NULL;\n\n"
            "-- check: second\nSELECT 2;\n"
        )
        self.assertEqual(self.read_content(content), [
            ("first", "SELECT id\nFROM example\nWHERE id IS NULL;"),
            ("second", "SELECT 2;"),
        ])

    def test_leading_blank_lines_and_title_whitespace_are_allowed(self):
        self.assertEqual(
            self.read_content("\n \t\n-- check:  first \t\nSELECT 1;\n"),
            [("first", "SELECT 1;")],
        )

    def test_utf8_content_and_sql_semicolons_are_preserved(self):
        self.assertEqual(
            self.read_content("-- check: descrição\nSELECT 'ação; revisão';\n"),
            [("descrição", "SELECT 'ação; revisão';")],
        )

    def test_empty_name_is_rejected_at_first_or_later_marker(self):
        for previous in ["", "-- check: valid\nSELECT 1;\n"]:
            with self.subTest(previous=previous):
                with self.assertRaisesRegex(ValueError, "Missing title"):
                    self.read_content(previous + "-- check: \t\nSELECT 2;\n")

    def test_duplicate_names_are_rejected_after_trimming(self):
        with self.assertRaisesRegex(ValueError, "Duplicated title.*first"):
            self.read_content(
                "-- check: first\nSELECT 1;\n-- check:  first \t\nSELECT 2;\n"
            )

    def test_empty_sql_is_rejected_between_markers_and_at_end(self):
        for suffix in ["", "-- check: valid\nSELECT 1;\n"]:
            for whitespace in ["", " \t\n"]:
                with self.subTest(suffix=suffix, whitespace=whitespace):
                    with self.assertRaisesRegex(ValueError, "Empty query for empty_check"):
                        self.read_content("-- check: empty_check\n" + whitespace + suffix)

    def test_content_before_first_marker_is_rejected(self):
        for content in ["SELECT 99;", "WITH example AS (SELECT 1)", "-- unmarked comment"]:
            with self.subTest(content=content):
                with self.assertRaisesRegex(ValueError, "before the first check"):
                    self.read_content(content + "\n-- check: valid\nSELECT 1;\n")

    def test_sql_without_markers_is_rejected(self):
        with self.assertRaises(ValueError):
            self.read_content("SELECT 1;\n")

    def test_empty_and_whitespace_only_files_are_rejected_with_path(self):
        for content in ["", "\n \t\n"]:
            with self.subTest(content=content):
                with self.assertRaises(ValueError) as raised:
                    self.read_content(content)
                self.assertIn(str(self.path), str(raised.exception))

    def test_missing_file_error_propagates(self):
        with self.assertRaises(FileNotFoundError):
            read_checks(self.path)


class ValidateQueryTests(unittest.TestCase):
    def setUp(self):
        self.connection = Mock(spec=Connection)

    def test_no_rows_passes_using_the_provided_connection(self):
        self.connection.execute.return_value.first.return_value = None

        result = validate_query(self.connection, "  SELECT 1 WHERE 1 = 0\n", "empty check")

        self.assertIsNone(result)
        self.connection.execute.assert_called_once()
        statement = self.connection.execute.call_args.args[0]
        self.assertIsInstance(statement, TextClause)
        self.assertEqual(str(statement), "SELECT 1 WHERE 1 = 0")
        self.connection.execute.return_value.first.assert_called_once_with()
        self.connection.begin.assert_not_called()
        self.connection.commit.assert_not_called()
        self.connection.rollback.assert_not_called()

    def test_any_row_is_a_violation_even_when_its_value_is_null_or_zero(self):
        for row in [(None,), (0,), ("duplicate",)]:
            with self.subTest(row=row):
                self.connection.execute.return_value.first.return_value = row
                with self.assertRaisesRegex(ValueError, "duplicate customer keys"):
                    validate_query(self.connection, "SELECT 1", " duplicate customer keys ")

    def test_empty_query_is_rejected_before_execution(self):
        for query in ["", "   ", "\n\t"]:
            with self.subTest(query=query):
                with self.assertRaisesRegex(ValueError, "Query is missing"):
                    validate_query(self.connection, query, "check")
        self.connection.execute.assert_not_called()

    def test_empty_check_name_is_rejected_before_execution(self):
        for name in ["", "   ", "\n\t"]:
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "Check name is missing"):
                    validate_query(self.connection, "SELECT 1", name)
        self.connection.execute.assert_not_called()

    def test_sql_error_propagates_unchanged(self):
        error = OperationalError("SELECT invalid", {}, RuntimeError("database error"))
        self.connection.execute.side_effect = error

        with self.assertRaises(OperationalError) as raised:
            validate_query(self.connection, "SELECT invalid", "broken check")

        self.assertIs(raised.exception, error)
        self.connection.commit.assert_not_called()
        self.connection.rollback.assert_not_called()


class ValidateQuerySQLiteTests(unittest.TestCase):
    """Exercise actual SQLAlchemy execution; this does not validate PostgreSQL SQL files."""

    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        self.addCleanup(self.engine.dispose)

    def test_select_without_rows_passes(self):
        with self.engine.begin() as connection:
            self.assertIsNone(validate_query(connection, "SELECT 1 WHERE 1 = 0", "no violations"))
            self.assertTrue(connection.in_transaction())

    def test_select_with_row_raises(self):
        with self.engine.begin() as connection:
            with self.assertRaisesRegex(ValueError, "unexpected row"):
                validate_query(connection, "SELECT NULL", "unexpected row")

    def test_invalid_sql_raises_database_error(self):
        with self.engine.begin() as connection:
            with self.assertRaises(OperationalError):
                validate_query(connection, "SELECT FROM", "invalid SQL")
