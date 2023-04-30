from __future__ import annotations

import functools
import inspect
from contextlib import contextmanager
from typing import Optional, Dict, Callable, Iterator, Tuple, TypeVar, Set, Type

from jinja2.environment import Template

from betty import fs
from betty.app import App, Extension
from betty.jinja2 import Environment
from betty.locale import Localey
from betty.tempfile import TemporaryDirectory

T = TypeVar('T')


def patch_cache(f):
    @functools.wraps(f)
    async def _patch_cache(*args, **kwargs) -> None:
        original_cache_directory_path = fs.CACHE_DIRECTORY_PATH
        cache_directory = TemporaryDirectory()
        fs.CACHE_DIRECTORY_PATH = cache_directory.path
        try:
            result = f(*args, **kwargs)
            if inspect.iscoroutinefunction(f):
                await result

        finally:
            fs.CACHE_DIRECTORY_PATH = original_cache_directory_path
            cache_directory.cleanup()

    return _patch_cache


class TemplateTestCase:
    template_string: Optional[str] = None
    template_file: Optional[str] = None
    extensions: Set[Type[Extension]] = set()

    @contextmanager
    def _render(self, data: Optional[Dict] = None, template_file: Optional[str] = None, template_string: Optional[str] = None, locale: Localey | None = None) -> Iterator[Tuple[str, App]]:
        if self.template_string is not None and self.template_file is not None:
            class_name = self.__class__.__name__
            raise RuntimeError(f'{class_name} must define either `{class_name}.template_string` or `{class_name}.template_file`, but not both.')

        if template_string is not None and template_file is not None:
            raise RuntimeError('You must define either `template_string` or `template_file`, but not both.')
        template_factory: Callable[..., Template]
        if template_string is not None:
            template = template_string
            template_factory = Environment.from_string  # type: ignore
        elif template_file is not None:
            template = template_file
            template_factory = Environment.get_template  # type: ignore
        elif self.template_string is not None:
            template = self.template_string
            template_factory = Environment.from_string  # type: ignore
        elif self.template_file is not None:
            template = self.template_file
            template_factory = Environment.get_template  # type: ignore
        else:
            class_name = self.__class__.__name__
            raise RuntimeError(f'You must define one of `template_string`, `template_file`, `{class_name}.template_string`, or `{class_name}.template_file`.')
        if data is None:
            data = {}
        app = App(locale=locale)
        app.project.configuration.debug = True
        with app:
            app.project.configuration.extensions.enable(*self.extensions)
            rendered = template_factory(app.jinja2_environment, template).render(**data)
            app.wait()
            yield rendered, app
