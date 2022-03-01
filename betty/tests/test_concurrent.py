from concurrent.futures.thread import ThreadPoolExecutor

from betty.concurrent import ExceptionRaisingAwaitableExecutor
from betty.tests import TestCase


class ExceptionRaisingAwaitableExecutorTest(TestCase):
    def test_without_exception_should_not_raise(self) -> None:
        def _task():
            return

        with ExceptionRaisingAwaitableExecutor(ThreadPoolExecutor()) as sut:
            sut.submit(_task)

    def test_with_exception_should_raise(self) -> None:
        def _task():
            raise RuntimeError()

        with self.assertRaises(RuntimeError):
            with ExceptionRaisingAwaitableExecutor(ThreadPoolExecutor()) as sut:
                sut.submit(_task)
