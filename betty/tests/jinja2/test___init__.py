from __future__ import annotations

from gettext import NullTranslations
from typing import TYPE_CHECKING

from betty.ancestry import (
    Citation,
    HasFileReferences,
)
from betty.jinja2 import Jinja2Renderer, _Citer, Jinja2Provider, EntityContexts
from betty.job import Context
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizer import Localizer
from betty.media_type.media_types import JINJA2_HTML, HTML
from betty.project import Project
from betty.test_utils.assets.templates import TemplateTestBase
from betty.test_utils.model import DummyEntity

if TYPE_CHECKING:
    from betty.media_type import MediaTypeIndicator
    from pathlib import Path
    from betty.app import App


class TestJinja2Provider:
    async def test_globals(self) -> None:
        sut = Jinja2Provider()
        assert isinstance(sut.globals, dict)

    async def test_filters(self) -> None:
        sut = Jinja2Provider()
        assert isinstance(sut.filters, dict)

    async def test_tests(self) -> None:
        sut = Jinja2Provider()
        assert isinstance(sut.tests, dict)

    async def test_new_context_vars(self) -> None:
        sut = Jinja2Provider()
        assert isinstance(sut.new_context_vars(), dict)


class TestJinja2Renderer:
    async def _test_render(
        self,
        project: Project,
        expected_job_context: bool,
        expected_locale: str,
        expected_page_resource: str | None,
        media_type_indicator: MediaTypeIndicator,
        job_context: Context | None,
        localizer: Localizer | None,
    ) -> None:
        sut = Jinja2Renderer(project.jinja2_environment, project.configuration)
        content = """<!DOCTYPE html><html><head><title></title></head><body><p>{% if true %}true{% endif %}</p><p>{{ localizer.locale }}</p><p>{{ page_resource | default(none) }}</p><p>{% if job_context is defined %}true{% endif %}</p></body></html>"""
        expected = f"""<!DOCTYPE html><html><head><title></title></head><body><p>true</p><p>{expected_locale}</p><p>{expected_page_resource}</p><p>{"true" if expected_job_context else ""}</p></body></html>"""
        rendered, from_media_type, to_media_type = await sut.render(
            content, media_type_indicator, job_context=job_context, localizer=localizer
        )
        assert rendered == expected
        assert from_media_type is JINJA2_HTML
        assert to_media_type is HTML

    async def test_render_with_file_name(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._test_render(
                project,
                False,
                DEFAULT_LOCALE,
                None,
                "betty.html.j2",
                None,
                None,
            )

    async def test_render_with_file_path_outside_www_directory(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._test_render(
                project,
                False,
                DEFAULT_LOCALE,
                None,
                tmp_path / "betty.html.j2",
                None,
                None,
            )

    async def test_render_with_file_path_in_www_directory(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._test_render(
                project,
                False,
                DEFAULT_LOCALE,
                "/some-path/betty.html.j2",
                project.configuration.www_directory_path
                / "some-path"
                / "betty.html.j2",
                None,
                None,
            )

    async def test_render_with_media_type(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._test_render(
                project,
                False,
                DEFAULT_LOCALE,
                None,
                JINJA2_HTML,
                None,
                None,
            )

    async def test_render_with_job_context(self, new_temporary_app: App) -> None:
        locale = "nl-NL"
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._test_render(
                project,
                True,
                locale,
                None,
                JINJA2_HTML,
                Context(),
                Localizer(locale, NullTranslations()),
            )

    async def test_render_with_localizer(self, new_temporary_app: App) -> None:
        locale = "nl-NL"
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._test_render(
                project,
                False,
                locale,
                None,
                JINJA2_HTML,
                None,
                Localizer(locale, NullTranslations()),
            )

    async def test_media_types(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = Jinja2Renderer(project.jinja2_environment, project.configuration)
            sut.media_types  # noqa B018


class DummyHasFileReferencesEntity(HasFileReferences, DummyEntity):
    pass


class TestGlobalCiter(TemplateTestBase):
    async def test_cite(self) -> None:
        citation1 = Citation()
        citation2 = Citation()
        sut = _Citer()
        assert sut.cite(citation1) == 1
        assert sut.cite(citation2) == 2
        assert sut.cite(citation1) == 1

    async def test_iter(self) -> None:
        citation1 = Citation()
        citation2 = Citation()
        sut = _Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        sut.cite(citation1)
        assert list(sut) == [(1, citation1), (2, citation2)]

    async def test_len(self) -> None:
        citation1 = Citation()
        citation2 = Citation()
        sut = _Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        sut.cite(citation1)
        assert len(sut) == 2


class EntityContextsTestEntityA(DummyEntity):
    pass


class EntityContextsTestEntityB(DummyEntity):
    pass


class TestEntityContexts:
    async def test___getitem__(self) -> None:
        sut = EntityContexts()
        assert sut[EntityContextsTestEntityA] is None

    async def test___getitem___with___init__(self) -> None:
        a = EntityContextsTestEntityA()
        sut = EntityContexts(a)
        assert sut[EntityContextsTestEntityA] is a

    async def test___call__(self) -> None:
        a = EntityContextsTestEntityA()
        contexts = EntityContexts()
        sut = contexts(a)
        assert sut[EntityContextsTestEntityA] is a

    async def test___call___with___init__(self) -> None:
        a = EntityContextsTestEntityA()
        b = EntityContextsTestEntityA()
        contexts = EntityContexts(a)
        sut = contexts(b)
        assert sut[EntityContextsTestEntityA] is b
