import os
from glob import glob
from typing import Any

import sass

from betty.render import Renderer


class SassRenderer(Renderer):
    _EXTENSIONS = ('sass', 'scss')

    async def render_file(self, file_path: str) -> None:
        for extension in self._EXTENSIONS:
            if file_path.endswith(self._EXTENSIONS):
                css_file_path = '%scss' % file_path[:-len(extension)]
                break
        else:
            return
        with open(css_file_path, 'w') as f:
            f.write(self._compile(filename=file_path))
        os.remove(file_path)

    async def render_tree(self, tree_path: str) -> None:
        self._compile(dirname=(tree_path, tree_path))
        for extension in self._EXTENSIONS:
            patterns = [
                # Files in the path.
                os.path.join(tree_path, '*.' + extension),
                # Files in the path's subdirectories.
                os.path.join(tree_path, '**', '*.' + extension),
            ]
            for pattern in patterns:
                for file_path in glob(pattern):
                    os.remove(file_path)

    def _compile(self, **kwargs) -> Any:
        return sass.compile(output_style='compressed', **kwargs)
