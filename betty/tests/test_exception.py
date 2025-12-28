from collections.abc import Sequence
from gettext import NullTranslations

import pytest

from betty.data import Attr, Key
from betty.exception import (
    HumanFacingException,
    HumanFacingExceptionGroup,
    do_raise,
    reraise_within_context,
)
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer
from betty.test_utils.exception import assert_error
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


def test_do_raise() -> None:
    expected = RuntimeError()
    try:
        do_raise(expected)
    except BaseException as actual:
        assert actual is expected  # noqa PT017


class _DummyHumanFacingException(HumanFacingException):
    pass


class TestHumanFacingException:
    def test___str__(self) -> None:
        message = "Hello, world!"
        sut = HumanFacingException(message)
        assert str(sut) == message

    def test_localize(self) -> None:
        locale = "nl"
        localized_message = "Hallo, wereld!"
        message = {
            DEFAULT_LOCALE_TAG: "Hello, world!",
            locale: localized_message,
        }
        sut = HumanFacingException(StaticTranslations(message))
        localizer = Localizer(locale, NullTranslations())
        assert sut.localize(localizer) == localized_message

    def test_localize__without_contexts(self) -> None:
        sut = HumanFacingException(StaticTranslations("Something went wrong!"))
        assert sut.localize(DEFAULT_LOCALIZER) == "Something went wrong!"

    def test_localize__with_contexts(self) -> None:
        sut = HumanFacingException(StaticTranslations("Something went wrong!"))
        sut.within_context(Attr("my_first_context"))
        sut.within_context(Attr("my_second_context"))
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- data.my_second_context.my_first_context"
        )

    def test_within_context__and_contexts(self) -> None:
        sut = HumanFacingException(StaticTranslations("Something went wrong!"))
        sut.within_context(Attr("my_first_context"))
        assert [context.format() for context in sut.contexts] == [".my_first_context"]

    @pytest.mark.parametrize(
        ("expected", "sut", "error_type"),
        [
            (True, HumanFacingException(DUMMY_LOCALIZABLE), HumanFacingException),
            (
                False,
                HumanFacingException(DUMMY_LOCALIZABLE),
                _DummyHumanFacingException,
            ),
            (
                True,
                _DummyHumanFacingException(DUMMY_LOCALIZABLE),
                HumanFacingException,
            ),
            (
                True,
                _DummyHumanFacingException(DUMMY_LOCALIZABLE),
                _DummyHumanFacingException,
            ),
        ],
    )
    def test_raised(
        self,
        expected: bool,
        sut: HumanFacingException,
        error_type: type[HumanFacingException],
    ) -> None:
        assert sut.raised(error_type) is expected


class TestHumanFacingExceptionGroup:
    def test_localize__without_errors(self) -> None:
        sut = HumanFacingExceptionGroup()
        assert sut.localize(DEFAULT_LOCALIZER) == ""

    def test_localize__with_one_error(self) -> None:
        sut = HumanFacingExceptionGroup()
        sut.append(HumanFacingException(StaticTranslations("Something went wrong!")))
        assert sut.localize(DEFAULT_LOCALIZER) == "Something went wrong!"

    def test_localize__with_multiple_errors(self) -> None:
        sut = HumanFacingExceptionGroup()
        sut.append(HumanFacingException(StaticTranslations("Something went wrong!")))
        sut.append(
            HumanFacingException(StaticTranslations("Something else went wrong, too!"))
        )
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n\nSomething else went wrong, too!"
        )

    def test_localize__with_predefined_contexts(self) -> None:
        sut = HumanFacingExceptionGroup()
        context_1 = Attr("my_first_context")
        context_2 = Attr("my_second_context")
        sut.within_context(context_1)
        sut.within_context(context_2)
        error_1 = HumanFacingException(StaticTranslations("Something went wrong!"))
        error_2 = HumanFacingException(
            StaticTranslations("Something else went wrong, too!")
        )
        sut.append(error_1)
        sut.append(error_2)
        assert error_1.contexts == [context_1, context_2]
        assert error_2.contexts == [context_1, context_2]
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- data.my_second_context.my_first_context\n\nSomething else went wrong, too!\n- data.my_second_context.my_first_context"
        )

    def test_localize__with_postdefined_contexts(self) -> None:
        sut = HumanFacingExceptionGroup()
        error_1 = HumanFacingException(StaticTranslations("Something went wrong!"))
        error_2 = HumanFacingException(
            StaticTranslations("Something else went wrong, too!")
        )
        sut.append(error_1)
        sut.append(error_2)
        context_1 = Attr("my_first_context")
        context_2 = Attr("my_second_context")
        sut.within_context(context_1)
        sut.within_context(context_2)
        assert error_1.contexts == [context_1, context_2]
        assert error_2.contexts == [context_1, context_2]
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- data.my_second_context.my_first_context\n\nSomething else went wrong, too!\n- data.my_second_context.my_first_context"
        )

    def test_within_context(self) -> None:
        sut = HumanFacingExceptionGroup()
        sut.within_context(Attr("my_first_context"))
        assert [context.format() for context in sut.contexts] == [".my_first_context"]

    def test_absorb__without_contexts(self) -> None:
        sut = HumanFacingExceptionGroup()
        error = HumanFacingException(StaticTranslations("Help!"))
        with sut.absorb():
            raise error
        assert_error(sut, error=error)  # type: ignore[unreachable]
        assert error.contexts == []

    def test_absorb__with_contexts(self) -> None:
        sut = HumanFacingExceptionGroup()
        error = HumanFacingException(StaticTranslations("Help!"))
        context = Attr("my_first_context")
        with sut.absorb(context):
            raise error
        assert_error(sut, error=error)  # type: ignore[unreachable]
        assert error.contexts == [context]

    @pytest.mark.parametrize(
        ("expected", "errors"),
        [
            (True, None),
            (True, []),
            (False, [HumanFacingException(DUMMY_LOCALIZABLE)]),
            (True, [HumanFacingExceptionGroup()]),
        ],
    )
    def test_valid__and_invalid(
        self, expected: bool, errors: Sequence[HumanFacingException] | None
    ) -> None:
        sut = HumanFacingExceptionGroup(errors)
        assert sut.valid is expected
        assert sut.invalid is not expected

    @pytest.mark.parametrize(
        ("expected", "errors"),
        [
            (False, None),
            (False, []),
            (True, [_DummyHumanFacingException(DUMMY_LOCALIZABLE)]),
            (False, [HumanFacingExceptionGroup()]),
        ],
    )
    def test_raised(
        self, expected: bool, errors: Sequence[HumanFacingException] | None
    ) -> None:
        sut = HumanFacingExceptionGroup(errors)
        assert sut.raised(_DummyHumanFacingException) is expected

    def test___enter____without_error(self) -> None:
        with HumanFacingExceptionGroup():
            pass

    def test___enter____with_error(self) -> None:
        with (
            pytest.raises(HumanFacingExceptionGroup),
            HumanFacingExceptionGroup([HumanFacingException(DUMMY_LOCALIZABLE)]),
        ):
            pass

    def test___exit____without_error(self) -> None:
        with HumanFacingExceptionGroup():
            pass

    def test___exit____with_error(self) -> None:
        with (
            pytest.raises(HumanFacingExceptionGroup),
            HumanFacingExceptionGroup(),
        ):
            raise HumanFacingException(DUMMY_LOCALIZABLE)

    def test_append(self) -> None:
        sut = HumanFacingExceptionGroup()
        sut.append(HumanFacingException(DUMMY_LOCALIZABLE))
        assert len(sut) == 1

    def test_append__with_group(self) -> None:
        sut = HumanFacingExceptionGroup()
        sut.append(HumanFacingExceptionGroup([HumanFacingException(DUMMY_LOCALIZABLE)]))
        assert len(sut) == 1

    def test___len__(self) -> None:
        sut = HumanFacingExceptionGroup([HumanFacingException(DUMMY_LOCALIZABLE)])
        assert len(sut) == 1

    def test___iter__(self) -> None:
        sut = HumanFacingExceptionGroup([HumanFacingException(DUMMY_LOCALIZABLE)])
        assert len(list(iter(sut))) == 1


def test_reraise_within_context__without_exception() -> None:
    with reraise_within_context():
        pass


def test_reraise_within_context__with_irrelevant_exception() -> None:
    class _Exception(Exception):
        pass

    with pytest.raises(_Exception), reraise_within_context():
        raise _Exception


def test_reraise_within_context__without_contexts() -> None:
    with pytest.raises(HumanFacingException), reraise_within_context():
        raise HumanFacingException("-")


def test_reraise_within_context__with_contexts() -> None:
    context = Key("my_first_key")
    with (
        pytest.raises(HumanFacingException) as exc_info,
        reraise_within_context(context),
    ):
        raise HumanFacingException("-")
    assert exc_info.value.contexts == [context]
