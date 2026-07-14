from __future__ import annotations

import ast
import inspect
import textwrap
import unittest

from hpr.gui.app import HostedPlayersReportApp


class GuiErrorLoggingTests(unittest.TestCase):
    def test_worker_and_callback_error_log_calls_preserve_exc_info(self) -> None:
        for method_name in ("_handoff_error", "_build_error", "_show_error", "report_callback_exception"):
            with self.subTest(method=method_name):
                source = textwrap.dedent(inspect.getsource(getattr(HostedPlayersReportApp, method_name)))
                tree = ast.parse(source)
                log_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and _is_self_log_call(node)]
                self.assertGreater(len(log_calls), 0, method_name)
                for call in log_calls:
                    self.assertTrue(
                        any(keyword.arg == "exc_info" for keyword in call.keywords),
                        f"{method_name} log call is missing exc_info",
                    )


def _is_self_log_call(node: ast.Call) -> bool:
    if not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr not in {"debug", "info", "warning", "error", "exception", "critical"}:
        return False
    receiver = node.func.value
    return (
        isinstance(receiver, ast.Attribute)
        and receiver.attr == "log"
        and isinstance(receiver.value, ast.Name)
        and receiver.value.id == "self"
    )


if __name__ == "__main__":
    unittest.main()
