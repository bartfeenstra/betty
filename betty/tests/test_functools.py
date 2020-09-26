from unittest import TestCase

from betty.functools import sync


class SyncTest(TestCase):
    def test_call_coroutinefunction_should_return_result(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        async def _async():
            return expected
        actual = sync(_async())
        self.assertEqual(expected, actual)

    def test_call_decorated_coroutinefunction_should_return_result(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        @sync
        async def _async():
            return expected
        actual = _async()
        self.assertEqual(expected, actual)
