from betty.locale import Str, DEFAULT_LOCALIZER
from betty.serde.error import SerdeError, SerdeErrorCollection
from betty.serde.load import LoadError
from betty.tests.serde import assert_error


class TestSerdeError:
    async def test_localizewithout_contexts(self) -> None:
        sut = SerdeError(Str.plain("Something went wrong!"))
        assert sut.localize(DEFAULT_LOCALIZER) == "Something went wrong!"

    async def test_localize_with_contexts(self) -> None:
        sut = SerdeError(Str.plain("Something went wrong!"))
        sut = sut.with_context(Str.plain("Somewhere, at some point..."))
        sut = sut.with_context(Str.plain("Somewhere else, too..."))
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too..."
        )

    async def test_with_context(self) -> None:
        sut = SerdeError(Str.plain("Something went wrong!"))
        sut_with_context = sut.with_context(Str.plain("Somewhere, at some point..."))
        assert sut != sut_with_context
        assert ["Somewhere, at some point..."] == [
            context.localize(DEFAULT_LOCALIZER) for context in sut_with_context.contexts
        ]


class TestSerdeErrorCollection:
    async def test_localize_without_errors(self) -> None:
        sut = SerdeErrorCollection()
        assert sut.localize(DEFAULT_LOCALIZER) == ""

    async def test_localize_with_one_error(self) -> None:
        sut = SerdeErrorCollection()
        sut.append(SerdeError(Str.plain("Something went wrong!")))
        assert sut.localize(DEFAULT_LOCALIZER) == "Something went wrong!"

    async def test_localize_with_multiple_errors(self) -> None:
        sut = SerdeErrorCollection()
        sut.append(SerdeError(Str.plain("Something went wrong!")))
        sut.append(SerdeError(Str.plain("Something else went wrong, too!")))
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n\nSomething else went wrong, too!"
        )

    async def test_localize_with_predefined_contexts(self) -> None:
        sut = SerdeErrorCollection()
        sut = sut.with_context(Str.plain("Somewhere, at some point..."))
        sut = sut.with_context(Str.plain("Somewhere else, too..."))
        error_1 = SerdeError(Str.plain("Something went wrong!"))
        error_2 = SerdeError(Str.plain("Something else went wrong, too!"))
        sut.append(error_1)
        sut.append(error_2)
        assert not len(error_1.contexts)
        assert not len(error_2.contexts)
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too...\n\nSomething else went wrong, too!\n- Somewhere, at some point...\n- Somewhere else, too..."
        )

    async def test_localize_with_postdefined_contexts(self) -> None:
        sut = SerdeErrorCollection()
        error_1 = SerdeError(Str.plain("Something went wrong!"))
        error_2 = SerdeError(Str.plain("Something else went wrong, too!"))
        sut.append(error_1)
        sut.append(error_2)
        sut = sut.with_context(Str.plain("Somewhere, at some point..."))
        sut = sut.with_context(Str.plain("Somewhere else, too..."))
        assert not len(error_1.contexts)
        assert not len(error_2.contexts)
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "Something went wrong!\n- Somewhere, at some point...\n- Somewhere else, too...\n\nSomething else went wrong, too!\n- Somewhere, at some point...\n- Somewhere else, too..."
        )

    async def test_with_context(self) -> None:
        sut = SerdeErrorCollection()
        sut_with_context = sut.with_context(Str.plain("Somewhere, at some point..."))
        assert sut is not sut_with_context
        assert ["Somewhere, at some point..."] == [
            context.localize(DEFAULT_LOCALIZER) for context in sut_with_context.contexts
        ]

    async def test_catch_without_contexts(self) -> None:
        sut = SerdeErrorCollection()
        error = LoadError(Str.plain("Help!"))
        with sut.catch() as errors:
            raise error
        assert_error(errors, error=error)
        assert_error(sut, error=error)

    async def test_catch_with_contexts(self) -> None:
        sut = SerdeErrorCollection()
        error = LoadError(Str.plain("Help!"))
        with sut.catch(Str.plain("Somewhere")) as errors:
            raise error
        assert_error(errors, error=error.with_context(Str.plain("Somewhere")))
        assert_error(sut, error=error.with_context(Str.plain("Somewhere")))
