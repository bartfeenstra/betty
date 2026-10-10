from pathlib import Path

from betty.link import StaticLink
from betty.localizer import default_localizer
from betty.location import HasLocation, format_, reduce
from betty.operator import Attr, Index, Key


class TestHasLocation:
    def test_location(self) -> None:
        assert HasLocation().location == ()
        assert HasLocation(location=[Key("a")]).location == (Key("a"),)


def test_reduce() -> None:
    assert reduce() == ()
    assert format_(
        *reduce(
            Path("foo"),
            Attr("my_first_attr"),
            HasLocation(location=[Attr("my_second_attr")]),
            Path("bar"),
            Attr("my_third_attr"),
            Attr("my_fourth_attr"),
        ),
        localizer=default_localizer,
    ) == (
        "foo",
        "data.my_first_attr.my_second_attr",
        "bar",
        "data.my_third_attr.my_fourth_attr",
    )


def test_format_() -> None:
    assert format_(localizer=default_localizer) == ()
    assert format_(
        Index(9),
        StaticLink("https://example.com"),
        Path("foo.bar"),
        localizer=default_localizer,
    ) == ("[9]", "https://example.com", "foo.bar")
