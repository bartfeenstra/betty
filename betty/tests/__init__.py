from __future__ import annotations

import functools
from contextlib import contextmanager
from typing import Callable, Iterator, TypeVar, Any

from jinja2.environment import Template
from typing_extensions import ParamSpec

from betty import fs
from betty.app import App
from betty.app.extension import Extension
from betty.jinja2 import Environment
from betty.locale import Localey
from betty.tempfile import TemporaryDirectory

T = TypeVar('T')
P = ParamSpec('P')


def patch_cache(f: Callable[P, T]) -> Callable[P, T]:
    @functools.wraps(f)
    def _patch_cache(*args: P.args, **kwargs: P.kwargs) -> T:
        original_cache_directory_path = fs.CACHE_DIRECTORY_PATH
        cache_directory = TemporaryDirectory()
        fs.CACHE_DIRECTORY_PATH = cache_directory.path
        try:
            return f(*args, **kwargs)

        finally:
            fs.CACHE_DIRECTORY_PATH = original_cache_directory_path
            cache_directory.cleanup()

    return _patch_cache


class TemplateTestCase:
    template_string: str | None = None
    template_file: str | None = None
    extensions = set[type[Extension]]()

    @contextmanager
    def _render(
        self,
        data: dict[str, Any] | None = None,
        template_file: str | None = None,
        template_string: str | None = None,
        locale: Localey | None = None,
    ) -> Iterator[tuple[str, App]]:
        if self.template_string is not None and self.template_file is not None:
            class_name = self.__class__.__name__
            raise RuntimeError(f'{class_name} must define either `{class_name}.template_string` or `{class_name}.template_file`, but not both.')

        if template_string is not None and template_file is not None:
            raise RuntimeError('You must define either `template_string` or `template_file`, but not both.')
        template_factory: Callable[..., Template]
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
        app = App(locale=locale)
        app.project.configuration.debug = True
        with app:
            app.project.configuration.extensions.enable(*self.extensions)
            rendered = template_factory(app.jinja2_environment, template).render(**data)
            app.wait()
            yield rendered, app
