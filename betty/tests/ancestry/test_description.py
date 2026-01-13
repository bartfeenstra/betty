from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.test_utils.ancestry.description import DummyHasDescription
from betty.test_utils.json.linked_data import assert_dumps_linked_data

if TYPE_CHECKING:
    from betty.ancestry.has_links import HasLinks
    from betty.serde import SerializedData, SerializedMapping


class TestHasDescription:
    async def test___init___with_description(self) -> None:
        description = "Hello, world!"
        sut = DummyHasDescription(description=description)
        assert sut.description is not None
        assert sut.description.localize(DEFAULT_LOCALIZER) == description

    async def test_description(self) -> None:
        sut = DummyHasDescription()
        assert not sut.description

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "@context": {"description": "https://schema.org/description"},
                },
                DummyHasDescription(),
            ),
            (
                {
                    "@context": {"description": "https://schema.org/description"},
                    "description": {DEFAULT_LOCALE_TAG: "Hello, world!"},
                },
                DummyHasDescription(description="Hello, world!"),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: SerializedMapping[SerializedData], sut: HasLinks
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected
