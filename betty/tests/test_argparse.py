import argparse

import pytest

from betty.argparse import (
    UserFacingArgumentError,
    add_yes_argument,
    validator_to_argument_type,
)
from betty.localizer import default_localizer
from betty.validation import Invalid


def test_validator_to_argument_type__with_error() -> None:
    message = "Hello, world!"

    def _validator(_: str) -> None:
        raise Invalid(None, message)

    with pytest.raises(UserFacingArgumentError, match=message):
        validator_to_argument_type(_validator)("Value")


def test_validator_to_argument_type__without_error() -> None:
    def _validator(value: str) -> str:
        return value.upper()

    assert validator_to_argument_type(_validator)("value") == "VALUE"


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
