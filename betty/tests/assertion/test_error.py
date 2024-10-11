from collections.abc import Sequence

import pytest

from betty.assertion.error import (
    AssertionFailed,
    AssertionFailedGroup,
    Attr,
    Key,
    Index,
    Contextey,
    localizable_contexts,
)
from betty.locale.localizable import static, plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.test_utils.assertion.error import assert_error


class TestAttr:
    def test_format(self) -> None:
        assert Attr("attr").format() == ".attr"


class TestIndex:
    def test_format(self) -> None:
        assert Index(0).format() == "[0]"


class TestKey:
    def test_format(self) -> None:
        assert Key("key").format() == '["key"]'


class TestLocalizableContexts:
    @pytest.mark.parametrize(
        ("expected", "contexts"),
        [
            ([], []),
            (
                ["My First Context"],
                [plain("My First Context")],
            ),
            (
                ["My First Context", "My First Context"],
                [plain("My First Context"), plain("My First Context")],
            ),
            (
                ["data.attr"],
                [Attr("attr")],
            ),
            (
                ["My First Context", "data.attr"],
                [Attr("attr"), plain("My First Context")],
            ),
            (
                ["data.attr", "My First Context"],
                [plain("My First Context"), Attr("attr")],
            ),
            (
                ["My First Context", 'data.attr[0]["key"]', "My First Context"],
                [
                    plain("My First Context"),
                    Key("key"),
                    Index(0),
                    Attr("attr"),
                    plain("My First Context"),
                ],
            ),
        ],
    )
    async def test(
        self, expected: Sequence[str], contexts: Sequence[Contextey]
    ) -> None:
        sut = AssertionFailed(static("Something went wrong!")).with_context(*contexts)
        assert [
            context.localize(DEFAULT_LOCALIZER)
            for context in localizable_contexts(*sut.contexts)
        ] == expected


class TestAssertionFailed:
    async def test_localize_without_contexts(self) -> None:
        sut = AssertionFailed(static("Something went wrong!"))
        assert sut.localize(DEFAULT_LOCALIZER) == "Something went wrong!"

    async def test_localize_with_contexts(self) -> None:
        sut = AssertionFailed(static("Something went wrong!"))
        sut = sut.with_context(static("Somewhere, at some point..."))
        sut = sut.with_context(static("Somewhere else, too..."))
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- Somewhere else, too...\n- Somewhere, at some point..."
        )

    async def test_with_context(self) -> None:
        sut = AssertionFailed(static("Something went wrong!"))
        sut_with_context = sut.with_context(static("Somewhere, at some point..."))
        assert sut != sut_with_context
        assert [
            context.localize(DEFAULT_LOCALIZER)
            for context in localizable_contexts(*sut_with_context.contexts)
        ] == ["Somewhere, at some point..."]


class TestAssertionFailedGroup:
    async def test_localize_without_errors(self) -> None:
        sut = AssertionFailedGroup()
        assert sut.localize(DEFAULT_LOCALIZER) == ""

    async def test_localize_with_one_error(self) -> None:
        sut = AssertionFailedGroup()
        sut.append(AssertionFailed(static("Something went wrong!")))
        assert sut.localize(DEFAULT_LOCALIZER) == "Something went wrong!"

    async def test_localize_with_multiple_errors(self) -> None:
        sut = AssertionFailedGroup()
        sut.append(AssertionFailed(static("Something went wrong!")))
        sut.append(AssertionFailed(static("Something else went wrong, too!")))
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n\nSomething else went wrong, too!"
        )

    async def test_localize_with_predefined_contexts(self) -> None:
        sut = AssertionFailedGroup()
        sut = sut.with_context(static("Somewhere, at some point..."))
        sut = sut.with_context(static("Somewhere else, too..."))
        error_1 = AssertionFailed(static("Something went wrong!"))
        error_2 = AssertionFailed(static("Something else went wrong, too!"))
        sut.append(error_1)
        sut.append(error_2)
        assert not len(error_1.contexts)
        assert not len(error_2.contexts)
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too...\n\nSomething else went wrong, too!\n- Somewhere, at some point...\n- Somewhere else, too..."
        )

    async def test_localize_with_postdefined_contexts(self) -> None:
        sut = AssertionFailedGroup()
        error_1 = AssertionFailed(static("Something went wrong!"))
        error_2 = AssertionFailed(static("Something else went wrong, too!"))
        sut.append(error_1)
        sut.append(error_2)
        sut = sut.with_context(static("Somewhere, at some point..."))
        sut = sut.with_context(static("Somewhere else, too..."))
        assert not len(error_1.contexts)
        assert not len(error_2.contexts)
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- Somewhere else, too...\n- Somewhere, at some point...\n\nSomething else went wrong, too!\n- Somewhere else, too...\n- Somewhere, at some point..."
        )

    async def test_with_context(self) -> None:
        sut = AssertionFailedGroup()
        sut_with_context = sut.with_context(static("Somewhere, at some point..."))
        assert sut is not sut_with_context
        assert [
            context.localize(DEFAULT_LOCALIZER)
            for context in localizable_contexts(*sut_with_context.contexts)
        ] == ["Somewhere, at some point..."]

    async def test_catch_without_contexts(self) -> None:
        sut = AssertionFailedGroup()
        error = AssertionFailed(static("Help!"))
        with sut.catch() as errors:
            raise error
        assert_error(errors, error=error)  # type: ignore[unreachable]
        assert_error(sut, error=error)

    async def test_catch_with_contexts(self) -> None:
        sut = AssertionFailedGroup()
        error = AssertionFailed(static("Help!"))
        with sut.catch(static("Somewhere")) as errors:
            raise error
        assert_error(errors, error=error.with_context(static("Somewhere")))  # type: ignore[unreachable]
        assert_error(sut, error=error.with_context(static("Somewhere")))
