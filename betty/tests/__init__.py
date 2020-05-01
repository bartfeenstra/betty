from tempfile import TemporaryDirectory

import betty


def patch_cache(f):
    def _patch_cache(*args, **kwargs):
        try:
            original_cache_directory_path = betty._CACHE_DIRECTORY_PATH
            cache_directory = TemporaryDirectory()
            betty._CACHE_DIRECTORY_PATH = cache_directory.name
            f(*args, **kwargs)
        finally:
            betty._CACHE_DIRECTORY_PATH = original_cache_directory_path
            cache_directory.cleanup()

    return _patch_cache
