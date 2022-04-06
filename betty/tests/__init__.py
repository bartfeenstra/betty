import functools
import logging
import unittest
from contextlib import contextmanager, ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Dict, Callable, Tuple, Iterator, ContextManager

from jinja2 import Environment, Template

from betty import fs
from betty.app import App


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
        # Prevent App from loading its application configuration from the current user session, as it would pollute the
        # tests.
        App.__load_configuration = App._load_configuration
        App._load_configuration = lambda _: None

    @classmethod
    def tearDownClass(cls) -> None:
        App._load_configuration = App.__load_configuration
        del App.__load_configuration
        logging.disable(logging.NOTSET)


class TemplateTestCase(TestCase):
    template_string: Optional[str] = None
    template_file: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.template_string is not None and self.template_file is not None:
            class_name = self.__class__.__name__
            raise RuntimeError(f'{class_name} must define either `{class_name}.template_string` or `{class_name}.template_file`, but not both.')

    @contextmanager
    def _render(self, data: Optional[Dict] = None, template_file: Optional[Template] = None, template_string: Optional[str] = None, set_up: Optional[Callable[[App], Iterator[ContextManager]]] = None) -> Iterator[Tuple[str, App]]:
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
        contexts = ExitStack()
        with app:
            try:
                if set_up is not None:
                    for context in set_up(app):
                        contexts.enter_context(context)
                rendered = template_factory(app.jinja2_environment, template).render(**data)
                app.wait()
                yield rendered, app
            finally:
                contexts.close()
