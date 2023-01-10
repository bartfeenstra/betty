from typing import Any

import pytest

from betty.app import App
from betty.config.load import ConfigurationValidationError
from betty.config.validate import validate_positive_number


class TestValidatePositiveNumber:
    def test_with_invalid_number(self) -> None:
        with App():
            with pytest.raises(ConfigurationValidationError):
                validate_positive_number(0)

    def test_with_valid_number(self) -> None:
        validate_positive_number(0.1)


class TestValidate:
    class Instance:
        def __init__(self):
            self._some_valid_property = None

        @property
        def some_valid_property(self) -> Any:
            return self._some_valid_property

        @some_valid_property.setter
        def some_valid_property(self, value: Any):
            self._some_valid_property = value

        @property
        def some_invalid_property(self) -> Any:
            return None

        @some_invalid_property.setter
        def some_invalid_property(self, value: Any):
            raise ConfigurationValidationError

    def test_valid_value(self) -> None:
        instance = self.Instance()
        instance.some_valid_property = 123
        assert 123 == instance.some_valid_property

    def test_invalid_value(self) -> None:
        instance = self.Instance()
        with pytest.raises(ConfigurationValidationError):
            instance.some_invalid_property = 123
