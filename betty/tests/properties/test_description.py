from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.properties.description import HasDescription

if TYPE_CHECKING:
    from betty.entity.has_links import HasLinks
    from betty.portable import PortableMapping
    from betty.test_utils.conftest import AssertDumpsLinkedData


class TestHasDescription:
    def test___init___with_description(self) -> None:
        description = "Hello, world!"
        sut = HasDescription(description=description)
        assert sut.description is not None
        assert sut.description.localize(DEFAULT_LOCALIZER) == description

    def test_description(self) -> None:
        sut = HasDescription()
        assert not sut.description

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "@context": {"description": "https://schema.org/description"},
                },
                HasDescription(),
            ),
            (
                {
                    "@context": {"description": "https://schema.org/description"},
                    "description": {DEFAULT_LOCALE_TAG: "Hello, world!"},
                },
                HasDescription(description="Hello, world!"),
            ),
        ],
    )
    async def test_dump_linked_data(
        self,
        assert_dumps_linked_data: AssertDumpsLinkedData,
        expected: PortableMapping,
        sut: HasLinks,
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
