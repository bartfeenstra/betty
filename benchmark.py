import asyncio
import logging
import multiprocessing
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory

import psutil

from betty.app import App
from betty.project.extension.demo.project import create_project, load_ancestry
from betty.project.generate import generate
from betty.project.load import load


def main() -> None:
    asyncio.run(_main())


async def _main() -> None:
    logging.getLogger("betty").setLevel(logging.DEBUG)

    open_files = []
    process = multiprocessing.Process(target=demo)
    process.start()
    psutil_process = psutil.Process(process.pid)
    while process.is_alive():
        try:
            open_files.extend(psutil_process.open_files())
        except psutil.AccessDenied:
            break
    process.join()

    # Gather unique file handles.
    open_file_fds = defaultdict(set)
    for open_file in open_files:
        open_file_fds[open_file.path].add(open_file.fd)

    # Count unique file handles.
    open_file_stats = {file_path: len(fds) for file_path, fds in open_file_fds.items()}

    # # Sort by file name.
    # for file_path in sorted(open_file_stats.keys()):
    #     print(f"FILE: {file_path} ({open_file_stats[file_path]})\n")

    # Sort by number of file handles, ascending.
    for _ in range(9):
        print("OMITTING FILES THAT HAD BUT 1 HANDLE")
    for file_path, fd_len in sorted(open_file_stats.items(), key=lambda x: x[1]):
        if fd_len > 1:
            print(f"{fd_len}: {file_path}\n")


def demo() -> None:
    asyncio.run(_demo())


async def _demo() -> None:
    async with App.new_from_environment() as app, app:
        with TemporaryDirectory() as tmp_path_str:
            project = await create_project(app, Path(tmp_path_str))
            async with project:
                await load_ancestry(project)
                await load(project)
                await generate(project)


if __name__ == "__main__":
    main()
