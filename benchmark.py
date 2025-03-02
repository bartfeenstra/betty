import asyncio
import multiprocessing
from pathlib import Path
from tempfile import TemporaryDirectory

import psutil

from betty.app import App
from betty.project.extension.demo.project import create_project
from betty.project.generate import generate
from betty.project.load import load


def main() -> None:
    asyncio.run(_main())


async def _main() -> None:
    process = multiprocessing.Process(target=demo)
    process.start()

    psutil_process = psutil.Process(process.pid)
    while process.is_alive():
        try:
            print(psutil_process.open_files())
        except psutil.AccessDenied:
            break
    process.join()


def demo() -> None:
    asyncio.run(_demo())


async def _demo() -> None:
    async with App.new_from_environment() as app, app:
        with TemporaryDirectory() as tmp_path_str:
            project = await create_project(app, Path(tmp_path_str))
            async with project:
                await load(project)
                await generate(project)


if __name__ == "__main__":
    main()
