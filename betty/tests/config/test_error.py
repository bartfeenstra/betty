from betty.config import ConfigurationLoadError
from betty.config.error import ConfigurationError, ConfigurationErrorCollection
from betty.tests.config.test___init__ import assert_configuration_error


class TestConfigurationError:
    def test__str__without_contexts(self) -> None:
        sut = ConfigurationError('Something went wrong!')
        assert 'Something went wrong!' == str(sut)

    def test__str___with_contexts(self) -> None:
        sut = ConfigurationError('Something went wrong!')
        sut = sut.with_context('Somewhere, at some point...')
        sut = sut.with_context('Somewhere else, too...')
        assert 'Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too...' == str(sut)

    def test_with_context(self) -> None:
        sut = ConfigurationError('Something went wrong!')
        sut_with_context = sut.with_context('Somewhere, at some point...')
        assert sut != sut_with_context
        assert sut_with_context.contexts == ('Somewhere, at some point...',)


class TestConfigurationErrorCollection:
    def test__str__without_errors(self) -> None:
        sut = ConfigurationErrorCollection()
        assert '' == str(sut)

    def test__str___with_one_error(self) -> None:
        sut = ConfigurationErrorCollection()
        sut.append(ConfigurationError('Something went wrong!'))
        assert 'Something went wrong!' == str(sut)

    def test__str___with_multiple_errors(self) -> None:
        sut = ConfigurationErrorCollection()
        sut.append(ConfigurationError('Something went wrong!'))
        sut.append(ConfigurationError('Something else went wrong, too!'))
        assert 'Something went wrong!\n\nSomething else went wrong, too!' == str(sut)

    def test__str___with_predefined_contexts(self) -> None:
        sut = ConfigurationErrorCollection()
        sut = sut.with_context('Somewhere, at some point...')
        sut = sut.with_context('Somewhere else, too...')
        error_1 = ConfigurationError('Something went wrong!')
        error_2 = ConfigurationError('Something else went wrong, too!')
        sut.append(error_1)
        sut.append(error_2)
        assert not len(error_1.contexts)
        assert not len(error_2.contexts)
        assert 'Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too...\n\nSomething else went wrong, too!\n- Somewhere, at some point...\n- Somewhere else, too...' == str(sut)

    def test__str___with_postdefined_contexts(self) -> None:
        sut = ConfigurationErrorCollection()
        error_1 = ConfigurationError('Something went wrong!')
        error_2 = ConfigurationError('Something else went wrong, too!')
        sut.append(error_1)
        sut.append(error_2)
        sut = sut.with_context('Somewhere, at some point...')
        sut = sut.with_context('Somewhere else, too...')
        assert not len(error_1.contexts)
        assert not len(error_2.contexts)
        assert 'Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too...\n\nSomething else went wrong, too!\n- Somewhere, at some point...\n- Somewhere else, too...' == str(sut)

    def test_with_context(self) -> None:
        sut = ConfigurationErrorCollection()
        sut_with_context = sut.with_context('Somewhere, at some point...')
        assert sut is not sut_with_context
        assert sut_with_context.contexts == ('Somewhere, at some point...',)

    def test_catch_without_contexts(self) -> None:
        sut = ConfigurationErrorCollection()
        error = ConfigurationLoadError('Help!')
        with sut.catch() as errors:
            raise error
        assert_configuration_error(errors, error=error)
        assert_configuration_error(sut, error=error)

    def test_catch_with_contexts(self) -> None:
        sut = ConfigurationErrorCollection()
        error = ConfigurationLoadError('Help!')
        with sut.catch('Somewhere') as errors:
            raise error
        assert_configuration_error(errors, error=error.with_context('Somewhere'))
        assert_configuration_error(sut, error=error.with_context('Somewhere'))
