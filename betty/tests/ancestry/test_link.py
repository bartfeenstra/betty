from __future__ import annotations

from typing import Mapping, Any, Sequence, TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.link import Link, LinkSchema, LinkCollectionSchema, HasLinks
from betty.app import App
from betty.locale import UNDETERMINED_LOCALE
from betty.media_type.media_types import HTML
from betty.project import Project
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.json.schema import SchemaTestBase

if TYPE_CHECKING:
    from betty.serde.dump import Dump, DumpMapping
    from betty.json.schema import Schema

_DUMMY_LINK_DUMPS: Sequence[DumpMapping[Dump]] = (
    {
        "url": "https://example.com",
    },
    {
        "url": "https://example.com",
        "relationship": "canonical",
    },
    {
        "url": "https://example.com",
        "label": {UNDETERMINED_LOCALE: "Hello, world!"},
    },
    {
        "url": "https://example.com",
        "privacy": True,
    },
)


class TestLink:
    async def test_url(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.url == url

    async def test_media_type(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.media_type is None

    async def test_locale(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.locale is UNDETERMINED_LOCALE

    async def test_description(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert not sut.description

    async def test_relationship(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert sut.relationship is None

    async def test_label(self) -> None:
        url = "https://example.com"
        sut = Link(url)
        assert not sut.label

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        link = Link("https://example.com")
        expected: Mapping[str, Any] = {
            "@context": {"description": "https://schema.org/description"},
            "url": "https://example.com",
            "locale": "und",
            "label": {},
            "description": {},
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected

    async def test_dump_linked_data_should_dump_full(self) -> None:
        link = Link(
            "https://example.com",
            label="The Link",
            relationship="external",
            locale="nl-NL",
            media_type=HTML,
        )
        expected: Mapping[str, Any] = {
            "@context": {"description": "https://schema.org/description"},
            "url": "https://example.com",
            "relationship": "external",
            "label": {UNDETERMINED_LOCALE: "The Link"},
            "locale": "nl-NL",
            "mediaType": "text/html",
            "description": {},
        }
        actual = await assert_dumps_linked_data(link)
        assert actual == expected


class TestLinkSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                await LinkSchema.new(),
                _DUMMY_LINK_DUMPS,
                [True, False, None, 123, "abc", [], {}],
            )
        ]


class TestLinkCollectionSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        schemas = []
        valid_datas: Sequence[Dump] = [
            *[[data] for data in _DUMMY_LINK_DUMPS],  # type: ignore[list-item]
            list(_DUMMY_LINK_DUMPS),
        ]
        invalid_datas: Sequence[Dump] = [True, False, None, 123, "abc", {}]
        async with (
            App.new_temporary() as app,
            app,
            Project.new_temporary(app) as project,
            project,
        ):
            schemas.append(
                (
                    await LinkCollectionSchema.new(),
                    valid_datas,
                    invalid_datas,
                )
            )
        return schemas


class DummyHasLinks(HasLinks):
    pass


class TestHasLinks:
    async def test_links(self) -> None:
        sut = DummyHasLinks()
        assert sut.links == []

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {"links": []},
                DummyHasLinks(),
            ),
            (
                {
                    "links": [
                        {
                            "@context": {
                                "description": "https://schema.org/description"
                            },
                            "url": "https://example.com",
                            "locale": "und",
                            "label": {},
                            "description": {},
                        }
                    ]
                },
                DummyHasLinks(links=[Link("https://example.com")]),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: HasLinks
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
