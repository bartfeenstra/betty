from betty.error import ContextError


class TestContextError:
    def test__str__(self):
        message = 'Something went wrong!'
        context = 'Somewhere, at some point...'
        expected = 'Something went wrong!\n- Somewhere, at some point...'
        sut = ContextError(message)
        sut.add_context(context)
        assert expected == str(sut)
