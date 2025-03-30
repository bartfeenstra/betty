import pytest

from betty.string import (
    camel_case_to_snake_case,
    camel_case_to_kebab_case,
    upper_camel_case_to_lower_camel_case,
    snake_case_to_upper_camel_case,
    kebab_case_to_lower_camel_case,
    snake_case_to_lower_camel_case,
    kebab_case_to_snake_case,
    snake_case_to_kebab_case,
)


@pytest.mark.parametrize(
    ("expected", "string"),
    [
        ("", ""),
        ("s", "s"),
        ("s", "S"),
        ("sn", "sn"),
        ("sn", "Sn"),
        ("snake_case", "snakeCase"),
        ("snake_case", "SnakeCase"),
        ("snake__case", "Snake_Case"),
    ],
)
async def test_camel_case_to_snake_case(expected: str, string: str) -> None:
    assert expected == camel_case_to_snake_case(string)


@pytest.mark.parametrize(
    ("expected", "string"),
    [
        ("", ""),
        ("s", "s"),
        ("s", "S"),
        ("sn", "sn"),
        ("sn", "Sn"),
        ("snake-case", "snakeCase"),
        ("snake-case", "SnakeCase"),
        ("snake--case", "Snake-Case"),
        ("123", "123"),
        (" ", " "),
    ],
)
async def test_camel_case_to_kebab_case(expected: str, string: str) -> None:
    assert expected == camel_case_to_kebab_case(string)


@pytest.mark.parametrize(
    ("expected", "string"),
    [
        ("", ""),
        ("s", "S"),
        ("sn", "Sn"),
        ("snakeCase", "SnakeCase"),
        ("123SnakeCase", "123SnakeCase"),
        ("123", "123"),
        (" ", " "),
    ],
)
async def test_upper_camel_case_to_lower_camel_case(expected: str, string: str) -> None:
    assert expected == upper_camel_case_to_lower_camel_case(string)


@pytest.mark.parametrize(
    ("expected", "string"),
    [
        ("", ""),
        ("S", "s"),
        ("Sn", "sn"),
        ("SnakeCase", "snake_case"),
        ("SnakeCase", "_snake_case"),
        ("123snakeCase", "123snake_case"),
        ("SnakeCase123", "snake_case_123"),
        ("123", "123"),
        (" ", " "),
    ],
)
async def test_snake_case_to_upper_camel_case(expected: str, string: str) -> None:
    assert expected == snake_case_to_upper_camel_case(string)


@pytest.mark.parametrize(
    ("expected", "string"),
    [
        ("", ""),
        ("s", "s"),
        ("sn", "sn"),
        ("snakeCase", "snake_case"),
        ("snakeCase", "_snake_case"),
        ("123snakeCase", "123snake_case"),
        ("snakeCase123", "snake_case_123"),
        ("123", "123"),
        (" ", " "),
    ],
)
async def test_snake_case_to_lower_camel_case(expected: str, string: str) -> None:
    assert expected == snake_case_to_lower_camel_case(string)


@pytest.mark.parametrize(
    ("expected", "string"),
    [
        ("", ""),
        ("s", "s"),
        ("sn", "sn"),
        ("snakeCase", "snake-case"),
        ("snakeCase", "-snake-case"),
        ("123snakeCase", "123snake-case"),
        ("snakeCase123", "snake-case-123"),
        ("123", "123"),
        (" ", " "),
    ],
)
async def test_kebab_case_to_lower_camel_case(expected: str, string: str) -> None:
    assert expected == kebab_case_to_lower_camel_case(string)


@pytest.mark.parametrize(
    ("expected", "string"),
    [
        ("", ""),
        ("k", "k"),
        ("ke", "ke"),
        ("kebab_case", "kebab-case"),
        ("_kebab_case", "-kebab-case"),
        ("123kebab_case", "123kebab-case"),
        ("kebab_case_123", "kebab-case-123"),
        ("123", "123"),
        (" ", " "),
    ],
)
async def test_kebab_case_to_snake_case(expected: str, string: str) -> None:
    assert expected == kebab_case_to_snake_case(string)


@pytest.mark.parametrize(
    ("expected", "string"),
    [
        ("", ""),
        ("s", "s"),
        ("sn", "sn"),
        ("snake-case", "snake_case"),
        ("-snake-case", "_snake_case"),
        ("123snake-case", "123snake_case"),
        ("snake-case-123", "snake_case_123"),
        ("123", "123"),
        (" ", " "),
    ],
)
async def test_snake_case_to_kebab_case(expected: str, string: str) -> None:
    assert expected == snake_case_to_kebab_case(string)
