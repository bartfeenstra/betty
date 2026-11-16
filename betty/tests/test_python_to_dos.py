from token import COMMENT
from tokenize import tokenize

import pytest

from betty.dirs import root_directory


def test_python_to_dos(subtests: pytest.Subtests) -> None:
    for directory, _directory_names, file_names in (root_directory / "betty").walk():
        for file_name in file_names:
            if file_name.endswith(".py"):
                file = directory / file_name
                with open(file, mode="rb") as f:
                    for (
                        token_type,
                        token,
                        token_start,
                        _token_end,
                        token_line,
                    ) in tokenize(f.readline):
                        if token_type == COMMENT:
                            with subtests.test():
                                assert not "@todo" in token, (
                                    f"Found a stray @todo comment on line {token_start[0]} of {file}: {token_line.strip()}"
                                )
