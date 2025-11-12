from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from jinja2 import Environment as Jinja2Environment
from typing_extensions import override

from betty.ancestry.has_file_references import HasFileReferences
from betty.cache.memory import MemoryCache
from betty.jinja2 import (
    Environment,
    Jinja2Provider,
    Jinja2Renderer,
)
from betty.job import Context
from betty.media_type.media_types import JINJA2
from betty.project import Project
from betty.resource import new_context
from betty.test_utils import Counter
from betty.test_utils.render import RendererDefinitionTestBase

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App
    from betty.plugin import PluginDefinition


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


class TestJinja2RendererDefinition(RendererDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Jinja2Renderer.plugin


class TestJinja2Renderer:
    async def test_render(self) -> None:
        sut = Jinja2Renderer(Jinja2Environment(enable_async=True))
        template = "{% if true %}true{% endif %}"
        rendered = await sut.render(template, JINJA2)
        assert rendered == "true"

    async def test_render__with_resource(
        self, temporary_app: App, tmp_path: Path
    ) -> None:
        resource = "betty:///"
        sut = Jinja2Renderer(Jinja2Environment(enable_async=True))
        template = "{{ resource.resource }}"
        rendered = await sut.render(template, JINJA2, resource=new_context(resource))
        assert rendered == resource

    async def test_media_types(self) -> None:
        sut = Jinja2Renderer(Jinja2Environment(enable_async=True))
        sut.media_types  # noqa B018


class DummyHasFileReferencesEntity(HasFileReferences):
    pass


class TestEnvironment:
    async def test_context_class(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await Environment.new_for_project(project)
            context_class = sut.context_class
            context_class(sut, {}, "", {}, {})

    async def test_project(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await Environment.new_for_project(project)
            assert sut.project is project

    async def test_new_for_project_with_debug(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.debug = True
            async with project:
                sut = await Environment.new_for_project(project)
                assert "jinja2.ext.DebugExtension" in sut.extensions


class Test_CacheTagExtension:
    async def test_tag__without_job_context(self, temporary_app: App) -> None:
        counter = Counter()
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await Environment.new_for_project(project)
            template = sut.from_string(
                "{% cache 'my-first-cache-key' %}{% do count() %}{% endcache %}"
            )
            await template.render_async(count=counter)
            await template.render_async(count=counter)
        assert counter.count == 2

    async def test_tag__with_job_context(self, temporary_app: App) -> None:
        counter = Counter()
        job_context = Context(cache=MemoryCache())
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await Environment.new_for_project(project)
            template = sut.from_string(
                "{% cache 'my-first-cache-key' %}{% do count() %}{% endcache %}"
            )
            await template.render_async(
                count=counter, resource=new_context(job_context=job_context)
            )
            await template.render_async(
                count=counter, resource=new_context(job_context=job_context)
            )
        assert counter.count == 1
