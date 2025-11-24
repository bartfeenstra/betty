import argparse

import pytest

from betty.console.assertion import assertion_to_argument_type
from betty.exception import HumanFacingException
from betty.locale.localizer import DEFAULT_LOCALIZER


def test_assertion_to_argument_type__with_error() -> None:
    message = "Hello, world!"

    def _assertion(_: str) -> None:
        raise HumanFacingException(message)

    with pytest.raises(argparse.ArgumentTypeError, match=message):
        assertion_to_argument_type(_assertion, localizer=DEFAULT_LOCALIZER)("Value")


def test_assertion_to_argument_type__without_error() -> None:
    def _assertion(value: str) -> str:
        return value.upper()

    assert (
        assertion_to_argument_type(_assertion, localizer=DEFAULT_LOCALIZER)("value")
        == "VALUE"
    )
