from asyncio import run_coroutine_threadsafe, get_running_loop, run, AbstractEventLoop
from collections.abc import Callable, Awaitable
from threading import Thread


async def _some_other_async_function() -> None:
    print("BUT THIS IS NOT PRINTED")


def _helper(loop: AbstractEventLoop, f: Callable[[], Awaitable[None]]) -> None:
    print("THIS IS PRINTED")
    run_coroutine_threadsafe(f(), loop).result()


def _some_sync_function(loop: AbstractEventLoop) -> None:
    thread = Thread(target=_helper, args=[loop, _some_other_async_function])
    thread.start()
    thread.join()


async def _async_main() -> None:
    _some_sync_function(get_running_loop())


if __name__ == "__main__":
    run(_async_main())
