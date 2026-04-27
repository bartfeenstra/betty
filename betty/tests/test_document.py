from __future__ import annotations

from gettext import NullTranslations
from typing import TYPE_CHECKING, Any, ClassVar

import pytest

from betty.document import (
    Breadcrumb,
    Breadcrumbs,
    Citer,
    Document,
    EntityContexts,
)
from betty.job import Context
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.plain import Plain
from betty.locale.localize import Localizer
from betty.media_type import MediaType
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.source import Source
from betty.test_utils.entity import DummyEntityOne
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.project import Project


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

    async def test_dump_linked_data__without_items(
        self, isolated_project: Project
    ) -> None:
        sut = Breadcrumbs()
        assert await sut.dump_linked_data(isolated_project) == {}

    async def test_dump_linked_data__with_items(
        self, isolated_project: Project
    ) -> None:
        sut = Breadcrumbs()
        sut.append("My First Page", "betty:///my-first-page")
        assert await sut.dump_linked_data(isolated_project) == {
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

    def test_resource_url(self) -> None:
        resource_url = "betty:///my-first-page"
        sut = Breadcrumb("My First Page", resource_url)
        assert sut.resource_url == resource_url

    async def test_dump_linked_data__with_items(
        self, isolated_project: Project
    ) -> None:
        sut = Breadcrumb("My First Page", "betty:///my-first-page")
        assert await sut.dump_linked_data(isolated_project) == {
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


class TestDocument:
    VARS: ClassVar[Mapping[str, Any]] = {
        "resource": object(),
        "resource_url": object(),
        "entity_contexts": EntityContexts(),
        "context": Context(),
        "localizer": Localizer(DEFAULT_LOCALE, NullTranslations()),
        "title": Plain("-"),
        "vars": {
            "my_first_var": "MY_FIRST_VAR",
        },
        "breadcrumbs": Breadcrumbs(),
        "citer": Citer(),
    }

    def test_resource__from___init___(self) -> None:
        resource = "betty:///"
        assert Document(resource).resource is resource

    def test_resource_url__from___init___(self) -> None:
        resource_url = "betty:///"
        assert Document(None, resource_url).resource_url is resource_url

    def test_media_type(self) -> None:
        media_type = MediaType("text/plain")
        assert Document(media_type=media_type).media_type is media_type

    def test_context__from___init___(self) -> None:
        context = Context()
        assert Document(context=context).context is context

    def test_breadcrumbs__from___init___(self) -> None:
        breadcrumbs = Breadcrumbs()
        assert Document(breadcrumbs=breadcrumbs).breadcrumbs is breadcrumbs

    def test_citer__from___init___(self) -> None:
        citer = Citer()
        assert Document(citer=citer).citer is citer

    def test_entity_contexts__from___init___(self) -> None:
        entity_contexts = EntityContexts()
        assert (
            Document(entity_contexts=entity_contexts).entity_contexts is entity_contexts
        )

    def test_localizer__from___init___(self) -> None:
        localizer = Localizer(DEFAULT_LOCALE, NullTranslations())
        assert Document(localizer=localizer).localizer is localizer

    def test_title__from___init___(self) -> None:
        title = DUMMY_LOCALIZABLE
        assert Document(title=title).title is title

    def test___getitem__(self) -> None:
        my_first_var = object()
        sut = Document(my_first_var=my_first_var)
        assert sut["my_first_var"] is my_first_var

    def test___setitem__(self) -> None:
        my_first_var = object()
        sut = Document()
        sut["my_first_var"] = my_first_var
        assert sut["my_first_var"] is my_first_var

    def test___contains__(self) -> None:
        my_first_var = object()
        sut = Document(my_first_var=my_first_var)
        assert "my_first_var" in sut
        assert "my_unknown_var" not in sut

    @pytest.mark.parametrize(
        ("expected", "sut_vars"),
        [
            (True, {}),
            (
                False,
                {
                    "resource": object(),
                },
            ),
            (
                False,
                {
                    "resource_url": object(),
                },
            ),
            (
                False,
                {
                    "entity_contexts": EntityContexts(),
                },
            ),
            (
                False,
                {
                    "context": Context(),
                },
            ),
            (
                False,
                {
                    "localizer": Localizer(DEFAULT_LOCALE, NullTranslations()),
                },
            ),
            (
                False,
                {
                    "title": DUMMY_LOCALIZABLE,
                },
            ),
            (
                False,
                {
                    "breadcrumbs": Breadcrumbs(),
                },
            ),
            (
                False,
                {
                    "citer": Citer(),
                },
            ),
            (
                False,
                {
                    "my_second_var": "MY_SECOND_VAR",
                },
            ),
        ],
    )
    def test___eq__(self, expected: bool, sut_vars: Mapping[str, object]) -> None:
        assert (
            Document(**{**self.VARS, **sut_vars}) == Document(**self.VARS)  # ty:ignore[invalid-argument-type]
        ) is expected

    def test_copy__minimal(self) -> None:
        original_sut = Document()
        assert original_sut.copy() == original_sut

    def test_copy__with_resource(self) -> None:
        original_sut = Document(resource=object())
        copied_resource = object()
        copied_sut = original_sut.copy(resource=copied_resource)
        assert copied_sut.resource is copied_resource

    def test_copy__with_resource_url(self) -> None:
        original_sut = Document(resource_url=object())
        copied_resource_url = object()
        copied_sut = original_sut.copy(resource_url=copied_resource_url)
        assert copied_sut.resource_url is copied_resource_url

    def test_copy__vars(self) -> None:
        context_value = object()
        original_sut = Document(context_value=context_value)
        copied_sut = original_sut.copy()
        assert copied_sut == original_sut
        assert copied_sut["context_value"] is context_value
