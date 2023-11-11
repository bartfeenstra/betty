import pytest

from betty.string import camel_case_to_snake_case, camel_case_to_kebab_case, upper_camel_case_to_lower_camel_case


class TestCamelCaseToSnakeCase:
    @pytest.mark.parametrize('expected, string', [
        ('snake_case', 'snakeCase'),
        ('snake_case', 'SnakeCase'),
        ('snake__case', 'Snake_Case'),
    ])
    async def test(self, expected: str, string: str) -> None:
        assert expected == camel_case_to_snake_case(string)


class TestCamelCaseToKebabCase:
    @pytest.mark.parametrize('expected, string', [
        ('snake-case', 'snakeCase'),
        ('snake-case', 'SnakeCase'),
        ('snake--case', 'Snake-Case'),
    ])
    async def test(self, expected: str, string: str) -> None:
        assert expected == camel_case_to_kebab_case(string)


class TestUpperCamelCaseToLowerCamelCase:
    @pytest.mark.parametrize('expected, string', [
        ('snakeCase', 'snakeCase'),
        ('snakeCase', 'SnakeCase'),
        ('123SnakeCase', '123SnakeCase'),
    ])
    async def test(self, expected: str, string: str) -> None:
        assert expected == upper_camel_case_to_lower_camel_case(string)
