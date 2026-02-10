from __future__ import annotations

from typing import TYPE_CHECKING

import aiofiles

from betty.document import Document
from betty.jinja import Environment, JinjaProvider
from betty.job import Context as JobContext
from betty.locale import DEFAULT_LOCALE_TAG
from betty.project import Project
from betty.test_utils import Counter

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App


class TestJinjaProvider:
    async def test_globals(self) -> None:
        sut = JinjaProvider()
        assert isinstance(sut.globals, dict)

    async def test_filters(self) -> None:
        sut = JinjaProvider()
        assert isinstance(sut.filters, dict)

    async def test_tests(self) -> None:
        sut = JinjaProvider()
        assert isinstance(sut.tests, dict)


class TestEnvironment:
    async def test_context_class(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await Environment.new(project)
            context_class = sut.context_class
            context_class(sut, {}, "", {}, {})

    async def test_project(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await Environment.new(project)
            assert sut.project is project

    async def test_new_with_debug(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.debug = True
            async with project:
                sut = await Environment.new(project)
                assert "jinja2.ext.DebugExtension" in sut.extensions

    async def test_make_copy_function__www_directory(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await Environment.new(project)
            source_file_path = tmp_path / "source.test.j2"
            async with aiofiles.open(source_file_path, "w") as f:
                await f.write("{{ document.resource }}\n{{ document.resource_url }}")
            www_directory_path = tmp_path / "www"
            destination_file_path = www_directory_path / "destination.test.j2"
            rendered_destination_file_path = www_directory_path / "destination.test"
            copy_function = sut.make_copy_function(
                www_directory_path=www_directory_path, document=Document()
            )
            await copy_function(source_file_path, destination_file_path)
            async with aiofiles.open(rendered_destination_file_path) as f:
                assert (
                    (await f.read()).strip()
                    == f"{rendered_destination_file_path}\nbetty:///destination.test"
                )

    async def test_make_copy_function__www_directory_with_hidden_file(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await Environment.new(project)
            source_file_path = tmp_path / "source.test.j2"
            async with aiofiles.open(source_file_path, "w") as f:
                await f.write("{{ document.resource }}\n{{ document.resource_url }}")
            www_directory_path = tmp_path / "www"
            destination_file_path = www_directory_path / ".destination.test.j2"
            rendered_destination_file_path = www_directory_path / ".destination.test"
            copy_function = sut.make_copy_function(
                www_directory_path=www_directory_path, document=Document()
            )
            await copy_function(source_file_path, destination_file_path)
            async with aiofiles.open(rendered_destination_file_path) as f:
                assert (
                    await f.read()
                ).strip() == f"{rendered_destination_file_path}\nNone"

    async def test_make_copy_function__www_directory_and_is_localized_and_multilingual(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await Environment.new(project)
            source_file_path = tmp_path / "source.test.j2"
            async with aiofiles.open(source_file_path, "w") as f:
                await f.write("{{ document.resource }}\n{{ document.resource_url }}")
            www_directory_path = tmp_path / "www"
            destination_file_path = (
                www_directory_path / DEFAULT_LOCALE_TAG / "destination.test.j2"
            )
            rendered_destination_file_path = (
                www_directory_path / DEFAULT_LOCALE_TAG / "destination.test"
            )
            copy_function = sut.make_copy_function(
                www_directory_path=www_directory_path,
                is_localized_and_multilingual=True,
                document=Document(),
            )
            await copy_function(source_file_path, destination_file_path)
            async with aiofiles.open(rendered_destination_file_path) as f:
                assert (
                    (await f.read()).strip()
                    == f"{rendered_destination_file_path}\nbetty:///destination.test"
                )


class Test_CacheTagExtension:
    async def test_tag__without_job_context(self, isolated_app: App) -> None:
        counter = Counter()
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await Environment.new(project)
            template = sut.from_string(
                "{% cache 'my-first-cache-key' %}{% do count() %}{% endcache %}"
            )
            await template.render_async(count=counter)
            await template.render_async(count=counter)
        assert counter.count == 2

    async def test_tag__with_job_context(self, isolated_app: App) -> None:
        counter = Counter()
        job_context = JobContext()
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await Environment.new(project)
            template = sut.from_string(
                "{% cache 'my-first-cache-key' %}{% do count() %}{% endcache %}"
            )
            await template.render_async(
                count=counter, document=Document(job_context=job_context)
            )
            await template.render_async(
                count=counter, document=Document(job_context=job_context)
            )
        assert counter.count == 1
