"""Build the analyst release zip from an explicit runtime whitelist."""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

APP_NAME = "hosted-players-report"
ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hpr._version import __version__  # noqa: E402

RUNTIME_FILES = {
    "setup_and_run_gui.bat",
    "run_gui.bat",
    "check_env.bat",
    "gui.py",
    "cli.py",
    "check_env.py",
    "requirements.txt",
}
RUNTIME_DIRS = {"hpr"}
GENERATED_START_HERE = "START_HERE.txt"

EXCLUDED_PARTS = {
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "doc",
    "tools",
    "tests",
}
EXCLUDED_NAMES = {
    ".DS_Store",
    "AGENTS.md",
    "CHANGELOG.md",
    "README.md",
    "pyproject.toml",
    "requirements-dev.txt",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}


def main() -> int:
    version = read_version()
    DIST.mkdir(exist_ok=True)
    zip_path = DIST / f"{APP_NAME}-{version}.zip"
    manifest_path = DIST / f"{APP_NAME}-{version}.manifest.json"
    sha_path = DIST / f"{APP_NAME}-{version}.sha256"

    if zip_path.exists():
        zip_path.unlink()

    files = collect_runtime_files()
    start_here = render_start_here(version)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
        archive.writestr(GENERATED_START_HERE, start_here)

    entries = validate_zip(zip_path)
    digest = sha256_file(zip_path)
    manifest = {
        "app": "Hosted Players Report",
        "version": version,
        "build_date": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "sha256": digest,
        "zip": zip_path.name,
        "entries": entries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    sha_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")

    print(f"Built: {zip_path}")
    print(f"SHA256: {digest}")
    print(f"Manifest: {manifest_path}")
    print(f"Entries: {len(entries)}")
    return 0


def read_version() -> str:
    return __version__


def collect_runtime_files() -> list[Path]:
    files: list[Path] = []
    for name in sorted(RUNTIME_FILES):
        path = ROOT / name
        if not path.is_file():
            raise FileNotFoundError(f"Required runtime file is missing: {name}")
        files.append(path)
    for directory in sorted(RUNTIME_DIRS):
        root = ROOT / directory
        if not root.is_dir():
            raise FileNotFoundError(f"Required runtime directory is missing: {directory}")
        for path in sorted(root.rglob("*")):
            if path.is_file() and is_runtime_path(path.relative_to(ROOT)):
                files.append(path)
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix().lower())


def is_runtime_path(relative_path: Path) -> bool:
    parts = set(relative_path.parts)
    name = relative_path.name
    if relative_path.as_posix() in RUNTIME_FILES:
        return True
    if parts & EXCLUDED_PARTS:
        return False
    if name in EXCLUDED_NAMES or name.startswith("._"):
        return False
    if relative_path.suffix in EXCLUDED_SUFFIXES:
        return False
    if len(relative_path.parts) == 1:
        return False
    return relative_path.parts[0] in RUNTIME_DIRS


def validate_zip(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as archive:
        entries = sorted(archive.namelist())

    for entry in entries:
        relative_path = Path(entry)
        if entry == GENERATED_START_HERE:
            continue
        if not is_runtime_path(relative_path):
            raise RuntimeError(f"Release zip contains a non-runtime file: {entry}")
    required = sorted(RUNTIME_FILES | {GENERATED_START_HERE})
    missing = [name for name in required if name not in entries]
    for directory in sorted(RUNTIME_DIRS):
        if not any(entry.startswith(f"{directory}/") for entry in entries):
            missing.append(f"{directory}/")
    if missing:
        raise RuntimeError("Release zip is missing required entries: " + ", ".join(missing))
    return entries


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def render_start_here(version: str) -> str:
    return f"""Hosted Players Report {version}

Start here:

1. Extract this zip to a local folder.
2. Double-click setup_and_run_gui.bat the first time.
3. Double-click run_gui.bat for normal weekly use.
4. Double-click check_env.bat if setup or launch fails.

The app creates a per-user Python environment in %LOCALAPPDATA%\\HostedPlayersReport.
No administrator rights are required.
"""


if __name__ == "__main__":
    raise SystemExit(main())
