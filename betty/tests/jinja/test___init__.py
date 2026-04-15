from __future__ import annotations

from typing import TYPE_CHECKING

from betty.document import Document
from betty.jinja import make_copy_function, new_environment
from betty.job import Context
from betty.locale import DEFAULT_LOCALE_TAG
from betty.test_utils import Counter

if TYPE_CHECKING:
    from pathlib import Path

    from betty.project import Project
    from betty.test_utils.conftest import IsolatedProjectFactory


async def test_new_environment__with_debug(
    isolated_project_factory: IsolatedProjectFactory,
) -> None:
    async with isolated_project_factory(debug=True) as project:
        sut = await new_environment(project)
        assert "jinja2.ext.DebugExtension" in sut.extensions


async def test_make_copy_function__www_directory(
    isolated_project: Project, tmp_path: Path
) -> None:
    environment = await new_environment(isolated_project)
    source_file_path = tmp_path / "source.test.j2"
    with open(source_file_path, "w", encoding="utf-8") as f:
        f.write("{{ document.resource }}\n{{ document.resource_url }}")
    www_directory_path = tmp_path / "www"
    destination_file_path = www_directory_path / "destination.test.j2"
    rendered_destination_file_path = www_directory_path / "destination.test"
    copy_function = make_copy_function(
        environment, www_directory_path=www_directory_path, document=Document()
    )
    await copy_function(source_file_path, destination_file_path)
    with open(rendered_destination_file_path, encoding="utf-8") as f:
        assert (
            f.read()
        ).strip() == f"{rendered_destination_file_path}\nbetty:///destination.test"


async def test_make_copy_function__www_directory_with_hidden_file(
    isolated_project: Project, tmp_path: Path
) -> None:
    environment = await new_environment(isolated_project)
    source_file_path = tmp_path / "source.test.j2"
    with open(source_file_path, "w", encoding="utf-8") as f:
        f.write("{{ document.resource }}\n{{ document.resource_url }}")
    www_directory_path = tmp_path / "www"
    destination_file_path = www_directory_path / ".destination.test.j2"
    rendered_destination_file_path = www_directory_path / ".destination.test"
    copy_function = make_copy_function(
        environment, www_directory_path=www_directory_path, document=Document()
    )
    await copy_function(source_file_path, destination_file_path)
    with open(rendered_destination_file_path, encoding="utf-8") as f:
        assert (f.read()).strip() == f"{rendered_destination_file_path}\nNone"


async def test_make_copy_function__www_directory_and_is_localized_and_multilingual(
    isolated_project: Project, tmp_path: Path
) -> None:
    environment = await new_environment(isolated_project)
    source_file_path = tmp_path / "source.test.j2"
    with open(source_file_path, "w", encoding="utf-8") as f:
        f.write("{{ document.resource }}\n{{ document.resource_url }}")
    www_directory_path = tmp_path / "www"
    destination_file_path = (
        www_directory_path / DEFAULT_LOCALE_TAG / "destination.test.j2"
    )
    rendered_destination_file_path = (
        www_directory_path / DEFAULT_LOCALE_TAG / "destination.test"
    )
    copy_function = make_copy_function(
        environment,
        www_directory_path=www_directory_path,
        is_localized_and_multilingual=True,
        document=Document(),
    )
    await copy_function(source_file_path, destination_file_path)
    with open(rendered_destination_file_path, encoding="utf-8") as f:
        assert (
            f.read()
        ).strip() == f"{rendered_destination_file_path}\nbetty:///destination.test"


class Test_CacheTagExtension:
    async def test_tag__without_context(self, isolated_project: Project) -> None:
        counter = Counter()
        sut = await new_environment(isolated_project)
        template = sut.from_string(
            "{% cache 'my-first-cache-key' %}{% do count() %}{% endcache %}"
        )
        await template.render_async(count=counter)
        await template.render_async(count=counter)
        assert counter.count == 2

    async def test_tag__with_context(self, isolated_project: Project) -> None:
        counter = Counter()
        context = Context()
        sut = await new_environment(isolated_project)
        template = sut.from_string(
            "{% cache 'my-first-cache-key' %}{% do count() %}{% endcache %}"
        )
        await template.render_async(count=counter, document=Document(context=context))
        await template.render_async(count=counter, document=Document(context=context))
        assert counter.count == 1
