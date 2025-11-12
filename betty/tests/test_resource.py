from __future__ import annotations

from gettext import NullTranslations
from typing import TYPE_CHECKING

from betty.ancestry.citation import Citation
from betty.ancestry.source import Source
from betty.job import Context as JobContext
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizer import Localizer
from betty.project import Project
from betty.resource import (
    Breadcrumb,
    Breadcrumbs,
    Citer,
    ContextVars,
    EntityContexts,
    copy_context,
    new_context,
)
from betty.test_utils.model import DummyEntityOne

if TYPE_CHECKING:
    from betty.app import App


class TestBreadcrumbs:
    def test_append(self) -> None:
        sut = Breadcrumbs()
        sut.append("My First Page", "betty:///my-first-page")

    def test___iter__(self) -> None:
        label = "My First Page"
        resource = "betty:///my-first-page"
        sut = Breadcrumbs()
        sut.append(label, resource)
        actual = list(iter(sut))
        assert actual[0].label == label

    def test___len__(self) -> None:
        label = "My First Page"
        resource = "betty:///my-first-page"
        sut = Breadcrumbs()
        sut.append(label, resource)
        assert len(sut) == 1

    async def test_dump_linked_data__without_items(self, temporary_app: App) -> None:
        sut = Breadcrumbs()
        async with Project.new_temporary(temporary_app) as project, project:
            assert await sut.dump_linked_data(project) == {}

    async def test_dump_linked_data__with_items(self, temporary_app: App) -> None:
        sut = Breadcrumbs()
        sut.append("My First Page", "betty:///my-first-page")
        async with Project.new_temporary(temporary_app) as project, project:
            assert await sut.dump_linked_data(project) == {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "item": "https://example.com/my-first-page",
                        "name": "My First Page",
                        "position": 1,
                    }
                ],
            }


class TestBreadcrumb:
    def test_label(self) -> None:
        label = "My First Page"
        sut = Breadcrumb(label, "betty:///my-first-page")
        assert sut.label == label

    def test_resource(self) -> None:
        resource = "betty:///my-first-page"
        sut = Breadcrumb("My First Page", resource)
        assert sut.resource == resource

    async def test_dump_linked_data__with_items(self, temporary_app: App) -> None:
        sut = Breadcrumb("My First Page", "betty:///my-first-page")
        async with Project.new_temporary(temporary_app) as project, project:
            assert await sut.dump_linked_data(project) == {
                "@type": "ListItem",
                "item": "https://example.com/my-first-page",
                "name": "My First Page",
            }


class TestCiter:
    def test_cite(self) -> None:
        citation1 = Citation(source=Source())
        citation2 = Citation(source=Source())
        sut = Citer()
        assert sut.cite(citation1) == 1
        assert sut.cite(citation2) == 2
        assert sut.cite(citation1) == 1

    def test___iter__(self) -> None:
        citation1 = Citation(source=Source())
        citation2 = Citation(source=Source())
        sut = Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        sut.cite(citation1)
        assert list(sut) == [(1, citation1), (2, citation2)]

    def test___len__(self) -> None:
        citation1 = Citation(source=Source())
        citation2 = Citation(source=Source())
        sut = Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        sut.cite(citation1)
        assert len(sut) == 2


class TestEntityContexts:
    async def test___getitem__(self) -> None:
        sut = EntityContexts()
        assert sut[DummyEntityOne] is None

    async def test___getitem___with___init__(self) -> None:
        a = DummyEntityOne()
        sut = EntityContexts(a)
        assert sut[DummyEntityOne] is a

    async def test___call__(self) -> None:
        a = DummyEntityOne()
        contexts = EntityContexts()
        sut = contexts(a)
        assert sut[DummyEntityOne] is a

    async def test___call___with___init__(self) -> None:
        a = DummyEntityOne()
        b = DummyEntityOne()
        contexts = EntityContexts(a)
        sut = contexts(b)
        assert sut[DummyEntityOne] is b


def test_new_context__minimal() -> None:
    assert new_context()


def test_new_context__with_resource() -> None:
    resource = "betty:///"
    assert new_context(resource)["resource"] is resource


def test_new_context__with_job_context() -> None:
    job_context = JobContext()
    assert new_context(job_context=job_context)["job_context"] is job_context


def test_new_context__with_localizer() -> None:
    localizer = Localizer(DEFAULT_LOCALE, NullTranslations())
    assert new_context(localizer=localizer)["localizer"] is localizer


def test_new_context__kwarg() -> None:
    my_first_kwarg = object()
    sut: ContextVars = new_context(my_first_kwarg=my_first_kwarg)
    assert (
        sut[
            "my_first_kwarg"  # type: ignore[typeddict-item]
        ]
        is my_first_kwarg
    )


def test_copy_context__minimal() -> None:
    context = new_context()
    assert copy_context(context) == context


def test_copy_context__kwarg() -> None:
    context_value = object()
    context = new_context(context_value=context_value)
    copied_context = copy_context(context)
    assert copied_context == context
    assert copied_context["context_value"] is context_value  # type: ignore[typeddict-item]
