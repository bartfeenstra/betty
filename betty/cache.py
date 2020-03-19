from copy import copy
from os import path, unlink, makedirs
from time import time
from typing import Any, Optional


class CacheMissError(RuntimeError):
    pass


class Cache:
    def with_scope(self, key_prefix: str) -> 'Cache':
        raise NotImplementedError

    def set(self, key: str, value: Any) -> None:
        raise NotImplementedError

    def get(self, key: str, ttl: Optional[int] = None) -> Any:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError


class FileCache(Cache):
    def __init__(self, cache_directory_path: str):
        self._cache_directory_path = cache_directory_path
        makedirs(cache_directory_path, exist_ok=True)

    def with_scope(self, scope: str) -> Cache:
        cache = copy(self)
        cache._cache_directory_path = path.join(self._cache_directory_path, scope)
        makedirs(cache._cache_directory_path, exist_ok=True)
        return cache

    def set(self, key: str, value: Any) -> None:
        fpath = path.join(self._cache_directory_path, key)
        with open(fpath, 'w') as f:
            f.write(value)

    def get(self, key: str, ttl: Optional[int] = None) -> Any:
        fpath = path.join(self._cache_directory_path, key)
        try:
            if ttl is not None and path.getmtime(fpath) + ttl < time():
                raise CacheMissError
            with open(fpath) as f:
                return f.read()
        except FileNotFoundError:
            raise CacheMissError

    def delete(self, key: str) -> None:
        fpath = path.join(self._cache_directory_path, key)
        unlink(fpath)
