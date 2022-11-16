from betty.config.error import ConfigurationError, ConfigurationErrorCollection


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
        sut: ConfigurationErrorCollection[ConfigurationError] = ConfigurationErrorCollection()
        assert '' == str(sut)

    def test__str___with_one_error(self) -> None:
        sut: ConfigurationErrorCollection[ConfigurationError] = ConfigurationErrorCollection()
        sut.append(ConfigurationError('Something went wrong!'))
        assert 'Something went wrong!' == str(sut)

    def test__str___with_multiple_errors(self) -> None:
        sut: ConfigurationErrorCollection[ConfigurationError] = ConfigurationErrorCollection()
        sut.append(ConfigurationError('Something went wrong!'))
        sut.append(ConfigurationError('Something else went wrong, too!'))
        assert 'Something went wrong!\nSomething else went wrong, too!' == str(sut)

    def test__str___with_predefined_contexts(self) -> None:
        sut: ConfigurationErrorCollection[ConfigurationError] = ConfigurationErrorCollection()
        sut = sut.with_context('Somewhere, at some point...')
        sut = sut.with_context('Somewhere else, too...')
        error_1 = ConfigurationError('Something went wrong!')
        error_2 = ConfigurationError('Something else went wrong, too!')
        sut.append(error_1)
        sut.append(error_2)
        assert not len(error_1.contexts)
        assert not len(error_2.contexts)
        assert 'Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too...\nSomething else went wrong, too!\n- Somewhere, at some point...\n- Somewhere else, too...' == str(sut)

    def test__str___with_postdefined_contexts(self) -> None:
        sut: ConfigurationErrorCollection[ConfigurationError] = ConfigurationErrorCollection()
        error_1 = ConfigurationError('Something went wrong!')
        error_2 = ConfigurationError('Something else went wrong, too!')
        sut.append(error_1)
        sut.append(error_2)
        sut = sut.with_context('Somewhere, at some point...')
        sut = sut.with_context('Somewhere else, too...')
        assert not len(error_1.contexts)
        assert not len(error_2.contexts)
        assert 'Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too...\nSomething else went wrong, too!\n- Somewhere, at some point...\n- Somewhere else, too...' == str(sut)

    def test_with_context(self) -> None:
        sut: ConfigurationErrorCollection[ConfigurationError] = ConfigurationErrorCollection()
        sut_with_context = sut.with_context('Somewhere, at some point...')
        assert sut != sut_with_context
        assert sut_with_context.contexts == ('Somewhere, at some point...',)
