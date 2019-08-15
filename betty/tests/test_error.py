from unittest import TestCase

from betty.error import ExternalContextError


class ExternalContextErrorTest(TestCase):
    def test__str__(self):
        message = 'Something went wrong!'
        context = 'Somewhere, at some point...'
        expected = 'Something went wrong!\n- Somewhere, at some point...'
        sut = ExternalContextError(message)
        sut.add_context(context)
        self.assertEquals(expected, str(sut))
