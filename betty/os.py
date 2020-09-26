import os
from contextlib import contextmanager


@contextmanager
def chdir(directory_path: str) -> None:
    owd = os.getcwd()
    try:
        os.chdir(directory_path)
        yield
    finally:
        os.chdir(owd)
