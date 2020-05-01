from contextlib import suppress
from tempfile import TemporaryDirectory

import betty


def patch_cache(f):
    def _patch_cache(*args, **kwargs):
        original_cache_directory_path = betty._CACHE_DIRECTORY_PATH
        cache_directory = TemporaryDirectory()
        betty._CACHE_DIRECTORY_PATH = cache_directory.name
        try:
            f(*args, **kwargs)
        finally:
            betty._CACHE_DIRECTORY_PATH = original_cache_directory_path
            # Pythons 3.6 and 3.7 do not allow the temporary directory to have been removed already.
            with suppress(FileNotFoundError):
                cache_directory.cleanup()

    return _patch_cache
