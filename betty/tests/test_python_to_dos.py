from asyncio import gather, to_thread
from pathlib import Path
from token import COMMENT
from tokenize import tokenize

import pytest

from betty.dirs import ROOT_DIRECTORY


async def test_python_to_dos(subtests: pytest.Subtests) -> None:
    await gather(*[
        to_thread(_test_python_to_dos, directory / file_name, subtests)
        for directory, _directory_names, file_names in (ROOT_DIRECTORY / "betty").walk()
        for file_name in file_names
        if file_name.endswith(".py")
    ])


def _test_python_to_dos(file: Path, subtests: pytest.Subtests) -> None:
    with open(file, mode="rb") as f:
        for token_type, token, token_start, _token_end, token_line in tokenize(
            f.readline
        ):
            if token_type == COMMENT:
                with subtests.test():
                    assert not "@todo" in token, (
                        f"Found a stray @todo comment on line {token_start[0]} of {file}: {token_line.strip()}."
                    )
