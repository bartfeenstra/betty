from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any

import pytest
from reactives.instance import ReactiveInstance
from reactives.instance.property import reactive_property

from betty.config.error import ConfigurationError
from betty.config.load import ConfigurationValidationError, Loader, ConfigurationLoadError, Field
from betty.tests.config.test___init__ import raises_no_configuration_errors, raises_configuration_error, \
    assert_configuration_error


class TestLoader:
    def test_commit_without_errors_and_committers(self) -> None:
        sut = Loader()
        sut.commit()

    def test_commit_without_errors_with_committers(self) -> None:
        on_commit_tracker = []
        sut = Loader()
        sut.on_commit(lambda: on_commit_tracker.append(True))
        sut.commit()
        assert [True] == on_commit_tracker

    def test_commit_with_errors(self) -> None:
        error = ConfigurationLoadError('Help!')
        sut = Loader()
        sut.error(error)
        with pytest.raises(ConfigurationError):
            sut.commit()

    def test_catch(self) -> None:
        sut = Loader()
        error = ConfigurationLoadError('Help!')
        with sut.catch():
            raise error
        assert_configuration_error(sut.errors, error)

    def test_context_without_contexts(self) -> None:
        sut = Loader()
        error = ConfigurationLoadError('Help!')
        with sut.context() as errors:
            sut.error(error)
            assert_configuration_error(errors, error)
        assert_configuration_error(sut.errors, error)

    def test_context_with_contexts(self) -> None:
        sut = Loader()
        error = ConfigurationLoadError('Help!')
        with sut.context('Somewhere') as errors:
            sut.error(error)
            assert_configuration_error(errors, error=error, error_contexts=('Somewhere',))
        assert_configuration_error(sut.errors, error=error, error_contexts=())

    def test_evaluate_with_errors(self) -> None:
        sut = Loader()
        error = ConfigurationLoadError('Help!')
        sut.error(error)
        assert_configuration_error(sut.errors, error)

    def test_evaluate_with_committers(self) -> None:
        sut = Loader()
        on_commit_tracker = []
        sut.on_commit(lambda: on_commit_tracker.append(True))
        sut.commit()
        assert [True] == on_commit_tracker

    def test_assert_bool_with_valid_value(self) -> None:
        with raises_no_configuration_errors() as loader:
            loader.assert_bool(True)

    def test_assert_bool_with_invalid_value(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_bool(123)

    def test_assert_int_with_valid_value(self) -> None:
        with raises_no_configuration_errors() as loader:
            loader.assert_int(123)

    def test_assert_int_with_invalid_value(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_int(False)

    def test_assert_float_with_valid_value(self) -> None:
        with raises_no_configuration_errors() as loader:
            loader.assert_float(1.23)

    def test_assert_float_with_invalid_value(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_float(False)

    def test_assert_str_with_valid_value(self) -> None:
        with raises_no_configuration_errors() as loader:
            loader.assert_str('Hello, world!')

    def test_assert_str_with_invalid_value(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_str(False)

    def test_assert_list_with_list(self) -> None:
        with raises_no_configuration_errors() as loader:
            loader.assert_list([])

    def test_assert_list_without_list(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_list(False)

    def test_assert_sequence_without_list(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_sequence(
                False,
                loader.assert_str,  # type: ignore
            )

    def test_assert_sequence_with_invalid_item(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError, error_contexts=('0',)) as loader:
            loader.assert_sequence(
                [123],
                loader.assert_str,  # type: ignore
            )

    def test_assert_sequence_with_empty_list(self) -> None:
        with raises_no_configuration_errors() as loader:
            loader.assert_sequence(
                [],
                loader.assert_str,  # type: ignore
            )

    def test_assert_sequence_with_valid_sequence(self) -> None:
        with raises_no_configuration_errors() as loader:
            loader.assert_sequence(
                ['Hello!'],
                loader.assert_str,  # type: ignore
            )

    def test_assert_dict_with_dict(self) -> None:
        with raises_no_configuration_errors() as loader:
            loader.assert_dict({})

    def test_assert_dict_without_dict(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_dict(False)

    def test_assert_required_key_without_dict(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            with loader.assert_required_key(
                False,
                'hello',
                loader.assert_str,  # type: ignore
            ) as (dumped_configuration, valid):
                assert not valid
                assert dumped_configuration is None

    def test_assert_required_key_without_key(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError, error_contexts=('hello',)) as loader:
            with loader.assert_required_key(
                {},
                'hello',
                loader.assert_str,  # type: ignore
            ) as (dumped_configuration, valid):
                assert not valid
                assert dumped_configuration is None

    def test_assert_required_key_with_key(self) -> None:
        with raises_no_configuration_errors() as loader:
            with loader.assert_required_key(
                {'hello': 'World!'},
                'hello',
                loader.assert_str,  # type: ignore
            ) as (dumped_configuration, valid):
                assert valid
                assert 'World!' == dumped_configuration

    def test_assert_optional_key_without_dict(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            with loader.assert_optional_key(
                    False,
                    'hello',
                    loader.assert_str,  # type: ignore
            ) as (dumped_configuration, valid):
                assert not valid
                assert dumped_configuration is None

    def test_assert_optional_key_without_key(self) -> None:
        with raises_no_configuration_errors() as loader:
            with loader.assert_optional_key(
                    {},
                    'hello',
                    loader.assert_str,  # type: ignore
            ) as (dumped_configuration, valid):
                assert not valid
                assert dumped_configuration is None

    def test_assert_optional_key_with_key(self) -> None:
        with raises_no_configuration_errors() as loader:
            with loader.assert_optional_key(
                    {'hello': 'World!'},
                    'hello',
                    loader.assert_str,  # type: ignore
            ) as (dumped_configuration, valid):
                assert valid
                assert 'World!' == dumped_configuration

    def test_assert_mapping_without_dict(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_mapping(
                False,
                loader.assert_str,  # type: ignore
            )

    def test_assert_mapping_with_invalid_value(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError, error_contexts=('hello',)) as loader:
            loader.assert_mapping(
                {'hello': False},
                loader.assert_str,  # type: ignore
            )

    def test_assert_mapping_with_empty_dict(self) -> None:
        with raises_no_configuration_errors() as loader:
            loader.assert_mapping(
                {},
                loader.assert_str,  # type: ignore
            )

    def test_assert_mapping_with_valid_mapping(self) -> None:
        with raises_no_configuration_errors() as loader:
            loader.assert_mapping(
                {'hello': 'World!'},
                loader.assert_str,  # type: ignore
            )

    def test_assert_record_without_fields(self) -> None:
        with pytest.raises(ValueError):
            Loader().assert_record({}, {})

    def test_assert_record_with_optional_fields_without_items(self) -> None:
        with raises_no_configuration_errors() as loader:
            loader.assert_record(
                {},
                {
                    'foo': Field(
                        False,
                        loader.assert_str,  # type: ignore
                    ),
                },
            )

    def test_assert_record_with_optional_fields_with_items(self) -> None:
        tracker = []
        with raises_no_configuration_errors() as loader:
            loader.assert_record(
                {
                    'foo': 'bar',
                },
                {
                    'foo': Field(
                        False,
                        loader.assert_str,  # type: ignore
                        lambda x: tracker.append(x),
                    )
                },
            )
        assert ['bar'] == tracker

    def test_assert_record_with_required_fields_without_items(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_record(
                {},
                {
                    'foo': Field(
                        True,
                        loader.assert_str,  # type: ignore
                    ),
                },
            )

    def test_assert_record_with_required_fields_with_items(self) -> None:
        tracker = []
        with raises_no_configuration_errors() as loader:
            loader.assert_record(
                {
                    'foo': 'bar',
                },
                {
                    'foo': Field(
                        True,
                        loader.assert_str,  # type: ignore
                        lambda x: tracker.append(x),
                    )
                },
            )
        assert ['bar'] == tracker

    def test_assert_path_without_str(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_path(False)

    def test_assert_path_with_valid_path(self) -> None:
        with raises_no_configuration_errors() as loader:
            loader.assert_path('~/../foo/bar')

    def test_assert_directory_path_without_str(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_directory_path(False)

    def test_assert_directory_path_without_existing_path(self) -> None:
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_directory_path('~/../foo/bar')

    def test_assert_directory_path_without_directory_path(self) -> None:
        with NamedTemporaryFile() as f:
            with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
                loader.assert_directory_path(f.name)

    def test_assert_directory_path_with_valid_path(self) -> None:
        with TemporaryDirectory() as directory_path:
            with raises_no_configuration_errors() as loader:
                loader.assert_directory_path(directory_path)
                loader.commit()

    class Instance(ReactiveInstance):
        def __init__(self):
            super().__init__()
            self._some_valid_property = None
            self._some_valid_reactive_property = None
            self.some_valid_attribute = None

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

        @property
        @reactive_property
        def some_valid_reactive_property(self) -> Any:
            return self._some_valid_reactive_property

        @some_valid_reactive_property.setter
        def some_valid_reactive_property(self, value: Any):
            self._some_valid_reactive_property = value

        @property
        def some_invalid_reactive_property(self) -> Any:
            return None

        @some_invalid_reactive_property.setter
        def some_invalid_reactive_property(self, value: Any):
            raise ConfigurationValidationError

    def test_assert_setattr_with_valid_property(self) -> None:
        instance = self.Instance()
        attr_name = 'some_valid_property'
        value = 'Hello, world!'
        with raises_no_configuration_errors() as loader:
            loader.assert_setattr(instance, attr_name, value)
        assert value == instance.some_valid_property

    def test_assert_setattr_with_invalid_property(self) -> None:
        instance = self.Instance()
        # @todo This fails because the GETTER raises a RuntimeError...
        attr_name = 'some_invalid_property'
        value = 'Hello, world!'
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_setattr(instance, attr_name, value)

    def test_assert_setattr_with_valid_reactive_property(self) -> None:
        instance = self.Instance()
        attr_name = 'some_valid_reactive_property'
        value = 'Hello, world!'
        with raises_no_configuration_errors() as loader:
            loader.assert_setattr(instance, attr_name, value)
        assert value == instance.some_valid_reactive_property

    def test_assert_setattr_with_valid_attribute(self) -> None:
        instance = self.Instance()
        attr_name = 'some_valid_attribute'
        value = 'Hello, world!'
        with raises_no_configuration_errors() as loader:
            loader.assert_setattr(instance, attr_name, value)
        assert value == instance.some_valid_attribute

    def test_assert_setattr_with_invalid_reactive_property(self) -> None:
        instance = self.Instance()
        attr_name = 'some_invalid_reactive_property'
        value = 'Hello, world!'
        with raises_configuration_error(error_type=ConfigurationValidationError) as loader:
            loader.assert_setattr(instance, attr_name, value)
