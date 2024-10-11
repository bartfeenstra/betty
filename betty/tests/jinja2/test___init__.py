from __future__ import annotations

from gettext import NullTranslations
from typing import TYPE_CHECKING

import aiofiles
from typing_extensions import override

from betty.ancestry.has_file_references import HasFileReferences
from betty.jinja2 import (
    Jinja2Renderer,
    Jinja2Provider,
    EntityContexts,
    Environment,
)
from betty.job import Context
from betty.locale.localizer import Localizer
from betty.project import Project
from betty.project.config import LocaleConfiguration
from betty.test_utils.model import DummyEntity
from betty.test_utils.plugin import PluginTestBase

if TYPE_CHECKING:
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


class TestJinja2Renderer(PluginTestBase[Jinja2Renderer]):
    @override
    def get_sut_class(self) -> type[Jinja2Renderer]:
        return Jinja2Renderer

    async def test_render_file(self, new_temporary_app: App, tmp_path: Path) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await Jinja2Renderer.new_for_project(project)
            template = "{% if true %}true{% endif %}"
            template_file_path = tmp_path / "betty.html.j2"
            async with aiofiles.open(template_file_path, "w") as f:
                await f.write(template)
            await sut.render_file(template_file_path)
            async with aiofiles.open(tmp_path / "betty.html") as f:
                assert (await f.read()).strip() == "true"
            assert not template_file_path.exists()

    async def test_render_file_with_job_context(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await Jinja2Renderer.new_for_project(project)
            template = "{{ job_context.start }}"
            template_file_path = tmp_path / "betty.html.j2"
            async with aiofiles.open(template_file_path, "w") as f:
                await f.write(template)
            job_context = Context()
            await sut.render_file(template_file_path, job_context=job_context)
            async with aiofiles.open(tmp_path / "betty.html") as f:
                assert (await f.read()).strip() == str(job_context.start)
            assert not template_file_path.exists()

    async def test_render_file_with_localizer(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await Jinja2Renderer.new_for_project(project)
            locale = "nl-NL"
            template = "{{ localizer.locale }}"
            template_file_path = tmp_path / "betty.html.j2"
            async with aiofiles.open(template_file_path, "w") as f:
                await f.write(template)
            localizer = Localizer(locale, NullTranslations())
            await sut.render_file(template_file_path, localizer=localizer)
            async with aiofiles.open(tmp_path / "betty.html") as f:
                assert (await f.read()).strip() == locale
            assert not template_file_path.exists()

    async def test_render_file_in_www_directory_monolingual(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await Jinja2Renderer.new_for_project(project)
            template = "{{ page_resource }}"
            template_file_path = (
                project.configuration.www_directory_path / "betty.html.j2"
            )
            template_file_path.parent.mkdir(parents=True)
            async with aiofiles.open(template_file_path, "w") as f:
                await f.write(template)
            await sut.render_file(template_file_path)
            async with aiofiles.open(
                project.configuration.www_directory_path / "betty.html"
            ) as f:
                assert (await f.read()).strip() == "/betty.html"
            assert not template_file_path.exists()

    async def test_render_file_in_www_directory_multilingual_with_static_resource(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.locales.append(LocaleConfiguration("nl-NL"))
            async with project:
                sut = await Jinja2Renderer.new_for_project(project)
                template = "{{ page_resource }}"
                template_file_path = (
                    project.configuration.www_directory_path / "betty.html.j2"
                )
                template_file_path.parent.mkdir(parents=True)
                async with aiofiles.open(template_file_path, "w") as f:
                    await f.write(template)
                await sut.render_file(template_file_path)
                async with aiofiles.open(
                    project.configuration.www_directory_path / "betty.html"
                ) as f:
                    assert (await f.read()).strip() == "/betty.html"
                assert not template_file_path.exists()

    async def test_render_file_in_www_directory_multilingual_with_localized_resource(
        self, new_temporary_app: App
    ) -> None:
        locale_alias = "nl"
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.locales.append(
                LocaleConfiguration("nl-NL", alias=locale_alias)
            )
            async with project:
                sut = await Jinja2Renderer.new_for_project(project)
                template = "{{ page_resource }}"
                template_file_path = (
                    project.configuration.www_directory_path
                    / locale_alias
                    / "betty.html.j2"
                )
                template_file_path.parent.mkdir(parents=True)
                async with aiofiles.open(template_file_path, "w") as f:
                    await f.write(template)
                await sut.render_file(template_file_path)
                async with aiofiles.open(
                    project.configuration.www_directory_path
                    / locale_alias
                    / "betty.html"
                ) as f:
                    assert (await f.read()).strip() == "/betty.html"
                assert not template_file_path.exists()

    async def test_file_extensions(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await Jinja2Renderer.new_for_project(project)
            sut.file_extensions  # noqa B018


class DummyHasFileReferencesEntity(HasFileReferences, DummyEntity):
    pass


class EntityContextsTestEntityA(DummyEntity):
    pass


class EntityContextsTestEntityB(DummyEntity):
    pass


class TestEntityContexts:
    async def test___getitem__(self) -> None:
        sut = await EntityContexts.new()
        assert sut[EntityContextsTestEntityA] is None

    async def test___getitem___with___init__(self) -> None:
        a = EntityContextsTestEntityA()
        sut = await EntityContexts.new(a)
        assert sut[EntityContextsTestEntityA] is a

    async def test___call__(self) -> None:
        a = EntityContextsTestEntityA()
        contexts = await EntityContexts.new()
        sut = contexts(a)
        assert sut[EntityContextsTestEntityA] is a

    async def test___call___with___init__(self) -> None:
        a = EntityContextsTestEntityA()
        b = EntityContextsTestEntityA()
        contexts = await EntityContexts.new(a)
        sut = contexts(b)
        assert sut[EntityContextsTestEntityA] is b


class TestEnvironment:
    async def test_context_class(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await Environment.new_for_project(project)
            context_class = sut.context_class
            context_class(sut, {}, "", {}, {})

    async def test_from_file(self, new_temporary_app: App, tmp_path: Path) -> None:
        template_string = "{% if true %}true{% endif %}"
        template_file_path = tmp_path / "betty.html.j2"
        async with aiofiles.open(template_file_path, "w") as f:
            await f.write(template_string)

        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await Environment.new_for_project(project)
            template = await sut.from_file(template_file_path)
            assert await template.render_async() == "true"

    async def test_project(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await Environment.new_for_project(project)
            assert sut.project is project

    async def test_new_for_project_with_debug(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.debug = True
            async with project:
                sut = await Environment.new_for_project(project)
                assert "jinja2.ext.DebugExtension" in sut.extensions
