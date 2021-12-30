from unittest import TestCase

from parameterized import parameterized

from betty.string import camel_case_to_snake_case, camel_case_to_kebab_case, upper_camel_case_to_lower_camel_case


class CamelCaseToSnakeCaseTest(TestCase):
    @parameterized.expand([
        ('snake_case', 'snakeCase'),
        ('snake_case', 'SnakeCase'),
        ('snake__case', 'Snake_Case'),
    ])
    def test(self, expected: str, string: str) -> None:
        self.assertEquals(expected, camel_case_to_snake_case(string))


class CamelCaseToKebabCaseTest(TestCase):
    @parameterized.expand([
        ('snake-case', 'snakeCase'),
        ('snake-case', 'SnakeCase'),
        ('snake--case', 'Snake-Case'),
    ])
    def test(self, expected: str, string: str) -> None:
        self.assertEquals(expected, camel_case_to_kebab_case(string))


class UpperCamelCaseToLowerCamelCase(TestCase):
    @parameterized.expand([
        ('snakeCase', 'snakeCase'),
        ('snakeCase', 'SnakeCase'),
        ('123SnakeCase', '123SnakeCase'),
    ])
    def test(self, expected: str, string: str) -> None:
        self.assertEquals(expected, upper_camel_case_to_lower_camel_case(string))
