import pytest

from betty.string import (
    camel_case_to_snake_case,
    camel_case_to_kebab_case,
    upper_camel_case_to_lower_camel_case,
    snake_case_to_upper_camel_case,
    kebab_case_to_lower_camel_case,
    snake_case_to_lower_camel_case,
)


class TestCamelCaseToSnakeCase:
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
    async def test(self, expected: str, string: str) -> None:
        assert expected == camel_case_to_snake_case(string)


class TestCamelCaseToKebabCase:
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
    async def test(self, expected: str, string: str) -> None:
        assert expected == camel_case_to_kebab_case(string)


class TestUpperCamelCaseToLowerCamelCase:
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
    async def test(self, expected: str, string: str) -> None:
        assert expected == upper_camel_case_to_lower_camel_case(string)


class TestSnakeCaseToUpperCamelCase:
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
    async def test(self, expected: str, string: str) -> None:
        assert expected == snake_case_to_upper_camel_case(string)


class TestSnakeCaseToLowerCamelCase:
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
    async def test(self, expected: str, string: str) -> None:
        assert expected == snake_case_to_lower_camel_case(string)


class TestKebabCaseToLowerCamelCase:
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
    async def test(self, expected: str, string: str) -> None:
        assert expected == kebab_case_to_lower_camel_case(string)
