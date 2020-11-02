from concurrent.futures.thread import ThreadPoolExecutor
from unittest import TestCase

from betty.concurrent import ExceptionRaisingExecutor


class ExceptionRaisingExecutorTest(TestCase):
    def test_without_exception_should_not_raise(self) -> None:
        def _task():
            return

        with ExceptionRaisingExecutor(ThreadPoolExecutor()) as sut:
            sut.submit(_task)

    def test_with_exception_should_raise(self) -> None:
        def _task():
            raise RuntimeError()

        with self.assertRaises(RuntimeError):
            with ExceptionRaisingExecutor(ThreadPoolExecutor()) as sut:
                sut.submit(_task)
