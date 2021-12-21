from pathlib import Path
from tempfile import TemporaryDirectory as StdTemporaryDirectory


class TemporaryDirectory(StdTemporaryDirectory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = Path(self.name)

    def __enter__(self) -> Path:
        return self.path
