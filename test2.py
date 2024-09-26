import threading
import time
import asyncio
from asyncio import run


# another task coroutine
async def task_coro2():
    # report a message
    print(f">>task2 running")
    # block for a moment
    await asyncio.sleep(2)
    # report a message
    print(f">>task2 done")


# task coroutine
async def task_coro():
    # loop a few times
    for i in range(5):
        # report a message
        print(f">task at {i}")
        # block a moment
        await asyncio.sleep(1)


# function executed in another thread
def task_thread(loop):
    # report a message
    print("thread running")
    # wait a moment
    time.sleep(1)
    # create a coroutine
    coro = task_coro2()
    # execute a coroutine
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    # wait for the task to finish
    future.result()
    # report a message
    print("thread done")


# entry point to the asyncio program
async def main():
    # report a message
    print("asyncio running")
    # get the event loop
    loop = asyncio.get_running_loop()
    # start a new thread
    thread = threading.Thread(target=task_thread, args=(loop,))
    thread.start()
    thread.join()
    # execute a task
    await task_coro()
    # report a message
    print("asyncio done")


if __name__ == "__main__":
    run(main())
