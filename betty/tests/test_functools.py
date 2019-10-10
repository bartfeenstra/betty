from unittest import TestCase

from betty.functools import passthrough


class PassthroughTest(TestCase):
    def test(self):
        x = 999
        self.assertEquals(x, passthrough(x))
