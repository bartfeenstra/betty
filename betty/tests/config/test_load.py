from __future__ import annotations

from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Dict

import pytest

from betty.config.load import ConfigurationValidationError, assert_bool, assert_float, \
    assert_list, assert_str, assert_sequence, assert_dict, assert_field, assert_int, assert_mapping, assert_record, \
    Fields, Assertions, assert_path, assert_directory_path, assert_positive_number, assert_number, Number, \
    assert_fields, OptionalField, RequiredField
from betty.tests.config.test___init__ import raises_configuration_error
from betty.typing import Void


class TestAssertBool:
    def test_with_valid_value(self) -> None:
        assert_bool()(True)

    def test_with_invalid_value(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_bool()(123)


class TestAssertInt:
    def test_with_valid_value(self) -> None:
        assert_int()(123)

    def test_with_invalid_value(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_int()(False)


class TestAssertFloat:
    def test_with_valid_value(self) -> None:
        assert_float()(1.23)

    def test_with_invalid_value(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_float()(False)


class TestAssertNumber:
    @pytest.mark.parametrize('value', [
        3,
        3.13,
    ])
    def test_with_valid_value(self, value: Number) -> None:
        assert_number()(value)

    def test_with_invalid_value(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_number()(False)


class TestAssertPositiveNumber:
    @pytest.mark.parametrize('value', [
        0,
        0.0,
        1,
        1.1,
    ])
    def test_with_valid_value(self, value: int | float) -> None:
        assert_positive_number()(1.23)

    @pytest.mark.parametrize('value', [
        -1,
        -0.0000000001,
        -1.0,
    ])
    def test_with_invalid_value(self, value: int | float) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_positive_number()(value)


class TestAssertStr:
    def test_with_valid_value(self) -> None:
        assert_str()('Hello, world!')

    def test_with_invalid_value(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_str()(False)


class TestAssertList:
    def test_with_list(self) -> None:
        assert_list()([])

    def test_without_list(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_list()(False)


class TestAssertSequence:
    def test_without_list(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_sequence(Assertions(assert_str()))(False)

    def test_with_invalid_item(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError, error_contexts=('0',)):
            assert_sequence(Assertions(assert_str()))([123])

    def test_with_empty_list(self) -> None:
        assert_sequence(Assertions(assert_str()))([])

    def test_with_valid_sequence(self) -> None:
        assert_sequence(Assertions(assert_str()))(['Hello!'])


class TestAssertDict:
    def test_with_dict(self) -> None:
        assert_dict()({})

    def test_without_dict(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_dict()(False)


class TestAssertFields:
    def test_with_invalid_value(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_fields(Fields(OptionalField('hello', Assertions(assert_str()))))(None)

    def test_required_without_key(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError, error_contexts=('hello',)):
            assert_fields(Fields(RequiredField('hello', Assertions(assert_str()))))({})

    def test_optional_without_key(self) -> None:
        expected: Dict = {}
        actual = assert_fields(Fields(OptionalField('hello', Assertions(assert_str()))))({})
        assert expected == actual

    def test_required_key_with_key(self) -> None:
        expected = {
            'hello': 'World!',
        }
        actual = assert_fields(Fields(RequiredField('hello', Assertions(assert_str()))))({'hello': 'World!'})
        assert expected == actual

    def test_optional_key_with_key(self) -> None:
        expected = {
            'hello': 'World!',
        }
        actual = assert_fields(Fields(OptionalField('hello', Assertions(assert_str()))))({'hello': 'World!'})
        assert expected == actual


class TestAssertField:
    def test_with_invalid_value(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_field(OptionalField('hello', Assertions(assert_str())))(None)

    def test_required_without_key(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError, error_contexts=('hello',)):
            assert_field(RequiredField('hello', Assertions(assert_str())))({})

    def test_optional_without_key(self) -> None:
        expected = Void
        actual = assert_field(OptionalField('hello', Assertions(assert_str())))({})
        assert expected == actual

    def test_required_key_with_key(self) -> None:
        expected = 'World!'
        actual = assert_field(RequiredField('hello', Assertions(assert_str())))({'hello': 'World!'})
        assert expected == actual

    def test_optional_key_with_key(self) -> None:
        expected = 'World!'
        actual = assert_field(OptionalField('hello', Assertions(assert_str())))({'hello': 'World!'})
        assert expected == actual


class TestAssertMapping:
    def test_without_mapping(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_mapping(Assertions(assert_str()))(None)

    def test_with_invalid_item(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError, error_contexts=('hello',)):
            assert_mapping(Assertions(assert_str()))({'hello': False})

    def test_with_empty_dict(self) -> None:
        assert_mapping(Assertions(assert_str()))({})

    def test_with_valid_mapping(self) -> None:
        assert_mapping(Assertions(assert_str()))({'hello': 'World!'})


class TestAssertRecord:
    def test_with_optional_fields_without_items(self) -> None:
        expected: Dict = {}
        actual = assert_record(Fields(
            OptionalField('hello', Assertions(assert_str())),
        ))({})
        assert expected == actual

    def test_with_optional_fields_with_items(self) -> None:
        expected = {
            'hello': 'WORLD!',
        }
        actual = assert_record(Fields(
            OptionalField('hello', Assertions(assert_str()) | (lambda x: x.upper())),
        ))({'hello': 'World!'})
        assert expected == actual

    def test_with_required_fields_without_items(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_record(Fields(
                RequiredField('hello', Assertions(assert_str())),
            ))({})

    def test_with_required_fields_with_items(self) -> None:
        expected = {
            'hello': 'WORLD!',
        }
        actual = assert_record(Fields(
            RequiredField('hello', Assertions(assert_str()) | (lambda x: x.upper())),
        ))({
            'hello': 'World!',
        })
        assert expected == actual


class TestAssertPath:
    def test_without_str(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_path()(False)

    def test_with_valid_path(self) -> None:
        assert_path()('~/../foo/bar')


class TestAssertDirectoryPath:
    def test_without_str(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_directory_path()(False)

    def test_without_existing_path(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError):
            assert_directory_path()('~/../foo/bar')

    def test_without_directory_path(self) -> None:
        with NamedTemporaryFile() as f:
            with raises_configuration_error(error_type=ConfigurationValidationError):
                assert_directory_path()(f.name)

    def test_with_valid_path(self) -> None:
        with TemporaryDirectory() as directory_path:
            assert_directory_path()(directory_path)
