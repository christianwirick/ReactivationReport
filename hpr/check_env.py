"""Checks the Hosted Players Report runtime environment.

Runs a suite of checks — interpreter discovery, required imports,
directory permissions, and optional Excel COM readiness — and reports the
results as text or JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from hpr._version import __version__ as __version__
from hpr.settings import APP_DIR_NAME, app_data_dir, default_output_folder

MIN_PYTHON = (3, 11)


@dataclass(frozen=True)
class PythonCandidate:
    executable: str
    source: str
    args: tuple[str, ...] = ()

    @property
    def command(self) -> list[str]:
        return [self.executable, *self.args]


@dataclass(frozen=True)
class PythonInfo:
    """Metadata for an interpreter that was executed and inspected."""

    candidate: PythonCandidate
    version: str
    version_tuple: tuple[int, int, int]
    architecture: str
    executable: str

    @property
    def supported(self) -> bool:
        """A Boolean value indicating whether the interpreter meets `MIN_PYTHON`."""
        return self.version_tuple >= (*MIN_PYTHON, 0)


EXIT_OK = 0
EXIT_REQUIRED_FAILURE = 1
CandidateFailure = tuple[PythonCandidate, str]
FindExecutable = Callable[[str], str | None]


@dataclass
class CheckResult:
    name: str
    required: bool
    ok: bool
    message: str
    remediation: str = ""

    @property
    def status(self) -> str:
        if self.ok:
            return "OK"
        return "FAIL" if self.required else "WARN"


def main(argv: list[str] | None = None) -> int:
    """Runs the environment check command line."""
    parser = argparse.ArgumentParser(description="Read-only Hosted Players Report environment check.")
    parser.add_argument("--json", action="store_true", help="Write machine-readable JSON.")
    parser.add_argument(
        "--print-python-executable",
        action="store_true",
        help="Print only the selected Python executable path.",
    )
    parser.add_argument("--output-folder", help="Folder to check for report write access.")
    parser.add_argument(
        "--skip-excel-launch",
        action="store_true",
        help="Do not instantiate Excel while checking optional COM readiness.",
    )
    args = parser.parse_args(argv)

    selected, candidate_failures = select_python()
    if args.print_python_executable:
        if selected is None:
            return 1
        print(selected.executable)
        return 0

    checks = build_checks(
        selected=selected,
        candidate_failures=candidate_failures,
        output_folder=Path(args.output_folder) if args.output_folder else default_output_folder(),
        skip_excel_launch=args.skip_excel_launch,
    )

    if args.json:
        print(json.dumps(_json_payload(selected, candidate_failures, checks), indent=2))
    else:
        _print_human_report(selected, candidate_failures, checks)

    return EXIT_REQUIRED_FAILURE if any(check.required and not check.ok for check in checks) else EXIT_OK


def collect_python_candidates(
    *,
    env: Mapping[str, str] | None = None,
    which: FindExecutable = shutil.which,
) -> list[PythonCandidate]:
    """Return ordered interpreter candidates without executing them."""

    selected_env = env if env is not None else os.environ
    candidates: list[PythonCandidate] = []

    explicit = selected_env.get("HOSTED_PLAYERS_PYTHON") or selected_env.get("PYTHON")
    if explicit:
        candidates.append(PythonCandidate(explicit, "explicit HOSTED_PLAYERS_PYTHON"))

    app_venv = _application_venv_python(selected_env)
    if app_venv:
        candidates.append(PythonCandidate(str(app_venv), "existing application virtual environment"))

    active_venv = selected_env.get("VIRTUAL_ENV")
    if active_venv:
        candidates.append(PythonCandidate(str(_venv_python(Path(active_venv))), "active virtual environment"))

    conda = selected_env.get("CONDA_PREFIX")
    if conda:
        candidates.append(PythonCandidate(str(_venv_python(Path(conda))), "active Conda environment"))

    py_launcher = which("py")
    if py_launcher:
        candidates.append(PythonCandidate(py_launcher, "py launcher", ("-3",)))

    python = which("python")
    if python:
        candidates.append(PythonCandidate(python, "python on PATH"))

    python3 = which("python3")
    if python3:
        candidates.append(PythonCandidate(python3, "python3 on PATH"))

    candidates.extend(_common_conda_candidates(selected_env))
    return _dedupe_candidates(candidates)


def inspect_python(candidate: PythonCandidate, *, timeout_seconds: int = 10) -> PythonInfo:
    """Execute a candidate and return version, architecture, and executable metadata."""

    script = (
        "import json, platform, struct, sys; "
        "print(json.dumps({"
        "'version': platform.python_version(), "
        "'version_info': list(sys.version_info[:3]), "
        "'architecture': platform.architecture()[0] or (str(struct.calcsize('P') * 8) + '-bit'), "
        "'executable': sys.executable"
        "}))"
    )
    completed = subprocess.run(
        [*candidate.command, "-c", script],
        text=True,
        capture_output=True,
        check=True,
        timeout=timeout_seconds,
    )
    payload = json.loads(completed.stdout.strip())
    version_info = payload["version_info"]
    return PythonInfo(
        candidate=candidate,
        version=payload["version"],
        version_tuple=(int(version_info[0]), int(version_info[1]), int(version_info[2])),
        architecture=payload["architecture"],
        executable=payload["executable"],
    )


def select_python(
    *,
    env: Mapping[str, str] | None = None,
    which: FindExecutable = shutil.which,
) -> tuple[PythonInfo | None, list[CandidateFailure]]:
    """Return the first supported Python and inspection failures for reporting."""

    failures: list[CandidateFailure] = []
    for candidate in collect_python_candidates(env=env, which=which):
        try:
            info = inspect_python(candidate)
        except Exception as exc:
            failures.append((candidate, f"{type(exc).__name__}: {exc}"))
            continue
        if info.supported:
            return info, failures
        failures.append((candidate, f"Python {info.version} is older than 3.11"))
    return None, failures


def build_checks(
    *,
    selected: PythonInfo | None,
    candidate_failures: list[CandidateFailure],
    output_folder: Path,
    skip_excel_launch: bool,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.append(_check_python(selected, candidate_failures))
    checks.append(_check_import("openpyxl", required=True, selected=selected))
    checks.append(_check_runtime_permissions())
    checks.append(_check_output_permissions(output_folder))
    checks.append(_check_import("win32com.client", required=False, selected=selected, label="pywin32"))
    checks.append(_check_excel_readiness(selected=selected, skip_excel_launch=skip_excel_launch))
    return checks


def _check_python(selected: PythonInfo | None, candidate_failures: list[CandidateFailure]) -> CheckResult:
    if selected is not None:
        return CheckResult(
            "Python interpreter",
            True,
            True,
            (
                f"{selected.version} {selected.architecture}; "
                f"source={selected.candidate.source}; executable={selected.executable}"
            ),
        )
    details = "; ".join(f"{candidate.source}: {error}" for candidate, error in candidate_failures)
    return CheckResult(
        "Python interpreter",
        True,
        False,
        details or "No Python interpreter candidates were found.",
        "Install Python 3.11+ or set HOSTED_PLAYERS_PYTHON to python.exe, then rerun setup_and_run_gui.bat.",
    )


def _application_venv_python(env: Mapping[str, str]) -> Path | None:
    root = env.get("LOCALAPPDATA")
    if not root:
        home = env.get("USERPROFILE")
        if home:
            root = str(Path(home) / "AppData" / "Local")
    if not root:
        return None
    return _venv_python(Path(root) / APP_DIR_NAME / ".venv")


def _venv_python(root: Path) -> Path:
    if platform.system() == "Windows":
        return root / "Scripts" / "python.exe"
    return root / "bin" / "python"


def _common_conda_candidates(env: Mapping[str, str]) -> list[PythonCandidate]:
    roots = []
    userprofile = env.get("USERPROFILE")
    if userprofile:
        roots.extend(
            [
                Path(userprofile) / "Anaconda3",
                Path(userprofile) / "Miniconda3",
            ]
        )
    home = env.get("HOME")
    if home:
        roots.extend(
            [
                Path(home) / "anaconda3",
                Path(home) / "miniconda3",
            ]
        )
    return [PythonCandidate(str(_venv_python(root)), f"{root.name} environment") for root in roots]


def _dedupe_candidates(candidates: list[PythonCandidate]) -> list[PythonCandidate]:
    seen: set[tuple[str, tuple[str, ...]]] = set()
    deduped: list[PythonCandidate] = []
    for candidate in candidates:
        key = (candidate.executable.lower(), candidate.args)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _check_import(
    module: str,
    *,
    required: bool,
    selected: PythonInfo | None,
    label: str | None = None,
) -> CheckResult:
    name = label or module
    if selected is None:
        return CheckResult(name, required, False, "No supported Python selected.")
    code = f"import {module}; print('ok')"
    try:
        subprocess.run(
            [selected.executable, "-c", code],
            check=True,
            text=True,
            capture_output=True,
            timeout=20,
        )
        return CheckResult(name, required, True, "import succeeded")
    except Exception as exc:
        remediation = f'"{selected.executable}" -m pip install -r requirements.txt'
        return CheckResult(name, required, False, f"{type(exc).__name__}: {exc}", remediation)


def _check_runtime_permissions() -> CheckResult:
    path = app_data_dir()
    return _check_writable_directory(
        "Runtime directory permissions",
        path,
        required=True,
        remediation=f'Create or grant write access to "{path}".',
    )


def _check_output_permissions(path: Path) -> CheckResult:
    return _check_writable_directory(
        "Output write permissions",
        path,
        required=True,
        remediation=f'Choose an output folder you can write to, for example "{Path.home() / "Downloads"}".',
    )


def _check_writable_directory(name: str, path: Path, *, required: bool, remediation: str) -> CheckResult:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".hpr_check_", dir=path, delete=True) as handle:
            handle.write(b"ok")
        return CheckResult(name, required, True, f"writable: {path}")
    except Exception as exc:
        return CheckResult(name, required, False, f"{type(exc).__name__}: {exc}", remediation)


def _check_excel_readiness(*, selected: PythonInfo | None, skip_excel_launch: bool) -> CheckResult:
    if platform.system() != "Windows":
        return CheckResult(
            "Excel COM readiness",
            False,
            True,
            "not checked on non-Windows; static workbook fallback remains available",
        )
    if selected is None:
        return CheckResult("Excel COM readiness", False, False, "No supported Python selected.")
    if skip_excel_launch:
        return CheckResult("Excel COM readiness", False, True, "skipped by --skip-excel-launch")
    code = (
        "import win32com.client as win32; "
        "excel = win32.DispatchEx('Excel.Application'); "
        "excel.Visible = False; "
        "excel.DisplayAlerts = False; "
        "excel.Quit(); "
        "print('ok')"
    )
    try:
        subprocess.run([selected.executable, "-c", code], check=True, text=True, capture_output=True, timeout=30)
        return CheckResult("Excel COM readiness", False, True, "Excel COM instance opened and closed")
    except Exception as exc:
        return CheckResult(
            "Excel COM readiness",
            False,
            False,
            f"{type(exc).__name__}: {exc}",
            "Install desktop Excel and pywin32, then rerun setup_and_run_gui.bat.",
        )


def _print_human_report(
    selected: PythonInfo | None,
    candidate_failures: list[CandidateFailure],
    checks: list[CheckResult],
) -> None:
    print("Hosted Players Report Environment Check")
    print(f"Version: {__version__}")
    print(f"Required Python: {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+")
    if selected is not None:
        print(f"Selected Python: {selected.executable}")
        print(f"Version: {selected.version} ({selected.architecture})")
        print(f"Source: {selected.candidate.source}")
    else:
        print("Selected Python: none")
    if candidate_failures:
        print()
        print("Candidate notes:")
        for candidate, error in candidate_failures:
            print(f"  - {candidate.source}: {candidate.executable} -> {error}")
    print()
    print("Checks:")
    for check in checks:
        required = "required" if check.required else "optional"
        print(f"  [{check.status}] {check.name} ({required}): {check.message}")
        if not check.ok and check.remediation:
            print(f"       Remediation: {check.remediation}")


def _json_payload(
    selected: PythonInfo | None,
    candidate_failures: list[CandidateFailure],
    checks: list[CheckResult],
) -> dict[str, object]:
    return {
        "app": "Hosted Players Report",
        "version": __version__,
        "selected_python": None
        if selected is None
        else {
            "executable": selected.executable,
            "version": selected.version,
            "architecture": selected.architecture,
            "source": selected.candidate.source,
        },
        "candidate_failures": [
            {"source": candidate.source, "executable": candidate.executable, "error": error}
            for candidate, error in candidate_failures
        ],
        "checks": [
            {
                "name": check.name,
                "required": check.required,
                "ok": check.ok,
                "status": check.status,
                "message": check.message,
                "remediation": check.remediation,
            }
            for check in checks
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
