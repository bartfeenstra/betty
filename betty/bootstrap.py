"""
Provide Betty bootstrap functionality.
"""
from multiprocessing import set_start_method


def bootstrap() -> None:
    """
    Bootstrap the environment in order to run Betty.
    """
    set_start_method('spawn', True)
