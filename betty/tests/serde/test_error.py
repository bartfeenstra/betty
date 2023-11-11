from betty.serde.error import SerdeError, SerdeErrorCollection
from betty.serde.load import LoadError
from betty.tests.serde import assert_error


class TestSerdeError:
    async def test__str__without_contexts(self) -> None:
        sut = SerdeError('Something went wrong!')
        assert 'Something went wrong!' == str(sut)

    async def test__str___with_contexts(self) -> None:
        sut = SerdeError('Something went wrong!')
        sut = sut.with_context('Somewhere, at some point...')
        sut = sut.with_context('Somewhere else, too...')
        assert 'Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too...' == str(sut)

    async def test_with_context(self) -> None:
        sut = SerdeError('Something went wrong!')
        sut_with_context = sut.with_context('Somewhere, at some point...')
        assert sut != sut_with_context
        assert sut_with_context.contexts == ('Somewhere, at some point...',)


class TestConfigurationErrorCollection:
    async def test__str__without_errors(self) -> None:
        sut = SerdeErrorCollection()
        assert '' == str(sut)

    async def test__str___with_one_error(self) -> None:
        sut = SerdeErrorCollection()
        sut.append(SerdeError('Something went wrong!'))
        assert 'Something went wrong!' == str(sut)

    async def test__str___with_multiple_errors(self) -> None:
        sut = SerdeErrorCollection()
        sut.append(SerdeError('Something went wrong!'))
        sut.append(SerdeError('Something else went wrong, too!'))
        assert 'Something went wrong!\n\nSomething else went wrong, too!' == str(sut)

    async def test__str___with_predefined_contexts(self) -> None:
        sut = SerdeErrorCollection()
        sut = sut.with_context('Somewhere, at some point...')
        sut = sut.with_context('Somewhere else, too...')
        error_1 = SerdeError('Something went wrong!')
        error_2 = SerdeError('Something else went wrong, too!')
        sut.append(error_1)
        sut.append(error_2)
        assert not len(error_1.contexts)
        assert not len(error_2.contexts)
        assert 'Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too...\n\nSomething else went wrong, too!\n- Somewhere, at some point...\n- Somewhere else, too...' == str(sut)

    async def test__str___with_postdefined_contexts(self) -> None:
        sut = SerdeErrorCollection()
        error_1 = SerdeError('Something went wrong!')
        error_2 = SerdeError('Something else went wrong, too!')
        sut.append(error_1)
        sut.append(error_2)
        sut = sut.with_context('Somewhere, at some point...')
        sut = sut.with_context('Somewhere else, too...')
        assert not len(error_1.contexts)
        assert not len(error_2.contexts)
        assert 'Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too...\n\nSomething else went wrong, too!\n- Somewhere, at some point...\n- Somewhere else, too...' == str(sut)

    async def test_with_context(self) -> None:
        sut = SerdeErrorCollection()
        sut_with_context = sut.with_context('Somewhere, at some point...')
        assert sut is not sut_with_context
        assert sut_with_context.contexts == ('Somewhere, at some point...',)

    async def test_catch_without_contexts(self) -> None:
        sut = SerdeErrorCollection()
        error = LoadError('Help!')
        with sut.catch() as errors:
            raise error
        assert_error(errors, error=error)
        assert_error(sut, error=error)

    async def test_catch_with_contexts(self) -> None:
        sut = SerdeErrorCollection()
        error = LoadError('Help!')
        with sut.catch('Somewhere') as errors:
            raise error
        assert_error(errors, error=error.with_context('Somewhere'))
        assert_error(sut, error=error.with_context('Somewhere'))
