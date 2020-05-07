import asyncio
import os
from glob import glob

from aiofiles import os as aioos
import sass

from betty.render import Renderer, RenderArguments


class SassRenderer(Renderer):
    _EXTENSIONS = ('sass', 'scss')

    async def render_tree(self, render_path: str, file_arguments: RenderArguments = None) -> None:
        sass.compile(dirname=(render_path, render_path))
        await asyncio.gather(*[aioos.remove(file_path) for extension in self._EXTENSIONS for pattern in [
            # Files in the path.
            os.path.join(render_path, '*.' + extension),
            # Files in the path's subdirectories.
            os.path.join(render_path, '**', '*.' + extension),
        ] for file_path in glob(pattern)])
