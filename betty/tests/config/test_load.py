from __future__ import annotations

from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Dict

import pytest

from betty.config.load import ConfigurationValidationError, Fields, Assertions, Number, OptionalField, RequiredField, \
    Asserter
from betty.tests.config.test___init__ import raises_configuration_error
from betty.typing import Void


class TestAsserter:
    def test_assert_bool_with_valid_value(self) -> None:
        sut = Asserter()
        sut.assert_bool()(True)

    def test_assert_bool_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_bool()(123)

    def test_assert_int_with_valid_value(self) -> None:
        sut = Asserter()
        sut.assert_int()(123)

    def test_assert_int_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_int()(False)

    def test_assert_float_with_valid_value(self) -> None:
        sut = Asserter()
        sut.assert_float()(1.23)

    def test_assert_float_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_float()(False)

    @pytest.mark.parametrize('value', [
        3,
        3.13,
    ])
    def test_assert_number_with_valid_value(self, value: Number) -> None:
        sut = Asserter()
        sut.assert_number()(value)

    def test_assert_number_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_number()(False)

    @pytest.mark.parametrize('value', [
        0,
        0.0,
        1,
        1.1,
    ])
    def test_assert_positive_number_with_valid_value(self, value: int | float) -> None:
        sut = Asserter()
        sut.assert_positive_number()(1.23)

    @pytest.mark.parametrize('value', [
        -1,
        -0.0000000001,
        -1.0,
    ])
    def test_assert_positive_number_with_invalid_value(self, value: int | float) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_positive_number()(value)

    def test_assert_str_with_valid_value(self) -> None:
        sut = Asserter()
        sut.assert_str()('Hello, world!')

    def test_assert_str_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_str()(False)

    def test_assert_list_with_list(self) -> None:
        sut = Asserter()
        sut.assert_list()([])

    def test_assert_list_without_list(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_list()(False)

    def test_assert_sequence_without_list(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_sequence(Assertions(sut.assert_str()))(False)

    def test_assert_sequence_with_invalid_item(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError, error_contexts=('0',)):
            sut.assert_sequence(Assertions(sut.assert_str()))([123])

    def test_assert_sequence_with_empty_list(self) -> None:
        sut = Asserter()
        sut.assert_sequence(Assertions(sut.assert_str()))([])

    def test_assert_sequence_with_valid_sequence(self) -> None:
        sut = Asserter()
        sut.assert_sequence(Assertions(sut.assert_str()))(['Hello!'])

    def test_assert_dict_with_dict(self) -> None:
        sut = Asserter()
        sut.assert_dict()({})

    def test_assert_dict_without_dict(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_dict()(False)

    def test_assert_fields_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_fields(Fields(OptionalField(
                'hello',
                Assertions(sut.assert_str()),
            )))(None)

    def test_assert_fields_required_without_key(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError, error_contexts=('hello',)):
            sut.assert_fields(Fields(RequiredField(
                'hello',
                Assertions(sut.assert_str()),
            )))({})

    def test_assert_fields_optional_without_key(self) -> None:
        sut = Asserter()
        expected: Dict = {}
        actual = sut.assert_fields(Fields(OptionalField(
            'hello',
            Assertions(sut.assert_str()),
        )))({})
        assert expected == actual

    def test_assert_fields_required_key_with_key(self) -> None:
        sut = Asserter()
        expected = {
            'hello': 'World!',
        }
        actual = sut.assert_fields(Fields(RequiredField(
            'hello',
            Assertions(sut.assert_str()),
        )))({'hello': 'World!'})
        assert expected == actual

    def test_assert_fields_optional_key_with_key(self) -> None:
        sut = Asserter()
        expected = {
            'hello': 'World!',
        }
        actual = sut.assert_fields(Fields(OptionalField(
            'hello',
            Assertions(sut.assert_str()),
        )))({'hello': 'World!'})
        assert expected == actual

    def test_assert_field_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_field(OptionalField(
                'hello',
                Assertions(sut.assert_str()),
            ))(None)

    def test_assert_field_required_without_key(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError, error_contexts=('hello',)):
            sut.assert_field(RequiredField(
                'hello',
                Assertions(sut.assert_str()),
            ))({})

    def test_assert_field_optional_without_key(self) -> None:
        sut = Asserter()
        expected = Void
        actual = sut.assert_field(OptionalField(
            'hello',
            Assertions(sut.assert_str()),
        ))({})
        assert expected == actual

    def test_assert_field_required_key_with_key(self) -> None:
        sut = Asserter()
        expected = 'World!'
        actual = sut.assert_field(RequiredField(
            'hello',
            Assertions(sut.assert_str()),
        ))({'hello': 'World!'})
        assert expected == actual

    def test_assert_field_optional_key_with_key(self) -> None:
        sut = Asserter()
        expected = 'World!'
        actual = sut.assert_field(OptionalField(
            'hello',
            Assertions(sut.assert_str()),
        ))({'hello': 'World!'})
        assert expected == actual

    def test_assert_mapping_without_mapping(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_mapping(Assertions(sut.assert_str()))(None)

    def test_assert_mapping_with_invalid_item(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError, error_contexts=('hello',)):
            sut.assert_mapping(Assertions(sut.assert_str()))({'hello': False})

    def test_assert_mapping_with_empty_dict(self) -> None:
        sut = Asserter()
        sut.assert_mapping(Assertions(sut.assert_str()))({})

    def test_assert_mapping_with_valid_mapping(self) -> None:
        sut = Asserter()
        sut.assert_mapping(Assertions(sut.assert_str()))({'hello': 'World!'})

    def test_assert_record_with_optional_fields_without_items(self) -> None:
        sut = Asserter()
        expected: Dict = {}
        actual = sut.assert_record(Fields(
            OptionalField(
                'hello',
                Assertions(sut.assert_str()),
            ),
        ))({})
        assert expected == actual

    def test_assert_record_with_optional_fields_with_items(self) -> None:
        sut = Asserter()
        expected = {
            'hello': 'WORLD!',
        }
        actual = sut.assert_record(Fields(
            OptionalField(
                'hello',
                Assertions(sut.assert_str()) | (lambda x: x.upper()),
            ),
        ))({'hello': 'World!'})
        assert expected == actual

    def test_assert_record_with_required_fields_without_items(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_record(Fields(
                RequiredField(
                    'hello',
                    Assertions(sut.assert_str()),
                ),
            ))({})

    def test_assert_record_with_required_fields_with_items(self) -> None:
        sut = Asserter()
        expected = {
            'hello': 'WORLD!',
        }
        actual = sut.assert_record(Fields(
            RequiredField(
                'hello',
                Assertions(sut.assert_str()) | (lambda x: x.upper()),
            ),
        ))({
            'hello': 'World!',
        })
        assert expected == actual

    def test_assert_path_without_str(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_path()(False)

    def test_assert_path_with_valid_path(self) -> None:
        sut = Asserter()
        sut.assert_path()('~/../foo/bar')

    def test_assert_directory_path_without_str(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_directory_path()(False)

    def test_assert_directory_path_without_existing_path(self) -> None:
        sut = Asserter()
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.assert_directory_path()('~/../foo/bar')

    def test_assert_directory_path_without_directory_path(self) -> None:
        sut = Asserter()
        with NamedTemporaryFile() as f:
            with raises_configuration_error(error_type=ConfigurationValidationError):
                sut.assert_directory_path()(f.name)

    def test_assert_directory_path_with_valid_path(self) -> None:
        sut = Asserter()
        with TemporaryDirectory() as directory_path:
            sut.assert_directory_path()(directory_path)
