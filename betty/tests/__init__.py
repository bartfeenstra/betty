import logging
from contextlib import suppress
try:
    from contextlib import asynccontextmanager
except ImportError:
    from async_generator import asynccontextmanager
from tempfile import TemporaryDirectory
from typing import Optional, Dict, Callable, Tuple
import unittest

from jinja2 import Environment, Template

import betty
from betty.config import Configuration
from betty.site import Site


def patch_cache(f):
    def _patch_cache(*args, **kwargs):
        original_cache_directory_path = betty._CACHE_DIRECTORY_PATH
        cache_directory = TemporaryDirectory()
        betty._CACHE_DIRECTORY_PATH = cache_directory.name
        try:
            f(*args, **kwargs)
        finally:
            betty._CACHE_DIRECTORY_PATH = original_cache_directory_path
            # Pythons 3.6 and 3.7 do not allow the temporary directory to have been removed already.
            with suppress(FileNotFoundError):
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
    template_string = None
    template_file = None

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        if self.template_string is not None and self.template_file is not None:
            class_name = self.__class__.__name__
            raise RuntimeError(f'{class_name} must define either `{class_name}.template_string` or `{class_name}.template_file`, but not both.')

    @asynccontextmanager
    async def _render(self, data: Optional[Dict] = None, template_file: Optional[Template] = None, template_string: Optional[str] = None, update_configuration: Optional[Callable[[Configuration], None]] = None) -> Tuple[str, Site]:
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
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            configuration.mode = 'development'
            if update_configuration is not None:
                update_configuration(configuration)
            async with Site(configuration) as site:
                rendered = await template_factory(site.jinja2_environment, template).render_async(**data)
                # We want to keep the site around, but we must make sure all dispatched tasks are done, so we shut down
                # the executor. Crude, but effective.
                site.executor.shutdown()
                yield rendered, site
