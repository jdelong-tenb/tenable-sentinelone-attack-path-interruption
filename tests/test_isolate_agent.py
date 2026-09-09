#!/usr/bin/env python3
"""
Fixture tests for isolate_agent.py's error handling around the destructive
SentinelOne isolation call. Mocks urllib so no real network call is made.
Pure stdlib, no dependencies.

Usage:
    python3 tests/test_isolate_agent.py
"""
import io
import json
import os
import sys
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import isolate_agent  # noqa: E402


class FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestIsolate(unittest.TestCase):
    def test_isolate_returns_parsed_json_on_success(self):
        with mock.patch("urllib.request.urlopen", return_value=FakeResponse({"data": {"affected": 1}})):
            result = isolate_agent.isolate("https://tenant.sentinelone.net", "tok", "agent-1")
        self.assertEqual(result, {"data": {"affected": 1}})

    def test_isolate_builds_expected_url_and_body(self):
        captured = {}

        def fake_urlopen(req, timeout=30):
            captured["url"] = req.full_url
            captured["body"] = json.loads(req.data)
            captured["auth"] = req.get_header("Authorization")
            return FakeResponse({"ok": True})

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            isolate_agent.isolate("https://tenant.sentinelone.net/", "tok-123", "agent-42")

        self.assertEqual(captured["url"], "https://tenant.sentinelone.net/web/api/v2.1/agents/actions/disconnect")
        self.assertEqual(captured["body"], {"filter": {"ids": ["agent-42"]}})
        self.assertEqual(captured["auth"], "ApiToken tok-123")


class TestMainErrorHandling(unittest.TestCase):
    def _run_main(self, argv, env):
        with mock.patch.object(sys, "argv", ["isolate_agent.py"] + argv), \
             mock.patch.dict(os.environ, env, clear=False), \
             mock.patch("sys.stdout", new_callable=io.StringIO), \
             mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            try:
                isolate_agent.main()
            except SystemExit as e:
                return e.code, err.getvalue()
            return 0, err.getvalue()

    def test_dry_run_without_confirm_makes_no_call(self):
        with mock.patch("isolate_agent.isolate") as fake_isolate:
            code, _ = self._run_main(["agent-1", "--reason", "test"], {})
        fake_isolate.assert_not_called()
        self.assertEqual(code, 0)

    def test_confirm_without_env_vars_exits_nonzero(self):
        env = {}
        with mock.patch.dict(os.environ, env, clear=True):
            code, err = self._run_main(["agent-1", "--reason", "test", "--confirm"], {})
        self.assertNotEqual(code, 0)
        self.assertIn("SENTINELONE_CONSOLE_URL", err)

    def test_http_error_reported_and_exits_nonzero(self):
        env = {"SENTINELONE_CONSOLE_URL": "https://tenant.sentinelone.net", "SENTINELONE_API_TOKEN": "tok"}
        http_err = urllib.error.HTTPError(
            "https://tenant.sentinelone.net/web/api/v2.1/agents/actions/disconnect",
            403,
            "Forbidden",
            {},
            io.BytesIO(b'{"error":"forbidden"}'),
        )
        with mock.patch("isolate_agent.isolate", side_effect=http_err):
            code, err = self._run_main(["agent-1", "--reason", "test", "--confirm"], env)
        self.assertNotEqual(code, 0)
        self.assertIn("FAILED", err)
        self.assertIn("403", err)
        self.assertIn("Verify the agent's connectivity status", err)

    def test_url_error_reported_and_exits_nonzero(self):
        env = {"SENTINELONE_CONSOLE_URL": "https://tenant.sentinelone.net", "SENTINELONE_API_TOKEN": "tok"}
        with mock.patch("isolate_agent.isolate", side_effect=urllib.error.URLError("no route")):
            code, err = self._run_main(["agent-1", "--reason", "test", "--confirm"], env)
        self.assertNotEqual(code, 0)
        self.assertIn("network error", err)

    def test_bad_json_response_reported_and_exits_nonzero(self):
        env = {"SENTINELONE_CONSOLE_URL": "https://tenant.sentinelone.net", "SENTINELONE_API_TOKEN": "tok"}
        with mock.patch("isolate_agent.isolate", side_effect=ValueError("not json")):
            code, err = self._run_main(["agent-1", "--reason", "test", "--confirm"], env)
        self.assertNotEqual(code, 0)
        self.assertIn("could not parse", err)

    def test_success_prints_result_without_claiming_proof(self):
        env = {"SENTINELONE_CONSOLE_URL": "https://tenant.sentinelone.net", "SENTINELONE_API_TOKEN": "tok"}
        with mock.patch("isolate_agent.isolate", return_value={"data": {"affected": 1}}), \
             mock.patch.object(sys, "argv", ["isolate_agent.py", "agent-1", "--reason", "test", "--confirm"]), \
             mock.patch.dict(os.environ, env, clear=False), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            try:
                isolate_agent.main()
            except SystemExit:
                pass
        self.assertIn("Do not treat this response alone as proof", out.getvalue())


if __name__ == "__main__":
    unittest.main()
