from collections.abc import Sequence
from gettext import NullTranslations

import pytest

from betty.exception import (
    Attr,
    Contextey,
    Index,
    Key,
    UserFacingException,
    UserFacingExceptionGroup,
    do_raise,
    localizable_contexts,
)
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import plain, static
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer
from betty.test_utils.exception import assert_error


def test_do_raise() -> None:
    expected = RuntimeError()
    try:
        do_raise(expected)
    except BaseException as actual:
        assert actual is expected  # noqa PT017


class _DummyUserFacingException(UserFacingException):
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
def test_localizable_contexts(
    expected: Sequence[str], contexts: Sequence[Contextey]
) -> None:
    sut = UserFacingException(static("Something went wrong!")).with_context(*contexts)
    assert [
        context.localize(DEFAULT_LOCALIZER)
        for context in localizable_contexts(*sut.contexts)
    ] == expected


class TestUserFacingException:
    def test___str__(self) -> None:
        message = "Hello, world!"
        sut = UserFacingException(plain(message))
        assert str(sut) == message

    def test_localize(self) -> None:
        locale = "nl"
        localized_message = "Hallo, wereld!"
        message = {
            DEFAULT_LOCALE: "Hello, world!",
            locale: localized_message,
        }
        sut = UserFacingException(static(message))
        localizer = Localizer(locale, NullTranslations())
        assert sut.localize(localizer) == localized_message

    def test_localize__without_contexts(self) -> None:
        sut = UserFacingException(static("Something went wrong!"))
        assert sut.localize(DEFAULT_LOCALIZER) == "Something went wrong!"

    def test_localize__with_contexts(self) -> None:
        sut = UserFacingException(static("Something went wrong!"))
        sut = sut.with_context(static("Somewhere, at some point..."))
        sut = sut.with_context(static("Somewhere else, too..."))
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- Somewhere else, too...\n- Somewhere, at some point..."
        )

    def test_with_context__and_contexts(self) -> None:
        sut = UserFacingException(static("Something went wrong!"))
        sut_with_context = sut.with_context(static("Somewhere, at some point..."))
        assert sut != sut_with_context
        assert [
            context.localize(DEFAULT_LOCALIZER)
            for context in localizable_contexts(*sut_with_context.contexts)
        ] == ["Somewhere, at some point..."]

    @pytest.mark.parametrize(
        ("expected", "sut", "error_type"),
        [
            (True, UserFacingException(plain("")), UserFacingException),
            (False, UserFacingException(plain("")), _DummyUserFacingException),
            (True, _DummyUserFacingException(plain("")), UserFacingException),
            (True, _DummyUserFacingException(plain("")), _DummyUserFacingException),
        ],
    )
    def test_raised(
        self,
        expected: bool,
        sut: UserFacingException,
        error_type: type[UserFacingException],
    ) -> None:
        assert sut.raised(error_type) is expected


class TestUserFacingExceptionGroup:
    def test_localize__without_errors(self) -> None:
        sut = UserFacingExceptionGroup()
        assert sut.localize(DEFAULT_LOCALIZER) == ""

    def test_localize__with_one_error(self) -> None:
        sut = UserFacingExceptionGroup()
        sut.append(UserFacingException(static("Something went wrong!")))
        assert sut.localize(DEFAULT_LOCALIZER) == "Something went wrong!"

    def test_localize__with_multiple_errors(self) -> None:
        sut = UserFacingExceptionGroup()
        sut.append(UserFacingException(static("Something went wrong!")))
        sut.append(UserFacingException(static("Something else went wrong, too!")))
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n\nSomething else went wrong, too!"
        )

    def test_localize__with_predefined_contexts(self) -> None:
        sut = UserFacingExceptionGroup()
        sut = sut.with_context(static("Somewhere, at some point..."))
        sut = sut.with_context(static("Somewhere else, too..."))
        error_1 = UserFacingException(static("Something went wrong!"))
        error_2 = UserFacingException(static("Something else went wrong, too!"))
        sut.append(error_1)
        sut.append(error_2)
        assert not len(error_1.contexts)
        assert not len(error_2.contexts)
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too...\n\nSomething else went wrong, too!\n- Somewhere, at some point...\n- Somewhere else, too..."
        )

    def test_localize__with_postdefined_contexts(self) -> None:
        sut = UserFacingExceptionGroup()
        error_1 = UserFacingException(static("Something went wrong!"))
        error_2 = UserFacingException(static("Something else went wrong, too!"))
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
        sut = UserFacingExceptionGroup()
        sut_with_context = sut.with_context(static("Somewhere, at some point..."))
        assert sut is not sut_with_context
        assert [
            context.localize(DEFAULT_LOCALIZER)
            for context in localizable_contexts(*sut_with_context.contexts)
        ] == ["Somewhere, at some point..."]

    def test_catch__without_contexts(self) -> None:
        sut = UserFacingExceptionGroup()
        error = UserFacingException(static("Help!"))
        with sut.catch() as errors:
            raise error
        assert_error(errors, error=error)  # type: ignore[unreachable]
        assert_error(sut, error=error)

    def test_catch__with_contexts(self) -> None:
        sut = UserFacingExceptionGroup()
        error = UserFacingException(static("Help!"))
        with sut.catch(static("Somewhere")) as errors:
            raise error
        assert_error(errors, error=error.with_context(static("Somewhere")))  # type: ignore[unreachable]
        assert_error(sut, error=error.with_context(static("Somewhere")))

    @pytest.mark.parametrize(
        ("expected", "errors"),
        [
            (True, None),
            (True, []),
            (False, [UserFacingException(plain(""))]),
            (True, [UserFacingExceptionGroup()]),
        ],
    )
    def test_valid__and_invalid(
        self, expected: bool, errors: Sequence[UserFacingException] | None
    ) -> None:
        sut = UserFacingExceptionGroup(errors)
        assert sut.valid is expected
        assert sut.invalid is not expected

    @pytest.mark.parametrize(
        ("expected", "errors"),
        [
            (False, None),
            (False, []),
            (True, [_DummyUserFacingException(plain(""))]),
            (False, [UserFacingExceptionGroup()]),
        ],
    )
    def test_raised(
        self, expected: bool, errors: Sequence[UserFacingException] | None
    ) -> None:
        sut = UserFacingExceptionGroup(errors)
        assert sut.raised(_DummyUserFacingException) is expected

    def test_assert_valid__without_errors(self) -> None:
        with UserFacingExceptionGroup().assert_valid():
            pass

    def test_assert_valid__with_prior_error(self) -> None:
        with (
            pytest.raises(UserFacingExceptionGroup),
            UserFacingExceptionGroup([UserFacingException(plain(""))]).assert_valid(),
        ):
            pass

    def test_assert_valid__with_error_during_context_manager(self) -> None:
        with (
            pytest.raises(UserFacingExceptionGroup),
            UserFacingExceptionGroup().assert_valid(),
        ):
            raise UserFacingException(plain(""))

    def test_append(self) -> None:
        sut = UserFacingExceptionGroup()
        sut.append(UserFacingException(plain("")))
        assert len(sut) == 1

    def test_append__with_group(self) -> None:
        sut = UserFacingExceptionGroup()
        sut.append(UserFacingExceptionGroup([UserFacingException(plain(""))]))
        assert len(sut) == 1

    def test___len__(self) -> None:
        sut = UserFacingExceptionGroup([UserFacingException(plain(""))])
        assert len(sut) == 1

    def test___iter__(self) -> None:
        sut = UserFacingExceptionGroup([UserFacingException(plain(""))])
        assert len(list(iter(sut))) == 1
