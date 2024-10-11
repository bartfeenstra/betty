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


class _DummyAssertionFailed(AssertionFailed):
    pass


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
    def test(self, expected: Sequence[str], contexts: Sequence[Contextey]) -> None:
        sut = AssertionFailed(static("Something went wrong!")).with_context(*contexts)
        assert [
            context.localize(DEFAULT_LOCALIZER)
            for context in localizable_contexts(*sut.contexts)
        ] == expected


class TestAssertionFailed:
    def test_localize_without_contexts(self) -> None:
        sut = AssertionFailed(static("Something went wrong!"))
        assert sut.localize(DEFAULT_LOCALIZER) == "Something went wrong!"

    def test_localize_with_contexts(self) -> None:
        sut = AssertionFailed(static("Something went wrong!"))
        sut = sut.with_context(static("Somewhere, at some point..."))
        sut = sut.with_context(static("Somewhere else, too..."))
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- Somewhere else, too...\n- Somewhere, at some point..."
        )

    def test_with_context_and_contexts(self) -> None:
        sut = AssertionFailed(static("Something went wrong!"))
        sut_with_context = sut.with_context(static("Somewhere, at some point..."))
        assert sut != sut_with_context
        assert [
            context.localize(DEFAULT_LOCALIZER)
            for context in localizable_contexts(*sut_with_context.contexts)
        ] == ["Somewhere, at some point..."]

    @pytest.mark.parametrize(
        ("expected", "sut", "error_type"),
        [
            (True, AssertionFailed(plain("")), AssertionFailed),
            (False, AssertionFailed(plain("")), _DummyAssertionFailed),
            (True, _DummyAssertionFailed(plain("")), AssertionFailed),
            (True, _DummyAssertionFailed(plain("")), _DummyAssertionFailed),
        ],
    )
    def test_raised(
        self, expected: bool, sut: AssertionFailed, error_type: type[AssertionFailed]
    ) -> None:
        assert sut.raised(error_type) is expected


class TestAssertionFailedGroup:
    def test_localize_without_errors(self) -> None:
        sut = AssertionFailedGroup()
        assert sut.localize(DEFAULT_LOCALIZER) == ""

    def test_localize_with_one_error(self) -> None:
        sut = AssertionFailedGroup()
        sut.append(AssertionFailed(static("Something went wrong!")))
        assert sut.localize(DEFAULT_LOCALIZER) == "Something went wrong!"

    def test_localize_with_multiple_errors(self) -> None:
        sut = AssertionFailedGroup()
        sut.append(AssertionFailed(static("Something went wrong!")))
        sut.append(AssertionFailed(static("Something else went wrong, too!")))
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n\nSomething else went wrong, too!"
        )

    def test_localize_with_predefined_contexts(self) -> None:
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

    def test_localize_with_postdefined_contexts(self) -> None:
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

    def test_with_context(self) -> None:
        sut = AssertionFailedGroup()
        sut_with_context = sut.with_context(static("Somewhere, at some point..."))
        assert sut is not sut_with_context
        assert [
            context.localize(DEFAULT_LOCALIZER)
            for context in localizable_contexts(*sut_with_context.contexts)
        ] == ["Somewhere, at some point..."]

    def test_catch_without_contexts(self) -> None:
        sut = AssertionFailedGroup()
        error = AssertionFailed(static("Help!"))
        with sut.catch() as errors:
            raise error
        assert_error(errors, error=error)  # type: ignore[unreachable]
        assert_error(sut, error=error)

    def test_catch_with_contexts(self) -> None:
        sut = AssertionFailedGroup()
        error = AssertionFailed(static("Help!"))
        with sut.catch(static("Somewhere")) as errors:
            raise error
        assert_error(errors, error=error.with_context(static("Somewhere")))  # type: ignore[unreachable]
        assert_error(sut, error=error.with_context(static("Somewhere")))

    @pytest.mark.parametrize(
        ("expected", "errors"),
        [
            (True, None),
            (True, []),
            (False, [AssertionFailed(plain(""))]),
            (True, [AssertionFailedGroup()]),
        ],
    )
    def test_valid_and_invalid(
        self, expected: bool, errors: Sequence[AssertionFailed] | None
    ) -> None:
        sut = AssertionFailedGroup(errors)
        assert sut.valid is expected
        assert sut.invalid is not expected

    @pytest.mark.parametrize(
        ("expected", "errors"),
        [
            (False, None),
            (False, []),
            (True, [_DummyAssertionFailed(plain(""))]),
            (False, [AssertionFailedGroup()]),
        ],
    )
    def test_raised(
        self, expected: bool, errors: Sequence[AssertionFailed] | None
    ) -> None:
        sut = AssertionFailedGroup(errors)
        assert sut.raised(_DummyAssertionFailed) is expected

    def test_assert_valid_without_errors(self) -> None:
        with AssertionFailedGroup().assert_valid():
            pass

    def test_assert_valid_with_prior_error(self) -> None:
        with (
            pytest.raises(AssertionFailedGroup),
            AssertionFailedGroup([AssertionFailed(plain(""))]).assert_valid(),
        ):
            pass

    def test_assert_valid_with_error_during_context_manager(self) -> None:
        with pytest.raises(AssertionFailedGroup), AssertionFailedGroup().assert_valid():
            raise AssertionFailed(plain(""))

    def test_append(self) -> None:
        sut = AssertionFailedGroup()
        sut.append(AssertionFailed(plain("")))
        assert len(sut) == 1

    def test_append_with_group(self) -> None:
        sut = AssertionFailedGroup()
        sut.append(AssertionFailedGroup([AssertionFailed(plain(""))]))
        assert len(sut) == 1

    def test___len__(self) -> None:
        sut = AssertionFailedGroup([AssertionFailed(plain(""))])
        assert len(sut) == 1

    def test___iter__(self) -> None:
        sut = AssertionFailedGroup([AssertionFailed(plain(""))])
        assert len(list(iter(sut))) == 1
