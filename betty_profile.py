import asyncio
import cProfile
import pstats
from pathlib import Path
from tempfile import TemporaryDirectory

import yappi

from betty.app import App
from betty.project.extension.demo.project import create_project
from betty.project.generate import generate
from betty.project.load import load


async def _main_cprofile() -> None:
    profile = cProfile.Profile()
    profile.enable()
    await __main()
    profile.disable()
    stats = pstats.Stats(profile)
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.reverse_order()
    stats.print_stats()


def _ystats_file_path(clock_type: str) -> Path:
    return Path(__file__).parent / f"betty_profile_{clock_type}.ystats"


async def _main_yappi(clock_type: str) -> None:
    file_path = _ystats_file_path(clock_type)
    if file_path.exists():
        stats = yappi.get_func_stats()
        stats.add([file_path])
    else:
        yappi.set_clock_type(clock_type)  # Use set_clock_type("wall") for wall time
        yappi.start()
        await __main()
        yappi.stop()
        stats = yappi.get_func_stats()
        stats.save(file_path)

    stats.sort("tsub", "asc")
    stats.print_all(
        columns={
            0: ("tsub", 10),
            1: ("ttot", 10),
            2: ("tavg", 10),
            3: ("ncall", 10),
            4: ("name", 99),
        }
    )
    # yappi.get_thread_stats().print_all()


async def __main() -> None:
    async with App.new_from_environment() as app, app:
        with TemporaryDirectory() as tmp_path_str:
            project = await create_project(app, Path(tmp_path_str))
            async with project:
                await load(project)
                await generate(project)


if __name__ == "__main__":
    asyncio.run(_main_yappi("cpu"))
