import os
from glob import glob

import sass

from betty.render import Renderer, TemplateArguments


class SassRenderer(Renderer):
    _EXTENSIONS = {'sass', 'scss'}

    def _assert_file_path(self, file_path: str) -> None:
        if not self.consumes_file_path(file_path):
            raise ValueError('Cannot consume "%s".' % file_path)

    def consumes_file_path(self, file_path: str) -> bool:
        return file_path.endswith(tuple(self._EXTENSIONS))

    def update_file_path(self, file_path: str) -> str:
        self._assert_file_path(file_path)
        return file_path[:-3]

    async def render_string(self, template: str, template_arguments: TemplateArguments = None) -> str:
        return sass.compile(string=template)

    async def render_file(self, file_path: str, file_arguments: TemplateArguments = None) -> None:
        self._assert_file_path(file_path)
        sass.compile(filename=(file_path, file_path))
        os.remove(file_path)

    async def render_directory(self, directory_path: str, file_arguments: TemplateArguments = None) -> None:
        sass.compile(dirname=(directory_path, directory_path))
        for extension in self._EXTENSIONS:
            patterns = [
                # Files in the path.
                os.path.join(directory_path, '*.' + extension),
                # Files in the path's subdirectories.
                os.path.join(directory_path, '**', '*.' + extension),
            ]
            for pattern in patterns:
                for file_path in glob(pattern):
                    os.remove(file_path)
