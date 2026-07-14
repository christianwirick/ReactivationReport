from __future__ import annotations

import unittest

from hpr.gui.run_jobs import ProgressController


class _FakeOwner:
    def __init__(self) -> None:
        self.callbacks = []

    def winfo_exists(self) -> bool:
        return True

    def after(self, _delay_ms, callback):
        self.callbacks.append(callback)


class _FakeVar:
    def __init__(self) -> None:
        self.value = ""

    def set(self, value) -> None:
        self.value = value


class _FakeProgress:
    def __init__(self) -> None:
        self.values: list[float] = []

    def set_value(self, value: float) -> None:
        self.values.append(value)

    def pack(self, **_kwargs) -> None:
        pass

    def pack_forget(self) -> None:
        pass


class _FakeWidget:
    def pack_forget(self) -> None:
        pass


class GuiProgressTests(unittest.TestCase):
    def test_progress_fills_once_and_does_not_wrap_while_pending(self) -> None:
        progress = _FakeProgress()
        controller = ProgressController(
            _FakeOwner(),
            status_var=_FakeVar(),
            progress=progress,
            percent_var=_FakeVar(),
            percent_label=_FakeWidget(),
            tick_ms=33,
            progress_step=25,
            finish_step=25,
        )

        controller.set_busy(True, "Working")
        for _ in range(10):
            controller._tick()

        self.assertEqual(progress.values[0], 0)
        self.assertEqual(progress.values.count(0), 1)
        self.assertEqual(progress.values[-1], 96.0)
        self.assertEqual(progress.values, sorted(progress.values))

    def test_finish_runs_callback_after_reaching_one_hundred(self) -> None:
        progress = _FakeProgress()
        controller = ProgressController(
            _FakeOwner(),
            status_var=_FakeVar(),
            progress=progress,
            percent_var=_FakeVar(),
            percent_label=_FakeWidget(),
            tick_ms=33,
            progress_step=50,
            finish_step=50,
        )
        completed: list[bool] = []

        controller.set_busy(True, "Working")
        controller.finish(lambda: completed.append(True))
        for _ in range(3):
            controller._tick()

        self.assertEqual(progress.values[-1], 100.0)
        self.assertEqual(completed, [True])


if __name__ == "__main__":
    unittest.main()
