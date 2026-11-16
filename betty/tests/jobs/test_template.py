from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, override

from babel.core import Locale
from jinja2 import Environment

from betty.jinja import ResolvableTemplateNames
from betty.jobs.template import CollectionResourceTemplate, ResourceTemplate, Template
from betty.project import Project, ProjectLocale
from betty.test_utils.job import do


class TestTemplate:
    def test_destination(self) -> None:
        template = Environment(enable_async=True).from_string("{{ my_first_data }}")
        destination = Path("my-first-destination")
        sut = Template("", template, destination)
        assert sut.destination is destination

    async def test_do(self, tmp_path: Path) -> None:
        template = Environment(enable_async=True).from_string("{{ my_first_data }}")
        destination = tmp_path / "template"
        data = {"my_first_data": "My First Data"}
        await do(Template("", template, destination, data))
        with open(destination, encoding="utf-8") as f:
            rendered = f.read()
        assert rendered == "My First Data"


@dataclass(frozen=True)
class _Resource:
    resource_value: Any


class _ResourceTemplate(ResourceTemplate[_Resource]):
    template_name: Final[str] = "resource-template.html.j2"

    @override
    @classmethod
    def template(cls, resource: _Resource, /) -> ResolvableTemplateNames:
        return cls.template_name

    @override
    @classmethod
    def id_prefix(cls, resource: _Resource, /) -> str:
        return cls.__name__


class TestResourceTemplate:
    def _setup_template(self, project: Project) -> None:
        template_path = (
            project.directory / "asset" / "templates" / _ResourceTemplate.template_name
        )
        template_path.parent.mkdir(parents=True)
        with open(template_path, encoding="utf-8", mode="w") as f:
            f.write("""
{{ document.resource.resource_value }}
{{ document.resource_url.resource_value }}
{{ document.localizer.locale }}
{{ document.media_type }}
""")

    async def test_do__monolingual(self, isolated_project: Project) -> None:
        self._setup_template(isolated_project)
        resource = _Resource("My First Resource Value")
        www_destination = Path("resource-template")
        (isolated_project.www_directory / www_destination).mkdir(parents=True)
        await do(_ResourceTemplate(resource, www_destination, project=isolated_project))
        with open(
            isolated_project.www_directory / www_destination / "index.html",
            encoding="utf-8",
        ) as f:
            rendered = f.read()
        assert (
            rendered
            == """
My First Resource Value
My First Resource Value
en_US
text/html"""
        )

    async def test_do__multilingual(self) -> None:
        async with Project.new_isolated() as project:
            project.locales = [
                ProjectLocale("en-US", alias="en"),
                ProjectLocale("nl-NL"),
            ]
            async with project:
                self._setup_template(project)
                resource = _Resource("My First Resource Value")
                www_destination = Path("resource-template")
                locales = (Locale("en", "US"), Locale("nl", "NL"))
                for locale in locales:
                    (project.localize_www_directory(locale) / www_destination).mkdir(
                        parents=True
                    )
                await do(_ResourceTemplate(resource, www_destination, project=project))
                for locale in locales:
                    with open(
                        project.localize_www_directory(locale)
                        / www_destination
                        / "index.html",
                        encoding="utf-8",
                    ) as f:
                        rendered = f.read()
                    assert (
                        rendered
                        == f"""
My First Resource Value
My First Resource Value
{locale}
text/html"""
                    )


@dataclass(frozen=True)
class _ResourceItem:
    resource_item_value: Any


class _CollectionResourceTemplate(CollectionResourceTemplate[_Resource, _ResourceItem]):
    template_name: Final[str] = "collection-resource-template.html.j2"

    @override
    @classmethod
    def template(cls, resource: _Resource, /) -> ResolvableTemplateNames:
        return cls.template_name

    @override
    @classmethod
    def id_prefix(cls, resource: _Resource, /) -> str:
        return cls.__name__


class TestCollectionResourceTemplate:
    _resource = _Resource("My First Resource Value")
    _resource_items = (
        _ResourceItem("My First Resource Item Value"),
        _ResourceItem("My Second Resource Item Value"),
        _ResourceItem("My Third Resource Item Value"),
    )
    _www_destination = Path("collection-resource-template")

    def _setup_template(self, project: Project) -> None:
        template_path = (
            project.directory
            / "asset"
            / "templates"
            / _CollectionResourceTemplate.template_name
        )
        template_path.parent.mkdir(parents=True)
        with open(template_path, encoding="utf-8", mode="w") as f:
            f.write("""
{{ document.resource.resource_value }}
{{ document.resource_url.resource_value }}
{{ document.localizer.locale }}
{{ document.media_type }}
{% for item in document.resource_items %}
- {{ item.resource_item_value }}
{% endfor %}
""")

    async def test_do__monolingual_without_items(
        self, isolated_project: Project
    ) -> None:
        self._setup_template(isolated_project)
        (isolated_project.www_directory / self._www_destination).mkdir(parents=True)
        await do(
            _CollectionResourceTemplate(
                self._resource, self._www_destination, project=isolated_project
            )
        )
        with open(
            isolated_project.www_directory / self._www_destination / "index.html",
            encoding="utf-8",
        ) as f:
            rendered = f.read()
        assert (
            rendered
            == """
My First Resource Value
My First Resource Value
en_US
text/html
"""
        )

    async def test_do__multilingual_without_items(self) -> None:
        async with Project.new_isolated() as project:
            project.locales = [
                ProjectLocale("en-US", alias="en"),
                ProjectLocale("nl-NL"),
            ]
            async with project:
                self._setup_template(project)
                locales = (Locale("en", "US"), Locale("nl", "NL"))
                for locale in locales:
                    (
                        project.localize_www_directory(locale) / self._www_destination
                    ).mkdir(parents=True)
                await do(
                    _CollectionResourceTemplate(
                        self._resource, self._www_destination, project=project
                    )
                )
                for locale in locales:
                    with open(
                        project.localize_www_directory(locale)
                        / self._www_destination
                        / "index.html",
                        encoding="utf-8",
                    ) as f:
                        rendered = f.read()
                    assert (
                        rendered
                        == f"""
My First Resource Value
My First Resource Value
{locale}
text/html
"""
                    )

    async def test_do__monolingual_with_items(self) -> None:
        async with Project.new_isolated() as project:
            project.per_page = 2
            async with project:
                self._setup_template(project)
                (project.www_directory / self._www_destination).mkdir(parents=True)
                await do(
                    _CollectionResourceTemplate(
                        self._resource,
                        self._www_destination,
                        *self._resource_items,
                        project=project,
                    )
                )
                with open(
                    project.www_directory / self._www_destination / "index.html",
                    encoding="utf-8",
                ) as f:
                    rendered = f.read()
                assert (
                    rendered
                    == """
My First Resource Value
My First Resource Value
en_US
text/html
- My First Resource Item Value
- My Second Resource Item Value
"""
                )
                with open(
                    project.www_directory
                    / self._www_destination
                    / "page--2"
                    / "index.html",
                    encoding="utf-8",
                ) as f:
                    rendered = f.read()
                assert (
                    rendered
                    == """
My First Resource Value
My First Resource Value
en_US
text/html
- My Third Resource Item Value
"""
                )

    async def test_do__multilingual_with_items(self) -> None:
        async with Project.new_isolated() as project:
            project.locales = [
                ProjectLocale("en-US", alias="en"),
                ProjectLocale("nl-NL"),
            ]
            project.per_page = 2
            async with project:
                self._setup_template(project)
                locales = (Locale("en", "US"), Locale("nl", "NL"))
                for locale in locales:
                    (
                        project.localize_www_directory(locale) / self._www_destination
                    ).mkdir(parents=True)
                await do(
                    _CollectionResourceTemplate(
                        self._resource,
                        self._www_destination,
                        *self._resource_items,
                        project=project,
                    )
                )
                for locale in locales:
                    with open(
                        project.localize_www_directory(locale)
                        / self._www_destination
                        / "index.html",
                        encoding="utf-8",
                    ) as f:
                        rendered = f.read()
                    assert (
                        rendered
                        == f"""
My First Resource Value
My First Resource Value
{locale}
text/html
- My First Resource Item Value
- My Second Resource Item Value
"""
                    )

                    with open(
                        project.localize_www_directory(locale)
                        / self._www_destination
                        / "page--2"
                        / "index.html",
                        encoding="utf-8",
                    ) as f:
                        rendered = f.read()
                    assert (
                        rendered
                        == f"""
My First Resource Value
My First Resource Value
{locale}
text/html
- My Third Resource Item Value
"""
                    )
