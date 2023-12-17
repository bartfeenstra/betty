from __future__ import annotations

from tempfile import NamedTemporaryFile
from typing import Any

import pytest
from aiofiles.tempfile import TemporaryDirectory

from betty.serde.dump import Void
from betty.serde.load import Asserter, AssertionFailed, Number, Fields, OptionalField, Assertions, RequiredField
from betty.tests.serde import raises_error


class TestAsserter:
    async def test_assert_bool_with_valid_value(self) -> None:
        sut = Asserter()
        sut.assert_bool()(True)

    async def test_assert_bool_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_bool()(123)

    async def test_assert_int_with_valid_value(self) -> None:
        sut = Asserter()
        sut.assert_int()(123)

    async def test_assert_int_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_int()(False)

    async def test_assert_float_with_valid_value(self) -> None:
        sut = Asserter()
        sut.assert_float()(1.23)

    async def test_assert_float_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_float()(False)

    @pytest.mark.parametrize('value', [
        3,
        3.13,
    ])
    async def test_assert_number_with_valid_value(self, value: Number) -> None:
        sut = Asserter()
        sut.assert_number()(value)

    async def test_assert_number_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_number()(False)

    @pytest.mark.parametrize('value', [
        0,
        0.0,
        1,
        1.1,
    ])
    async def test_assert_positive_number_with_valid_value(self, value: int | float) -> None:
        sut = Asserter()
        sut.assert_positive_number()(1.23)

    @pytest.mark.parametrize('value', [
        -1,
        -0.0000000001,
        -1.0,
    ])
    async def test_assert_positive_number_with_invalid_value(self, value: int | float) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_positive_number()(value)

    async def test_assert_str_with_valid_value(self) -> None:
        sut = Asserter()
        sut.assert_str()('Hello, world!')

    async def test_assert_str_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_str()(False)

    async def test_assert_list_with_list(self) -> None:
        sut = Asserter()
        sut.assert_list()([])

    async def test_assert_list_without_list(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_list()(False)

    async def test_assert_sequence_without_list(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_sequence(Assertions(sut.assert_str()))(False)

    async def test_assert_sequence_with_invalid_item(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed, error_contexts=['0']):
            sut.assert_sequence(Assertions(sut.assert_str()))([123])

    async def test_assert_sequence_with_empty_list(self) -> None:
        sut = Asserter()
        sut.assert_sequence(Assertions(sut.assert_str()))([])

    async def test_assert_sequence_with_valid_sequence(self) -> None:
        sut = Asserter()
        sut.assert_sequence(Assertions(sut.assert_str()))(['Hello!'])

    async def test_assert_dict_with_dict(self) -> None:
        sut = Asserter()
        sut.assert_dict()({})

    async def test_assert_dict_without_dict(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_dict()(False)

    async def test_assert_fields_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_fields(Fields(OptionalField(
                'hello',
                Assertions(sut.assert_str()),
            )))(None)

    async def test_assert_fields_required_without_key(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed, error_contexts=['hello']):
            sut.assert_fields(Fields(RequiredField(
                'hello',
                Assertions(sut.assert_str()),
            )))({})

    async def test_assert_fields_optional_without_key(self) -> None:
        sut = Asserter()
        expected: dict[str, Any] = {}
        actual = sut.assert_fields(Fields(OptionalField(
            'hello',
            Assertions(sut.assert_str()),
        )))({})
        assert expected == actual

    async def test_assert_fields_required_key_with_key(self) -> None:
        sut = Asserter()
        expected = {
            'hello': 'World!',
        }
        actual = sut.assert_fields(Fields(RequiredField(
            'hello',
            Assertions(sut.assert_str()),
        )))({'hello': 'World!'})
        assert expected == actual

    async def test_assert_fields_optional_key_with_key(self) -> None:
        sut = Asserter()
        expected = {
            'hello': 'World!',
        }
        actual = sut.assert_fields(Fields(OptionalField(
            'hello',
            Assertions(sut.assert_str()),
        )))({'hello': 'World!'})
        assert expected == actual

    async def test_assert_field_with_invalid_value(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_field(OptionalField(
                'hello',
                Assertions(sut.assert_str()),
            ))(None)

    async def test_assert_field_required_without_key(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed, error_contexts=['hello']):
            sut.assert_field(RequiredField(
                'hello',
                Assertions(sut.assert_str()),
            ))({})

    async def test_assert_field_optional_without_key(self) -> None:
        sut = Asserter()
        expected = Void
        actual = sut.assert_field(OptionalField(
            'hello',
            Assertions(sut.assert_str()),
        ))({})
        assert expected == actual

    async def test_assert_field_required_key_with_key(self) -> None:
        sut = Asserter()
        expected = 'World!'
        actual = sut.assert_field(RequiredField(
            'hello',
            Assertions(sut.assert_str()),
        ))({'hello': 'World!'})
        assert expected == actual

    async def test_assert_field_optional_key_with_key(self) -> None:
        sut = Asserter()
        expected = 'World!'
        actual = sut.assert_field(OptionalField(
            'hello',
            Assertions(sut.assert_str()),
        ))({'hello': 'World!'})
        assert expected == actual

    async def test_assert_mapping_without_mapping(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_mapping(Assertions(sut.assert_str()))(None)

    async def test_assert_mapping_with_invalid_item(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed, error_contexts=['hello']):
            sut.assert_mapping(Assertions(sut.assert_str()))({'hello': False})

    async def test_assert_mapping_with_empty_dict(self) -> None:
        sut = Asserter()
        sut.assert_mapping(Assertions(sut.assert_str()))({})

    async def test_assert_mapping_with_valid_mapping(self) -> None:
        sut = Asserter()
        sut.assert_mapping(Assertions(sut.assert_str()))({'hello': 'World!'})

    async def test_assert_record_with_optional_fields_without_items(self) -> None:
        sut = Asserter()
        expected: dict[str, Any] = {}
        actual = sut.assert_record(Fields(
            OptionalField(
                'hello',
                Assertions(sut.assert_str()),
            ),
        ))({})
        assert expected == actual

    async def test_assert_record_with_optional_fields_with_items(self) -> None:
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

    async def test_assert_record_with_required_fields_without_items(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_record(Fields(
                RequiredField(
                    'hello',
                    Assertions(sut.assert_str()),
                ),
            ))({})

    async def test_assert_record_with_required_fields_with_items(self) -> None:
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

    async def test_assert_path_without_str(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_path()(False)

    async def test_assert_path_with_valid_path(self) -> None:
        sut = Asserter()
        sut.assert_path()('~/../foo/bar')

    async def test_assert_directory_path_without_str(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_directory_path()(False)

    async def test_assert_directory_path_without_existing_path(self) -> None:
        sut = Asserter()
        with raises_error(error_type=AssertionFailed):
            sut.assert_directory_path()('~/../foo/bar')

    async def test_assert_directory_path_without_directory_path(self) -> None:
        sut = Asserter()
        with NamedTemporaryFile() as f:
            with raises_error(error_type=AssertionFailed):
                sut.assert_directory_path()(f.name)

    async def test_assert_directory_path_with_valid_path(self) -> None:
        sut = Asserter()
        async with TemporaryDirectory() as directory_path_str:
            sut.assert_directory_path()(directory_path_str)
