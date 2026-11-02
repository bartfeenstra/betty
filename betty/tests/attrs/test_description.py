from __future__ import annotations

from betty.attrs.description import HasDescription


class TestHasDescription:
    def test___init___with_description(self) -> None:
        description = "Hello, world!"
        sut = HasDescription(description=description)
        assert sut.description is not None
        assert sut.description == description

    def test_description(self) -> None:
        sut = HasDescription()
        assert not sut.description
