from __future__ import annotations

from asyncio import get_running_loop, run_coroutine_threadsafe, run
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Awaitable, TypeVar, ParamSpec, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

_T = TypeVar("_T")
_P = ParamSpec("_P")

THREAD_POOL = ThreadPoolExecutor()


def wait_to_thread(
    f: Callable[_P, Awaitable[_T]], *args: _P.args, **kwargs: _P.kwargs
) -> _T:
    loop = get_running_loop()

    def _wait_to_thread():
        print("PRE CORO THREADSAFE")
        coroutine = f(*args, **kwargs)
        return run_coroutine_threadsafe(coroutine, loop).result()

    return THREAD_POOL.submit(_wait_to_thread).result()


async def main_async() -> None:
    print("THE END")


def main_sync() -> None:
    wait_to_thread(main_async)
    print("POST WAIT TO THREAD")


async def main() -> None:
    main_sync()


if __name__ == "__main__":
    run(main())
