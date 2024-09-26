from asyncio import run_coroutine_threadsafe, get_running_loop, run
from threading import Thread


async def main_async() -> None:
    foo()
    pass


def _main_async(loop) -> None:
    run_coroutine_threadsafe(main_async(), loop).result()


def main_sync() -> None:
    thread = Thread(target=_main_async, args=[get_running_loop()])
    thread.start()
    thread.join()


async def main() -> None:
    main_sync()


if __name__ == "__main__":
    run(main())
