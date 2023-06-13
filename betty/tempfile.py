from pathlib import Path
from tempfile import TemporaryDirectory as StdTemporaryDirectory
from typing import Any


class TemporaryDirectory(StdTemporaryDirectory[Any]):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.path = Path(self.name)

    def __enter__(self) -> Path:
        return self.path
