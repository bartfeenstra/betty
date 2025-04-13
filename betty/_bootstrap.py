from asyncio import BaseEventLoop
from multiprocessing import set_start_method
from typing import Any

_bootstrapped = False


if not _bootstrapped:
    _bootstrapped = True

    _original_shutdown_default_executor = BaseEventLoop.shutdown_default_executor

    async def _shutdown_default_executor(
        loop: BaseEventLoop, *args: Any, **kwargs: Any
    ) -> None:
        try:
            await _original_shutdown_default_executor(loop, *args, **kwargs)
        except RuntimeError as error:
            # Work around a bug in Python 3.12 that will randomly cause a RuntimeError with the
            # following message to be raised.
            if "can't create new thread at interpreter shutdown" not in str(error):
                raise

    BaseEventLoop.shutdown_default_executor = _shutdown_default_executor  # type: ignore[assignment, callable-functiontype, method-assign, misc]

    # Avoid `fork` so as not to start worker processes with unneeded resources.
    # Use `spawn`, which is the Python 3.14 default.
    set_start_method("spawn", force=True)
