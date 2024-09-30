from asyncio import run_coroutine_threadsafe, get_running_loop, run, AbstractEventLoop
from collections.abc import Callable, Awaitable
from concurrent.futures.thread import ThreadPoolExecutor
from typing import TypeVar

_T = TypeVar("_T")


def _await_in_thread(loop: AbstractEventLoop, f: Callable[[], Awaitable[_T]]) -> _T:
    """
    Await something inside a thread, using the main thread's loop.
    """

    print("THIS IS PRINTED")
    return run_coroutine_threadsafe(f(), loop).result()


def _await_to_thread(pool: ThreadPoolExecutor, f: Callable[[], Awaitable[_T]]) -> _T:
    """
    Await something by moving it to a thread.
    """
    return pool.submit(_await_in_thread, get_running_loop(), f).result()


async def _async_main(pool: ThreadPoolExecutor) -> None:
    """
    Run the main application, which is asynchronous.
    """

    # Eventually, the application calls a function that due to its nature (maybe a third-party API) is synchronous.
    _some_sync_function(pool)


def _sync_main() -> None:
    with ThreadPoolExecutor() as pool:
        run(_async_main(pool))


def _some_sync_function(pool: ThreadPoolExecutor) -> None:
    # This synchronous function then has to call a function that is asynchronous.
    result = _await_to_thread(pool, _some_async_function)
    assert result == 123


async def _some_async_function() -> int:
    print("BUT THIS IS NOT PRINTED")
    return 123


if __name__ == "__main__":
    _sync_main()
