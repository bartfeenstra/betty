from concurrent.futures.thread import ThreadPoolExecutor
from time import sleep

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

    def test_wait_with_submitted_tasks(self) -> None:
        tracker = []

        def _task():
            sleep(1)
            tracker.append(True)
            return True

        sut = ExceptionRaisingAwaitableExecutor(ThreadPoolExecutor())
        future = sut.submit(_task)
        sut.wait()
        self.assertTrue(future.result())
        self.assertEqual([True], tracker)
        future = sut.submit(_task)
        sut.wait()
        self.assertTrue(future.result())
        self.assertEqual([True, True], tracker)

    def test_wait_with_mapped_tasks(self) -> None:
        tracker = []

        def _task(arg):
            sleep(1)
            tracker.append(arg)
            return arg

        sut = ExceptionRaisingAwaitableExecutor(ThreadPoolExecutor())
        future = sut.map(_task, [1])
        sut.wait()
        self.assertEqual([1], list(future))
        self.assertEqual([True], tracker)
        future = sut.map(_task, [2])
        sut.wait()
        self.assertEqual([2], list(future))
        self.assertEqual([1, 2], tracker)
