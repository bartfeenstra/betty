from os import path, makedirs
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.asyncio import sync
from betty.sass import SassRenderer


class SassRendererTest(TestCase):
    @sync
    async def test_render_file(self) -> None:
        sut = SassRenderer()
        scss = 'outer { inner { display: block; } }'
        expected_css = 'outer inner{display:block}'
        with TemporaryDirectory() as working_directory_path:
            scss_file_path = path.join(working_directory_path, 'betty.scss')
            with open(scss_file_path, 'w') as f:
                f.write(scss)
            await sut.render_file(scss_file_path)
            with open(path.join(working_directory_path, 'betty.css')) as f:
                self.assertEquals(expected_css, f.read().strip())
            self.assertFalse(path.exists(scss_file_path))

    @sync
    async def test_render_file_should_ignore_non_sass_or_scss(self) -> None:
        sut = SassRenderer()
        css = 'outer inner { display: block; }'
        with TemporaryDirectory() as working_directory_path:
            css_file_path = path.join(working_directory_path, 'betty.css')
            with open(css_file_path, 'w') as f:
                f.write(css)
            await sut.render_file(css_file_path)
            with open(path.join(working_directory_path, 'betty.css')) as f:
                self.assertEquals(css, f.read())

    @sync
    async def test_render_tree(self) -> None:
        sut = SassRenderer()
        scss = 'outer { inner { display: block; } }'
        expected_css = 'outer inner{display:block}'
        with TemporaryDirectory() as working_directory_path:
            working_subdirectory_path = path.join(working_directory_path, 'sub')
            makedirs(working_subdirectory_path)
            scss_file_path = path.join(working_subdirectory_path, 'betty.scss')
            with open(scss_file_path, 'w') as f:
                f.write(scss)
            await sut.render_tree(working_directory_path)
            with open(path.join(working_subdirectory_path, 'betty.css')) as f:
                self.assertEquals(expected_css, f.read().strip())
            self.assertFalse(path.exists(scss_file_path))
