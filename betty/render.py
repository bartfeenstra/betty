from pathlib import Path
from typing import List, Set


class Renderer:
    @property
    def file_extensions(self) -> Set[str]:
        raise NotImplementedError(repr(self))

    async def render_file(self, file_path: Path) -> Path:
        raise NotImplementedError(repr(self))


class SequentialRenderer(Renderer):
    def __init__(self, renderers: List[Renderer]):
        self._renderers = renderers
        self._file_extensions = {
            file_extension
            for renderer
            in self._renderers
            for file_extension
            in renderer.file_extensions
        }

    @property
    def file_extensions(self) -> Set[str]:
        return self._file_extensions

    async def render_file(self, file_path: Path) -> Path:
        for renderer in self._renderers:
            if file_path.suffix in renderer.file_extensions:
                return await self.render_file(await renderer.render_file(file_path))
        return file_path
