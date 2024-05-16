import pytest

from betty.string import (
    camel_case_to_snake_case,
    camel_case_to_kebab_case,
    upper_camel_case_to_lower_camel_case,
    snake_case_to_upper_camel_case,
)


class TestCamelCaseToSnakeCase:
    @pytest.mark.parametrize(
        "expected, string",
        [
            ("snake_case", "snakeCase"),
            ("snake_case", "SnakeCase"),
            ("snake__case", "Snake_Case"),
        ],
    )
    async def test(self, expected: str, string: str) -> None:
        assert expected == camel_case_to_snake_case(string)


class TestCamelCaseToKebabCase:
    @pytest.mark.parametrize(
        "expected, string",
        [
            ("snake-case", "snakeCase"),
            ("snake-case", "SnakeCase"),
            ("snake--case", "Snake-Case"),
            ("123", "123"),
            ("", ""),
            (" ", " "),
        ],
    )
    async def test(self, expected: str, string: str) -> None:
        assert expected == camel_case_to_kebab_case(string)


class TestUpperCamelCaseToLowerCamelCase:
    @pytest.mark.parametrize(
        "expected, string",
        [
            ("snakeCase", "snakeCase"),
            ("snakeCase", "SnakeCase"),
            ("123SnakeCase", "123SnakeCase"),
            ("123", "123"),
            ("", ""),
            (" ", " "),
        ],
    )
    async def test(self, expected: str, string: str) -> None:
        assert expected == upper_camel_case_to_lower_camel_case(string)


class TestSnakeCaseToUpperCamelCase:
    @pytest.mark.parametrize(
        "expected, string",
        [
            ("SnakeCase", "snake_case"),
            ("SnakeCase", "_snake_case"),
            ("123snakeCase", "123snake_case"),
            ("SnakeCase123", "snake_case_123"),
            ("123", "123"),
            ("", ""),
            (" ", " "),
        ],
    )
    async def test(self, expected: str, string: str) -> None:
        assert expected == snake_case_to_upper_camel_case(string)
