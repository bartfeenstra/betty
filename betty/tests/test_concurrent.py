from concurrent.futures.thread import ThreadPoolExecutor
from time import sleep

import pytest

from betty.concurrent import ExceptionRaisingAwaitableExecutor


class TestExceptionRaisingAwaitableExecutor:
    def test_without_exception_should_not_raise(self) -> None:
        def _task():
            return

        with ExceptionRaisingAwaitableExecutor(ThreadPoolExecutor()) as sut:
            sut.submit(_task)

    def test_with_exception_should_raise(self) -> None:
        def _task():
            raise RuntimeError()

        with pytest.raises(RuntimeError):
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
        assert future.result() is True
        assert [True] == tracker
        future = sut.submit(_task)
        sut.wait()
        assert future.result() is True
        assert [True, True] == tracker

    def test_wait_with_mapped_tasks(self) -> None:
        tracker = []

        def _task(arg):
            sleep(1)
            tracker.append(arg)
            return arg

        sut = ExceptionRaisingAwaitableExecutor(ThreadPoolExecutor())
        future = sut.map(_task, [1])
        sut.wait()
        assert [1] == list(future)
        assert [True] == tracker
        future = sut.map(_task, [2])
        sut.wait()
        assert [2] == list(future)
        assert [1, 2] == tracker
