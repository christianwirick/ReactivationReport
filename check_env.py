"""Launch the Hosted Players Report environment check."""

from hpr.check_env import __version__, collect_python_candidates, main

__all__ = ["__version__", "collect_python_candidates", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
