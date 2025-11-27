import pathlib
from collections.abc import Sequence

import pytest

from betty.data import Attr, Context, Index, Key, Path, Selector, Selectors
from betty.locale.localizable import Lines
from betty.locale.localizer import DEFAULT_LOCALIZER


class TestAttr:
    def test_localize(self) -> None:
        assert Attr("attr").localize(DEFAULT_LOCALIZER) == ".attr"


class TestIndex:
    def test_localize(self) -> None:
        assert Index(0).localize(DEFAULT_LOCALIZER) == "[0]"


class TestKey:
    def test_localize(self) -> None:
        assert Key("key").localize(DEFAULT_LOCALIZER) == '["key"]'


class TestPath:
    def test_localize(self) -> None:
        assert (
            Path(pathlib.Path("my-first-path")).localize(DEFAULT_LOCALIZER)
            == "my-first-path"
        )


class TestSelectors:
    @pytest.mark.parametrize(
        ("expected", "selectors"),
        [
            (
                "data",
                [],
            ),
            (
                "data.my_first_attr.my_second_attr",
                [
                    Attr("my_first_attr"),
                    Attr("my_second_attr"),
                ],
            ),
        ],
    )
    def test_localize(self, expected: str, selectors: Sequence[Selector]) -> None:
        assert Selectors(*selectors).localize(DEFAULT_LOCALIZER) == expected

    @pytest.mark.parametrize(
        ("expected", "contexts"),
        [
            (
                "",
                [],
            ),
            (
                "my-first-path\ndata.my_first_attr.my_second_attr\nmy-second-path\ndata.my_third_attr.my_fourth_attr",
                [
                    Path(pathlib.Path("my-first-path")),
                    Attr("my_first_attr"),
                    Attr("my_second_attr"),
                    Path(pathlib.Path("my-second-path")),
                    Attr("my_third_attr"),
                    Attr("my_fourth_attr"),
                ],
            ),
        ],
    )
    def test_reduce(self, expected: str, contexts: Sequence[Context]) -> None:
        assert (
            Lines(*Selectors.reduce(*contexts)).localize(DEFAULT_LOCALIZER) == expected
        )
