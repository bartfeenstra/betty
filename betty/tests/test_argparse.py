import argparse

import pytest

from betty.argparse import add_yes_argument, assertion_to_argument_type
from betty.exception import HumanFacingException
from betty.locale.localize import default_localizer


def test_assertion_to_argument_type__with_error() -> None:
    message = "Hello, world!"

    def _assertion(_: str) -> None:
        raise HumanFacingException(message)

    with pytest.raises(argparse.ArgumentTypeError, match=message):
        assertion_to_argument_type(_assertion, localizer=default_localizer)("Value")


def test_assertion_to_argument_type__without_error() -> None:
    def _assertion(value: str) -> str:
        return value.upper()

    assert (
        assertion_to_argument_type(_assertion, localizer=default_localizer)("value")
        == "VALUE"
    )


async def test_add_yes_argument__without_argument() -> None:
    parser = argparse.ArgumentParser()
    add_yes_argument(parser, localizer=default_localizer)
    namespace = parser.parse_args([])
    assert not namespace.yes


async def test_add_yes_argument__with_argument() -> None:
    parser = argparse.ArgumentParser()
    add_yes_argument(parser, localizer=default_localizer)
    namespace = parser.parse_args(["--yes"])
    assert namespace.yes
