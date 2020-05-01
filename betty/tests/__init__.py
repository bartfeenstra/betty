from tempfile import TemporaryDirectory

import betty


def patch_cache(f):
    def _patch_cache(*args, **kwargs):
        original_cache_directory_path = betty._CACHE_DIRECTORY_PATH
        with TemporaryDirectory() as cache_directory_path:
            try:
                betty._CACHE_DIRECTORY_PATH = cache_directory_path
                f(*args, **kwargs)
            finally:
                betty._CACHE_DIRECTORY_PATH = original_cache_directory_path

    return _patch_cache
