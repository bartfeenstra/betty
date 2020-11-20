from betty.asyncio import sync
from betty.tests import TestCase


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

    def test_call_decorated_function_should_return_result(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        @sync
        def _sync():
            return expected
        actual = _sync()
        self.assertEqual(expected, actual)

    def test_call_decorated_callable_method_should_return_result(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        class _Sync:
            @sync
            def __call__(self, *args, **kwargs):
                return expected
        actual = _Sync()()
        self.assertEqual(expected, actual)

    def test_call_decorated_callable_coroutinemethod_should_return_result(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        class _Sync:
            @sync
            async def __call__(self, *args, **kwargs):
                return expected
        actual = _Sync()()
        self.assertEqual(expected, actual)

    def test_call_wrapped_callable_object_should_return_result(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        class _Sync:
            def __call__(self, *args, **kwargs):
                return expected
        actual = sync(_Sync())()
        self.assertEqual(expected, actual)

    def test_call_wrapped_coroutinecallable_object_should_return_result(self) -> None:
        expected = 'Hello, oh asynchronous, world!'

        class _Sync:
            async def __call__(self, *args, **kwargs):
                return expected
        actual = sync(_Sync())()
        self.assertEqual(expected, actual)

    def test_unsychronizable(self) -> None:
        with self.assertRaises(ValueError):
            sync(True)
