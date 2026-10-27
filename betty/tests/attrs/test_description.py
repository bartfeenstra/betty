from __future__ import annotations

from betty.attrs.description import HasDescription
from betty.localizer import default_localizer


class TestHasDescription:
    def test___init___with_description(self) -> None:
        description = "Hello, world!"
        sut = HasDescription(description=description)
        assert sut.description is not None
        assert sut.description.localize(default_localizer) == description

    def test_description(self) -> None:
        sut = HasDescription()
        assert not sut.description
