"""The Betty package root."""

from pathlib import Path

from betty import _bootstrap  # noqa: F401

# This lives here so it can be imported before any third-party Python modules are available.
_ROOT_DIRECTORY_PATH = Path(__file__).resolve().parents[1]
