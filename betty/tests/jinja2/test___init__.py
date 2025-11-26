from __future__ import annotations

from typing import TYPE_CHECKING

import aiofiles

from betty.ancestry.has_file_references import HasFileReferences
from betty.jinja2 import Environment, Jinja2Provider
from betty.job import Context
from betty.locale import DEFAULT_LOCALE
from betty.project import Project
from betty.resource import new_context
from betty.test_utils import Counter

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

    async def test_make_copy_function__www_directory(
        self, temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await Environment.new_for_project(project)
            source_file_path = tmp_path / "source.test.j2"
            async with aiofiles.open(source_file_path, "w") as f:
                await f.write("{{ resource.resource }}\n{{ resource.resource_url }}")
            www_directory_path = tmp_path / "www"
            destination_file_path = www_directory_path / "destination.test.j2"
            rendered_destination_file_path = www_directory_path / "destination.test"
            copy_function = sut.make_copy_function(
                www_directory_path=www_directory_path, resource=new_context()
            )
            await copy_function(source_file_path, destination_file_path)
            async with aiofiles.open(rendered_destination_file_path) as f:
                assert (
                    (await f.read()).strip()
                    == f"{rendered_destination_file_path}\nbetty:///destination.test"
                )

    async def test_make_copy_function__www_directory_with_hidden_file(
        self, temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await Environment.new_for_project(project)
            source_file_path = tmp_path / "source.test.j2"
            async with aiofiles.open(source_file_path, "w") as f:
                await f.write("{{ resource.resource }}\n{{ resource.resource_url }}")
            www_directory_path = tmp_path / "www"
            destination_file_path = www_directory_path / ".destination.test.j2"
            rendered_destination_file_path = www_directory_path / ".destination.test"
            copy_function = sut.make_copy_function(
                www_directory_path=www_directory_path, resource=new_context()
            )
            await copy_function(source_file_path, destination_file_path)
            async with aiofiles.open(rendered_destination_file_path) as f:
                assert (
                    await f.read()
                ).strip() == f"{rendered_destination_file_path}\nNone"

    async def test_make_copy_function__www_directory_and_is_localized_and_multilingual(
        self, temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await Environment.new_for_project(project)
            source_file_path = tmp_path / "source.test.j2"
            async with aiofiles.open(source_file_path, "w") as f:
                await f.write("{{ resource.resource }}\n{{ resource.resource_url }}")
            www_directory_path = tmp_path / "www"
            destination_file_path = (
                www_directory_path / DEFAULT_LOCALE / "destination.test.j2"
            )
            rendered_destination_file_path = (
                www_directory_path / DEFAULT_LOCALE / "destination.test"
            )
            copy_function = sut.make_copy_function(
                www_directory_path=www_directory_path,
                is_localized_and_multilingual=True,
                resource=new_context(),
            )
            await copy_function(source_file_path, destination_file_path)
            async with aiofiles.open(rendered_destination_file_path) as f:
                assert (
                    (await f.read()).strip()
                    == f"{rendered_destination_file_path}\nbetty:///destination.test"
                )


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
        job_context = Context()
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
