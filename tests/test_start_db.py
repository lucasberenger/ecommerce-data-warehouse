"""Exercise the Bash script with a fake Docker CLI; no real database is used."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/start_db.sh"
FAKE_DOCKER = """#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
with open(os.environ['DOCKER_CALLS'], 'a') as log:
    log.write(json.dumps(args) + '\\n')
if any('pg_isready' in arg for arg in args):
    sys.exit(int(os.environ.get('READY_EXIT', '0')))
if '--tuples-only' in args:
    if os.environ.get('QUERY_FAIL'):
        sys.exit(1)
    print(os.environ.get('TABLE_COUNT', '0'))
if '--single-transaction' in args:
    sys.exit(int(os.environ.get('DDL_EXIT', '0')))
"""


class StartDbTests(unittest.TestCase):
    def run_script(self, **overrides):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docker = root / "docker"
            docker.write_text(FAKE_DOCKER)
            docker.chmod(0o755)
            sleep = root / "sleep"
            sleep.write_text("#!/bin/sh\nexit 0\n")
            sleep.chmod(0o755)
            log = root / "calls.jsonl"
            environment = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}",
                               DOCKER_CALLS=str(log), TABLE_COUNT="0",
                               READY_EXIT="0", DDL_EXIT="0", QUERY_FAIL="")
            environment.update(overrides)
            result = subprocess.run(["bash", str(SCRIPT)], cwd=root,
                                    env=environment, capture_output=True, text=True,
                                    timeout=15)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
        return result, calls

    def test_empty_database_applies_all_files_in_order(self):
        result, calls = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(["compose", "up", "-d", "db"], calls)
        ddl_calls = [call for call in calls if "--single-transaction" in call]
        self.assertEqual(len(ddl_calls), 1)
        self.assertEqual([arg for arg in ddl_calls[0] if arg.startswith('--file=')], [
            '--file=/sql/staging/01_create_schemas.sql',
            '--file=/sql/staging/02_create_staging.sql',
            '--file=/sql/analytics/01_create_schemas.sql',
            '--file=/sql/analytics/02_create_analytics.sql',
        ])

    def test_existing_tables_skip_ddl(self):
        result, calls = self.run_script(TABLE_COUNT="6")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(any('--single-transaction' in call for call in calls))

    def test_partial_structure_stops_without_ddl(self):
        result, calls = self.run_script(TABLE_COUNT="3")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any('--single-transaction' in call for call in calls))

    def test_readiness_timeout_stops_before_psql(self):
        result, calls = self.run_script(READY_EXIT="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(sum(any('pg_isready' in arg for arg in call) for call in calls), 30)
        self.assertFalse(any('--tuples-only' in call for call in calls))

    def test_query_failure_stops_without_ddl(self):
        result, calls = self.run_script(QUERY_FAIL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(any('--single-transaction' in call for call in calls))

    def test_ddl_failure_is_reported(self):
        result, _ = self.run_script(DDL_EXIT="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Tabelas criadas com sucesso.', result.stdout)
