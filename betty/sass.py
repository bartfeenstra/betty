import os
from glob import glob

import sass

from betty.render import Renderer, RenderArguments


class SassRenderer(Renderer):
    _EXTENSIONS = ('sass', 'scss')

    async def render_tree(self, render_path: str, file_arguments: RenderArguments = None) -> None:
        sass.compile(dirname=(render_path, render_path))
        for extension in self._EXTENSIONS:
            patterns = [
                # Files in the path.
                os.path.join(render_path, '*.' + extension),
                # Files in the path's subdirectories.
                os.path.join(render_path, '**', '*.' + extension),
            ]
            for pattern in patterns:
                for file_path in glob(pattern):
                    os.remove(file_path)
