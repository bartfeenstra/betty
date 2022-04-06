import functools
import logging
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Dict, Callable, Tuple, AsyncIterator

from jinja2 import Environment, Template

from betty import fs
from betty.app import App
from betty.project import Configuration


def patch_cache(f):
    @functools.wraps(f)
    def _patch_cache(*args, **kwargs):
        original_cache_directory_path = fs.CACHE_DIRECTORY_PATH
        cache_directory = TemporaryDirectory()
        fs.CACHE_DIRECTORY_PATH = Path(cache_directory.name)
        try:
            f(*args, **kwargs)
        finally:
            fs.CACHE_DIRECTORY_PATH = original_cache_directory_path
            cache_directory.cleanup()

    return _patch_cache


class TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls) -> None:
        logging.disable(logging.NOTSET)


class TemplateTestCase(TestCase):
    template_string: Optional[str] = None
    template_file: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.template_string is not None and self.template_file is not None:
            class_name = self.__class__.__name__
            raise RuntimeError(f'{class_name} must define either `{class_name}.template_string` or `{class_name}.template_file`, but not both.')

    @asynccontextmanager
    async def _render(self, data: Optional[Dict] = None, template_file: Optional[Template] = None, template_string: Optional[str] = None, update_project_configuration: Optional[Callable[[Configuration], None]] = None) -> AsyncIterator[Tuple[str, App]]:
        if template_string is not None and template_file is not None:
            raise RuntimeError('You must define either `template_string` or `template_file`, but not both.')
        if template_string is not None:
            template = template_string
            template_factory = Environment.from_string
        elif template_file is not None:
            template = template_file
            template_factory = Environment.get_template
        elif self.template_string is not None:
            template = self.template_string
            template_factory = Environment.from_string
        elif self.template_file is not None:
            template = self.template_file
            template_factory = Environment.get_template
        else:
            class_name = self.__class__.__name__
            raise RuntimeError(f'You must define one of `template_string`, `template_file`, `{class_name}.template_string`, or `{class_name}.template_file`.')
        if data is None:
            data = {}
        app = App()
        app.project.configuration.debug = True
        if update_project_configuration is not None:
            update_project_configuration(app.project.configuration)
        async with app:
            rendered = template_factory(app.jinja2_environment, template).render(**data)
            app.wait()
            yield rendered, app
