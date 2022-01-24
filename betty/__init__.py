from pathlib import Path

# This lives here so it can be imported before any third-party Python modules are available.
_ROOT_DIRECTORY_PATH = Path(__file__).resolve().parents[1]
