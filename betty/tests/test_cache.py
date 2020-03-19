from os import path
from tempfile import TemporaryDirectory
from time import sleep
from unittest import TestCase

from betty.cache import FileCache, CacheMissError


class FileCacheTest(TestCase):
    _KEY = 'WhatOpensALock'
    _VALUE = 'YouFoundMe'

    def setUp(self) -> None:
        self._cache_directory = TemporaryDirectory()
        # Set the cache directory path to a non-existent directory, to ensure the SUT can lazily create it.
        cache_directory_path = path.join(self._cache_directory.name, 'SomeSubDirectory')
        self._sut = FileCache(cache_directory_path)

    def tearDown(self) -> None:
        self._cache_directory.cleanup()

    def test_get_with_unknown_key_should_raise_error(self) -> None:
        with self.assertRaises(CacheMissError):
            self._sut.get(self._KEY)

    def test_get_with_ttl_and_expired_item_should_raise_error(self) -> None:
        with self.assertRaises(CacheMissError):
            self._sut.set(self._KEY, self._VALUE)
            sleep(1)
            self.assertEqual(self._VALUE, self._sut.get(self._KEY, 0))

    def test_get_without_ttl_should_return(self) -> None:
        self._sut.set(self._KEY, self._VALUE)
        self.assertEqual(self._VALUE, self._sut.get(self._KEY))

    def test_delete(self) -> None:
        self._sut.set(self._KEY, self._VALUE)
        self._sut.delete(self._KEY)
        with self.assertRaises(CacheMissError):
            self._sut.get(self._KEY)

    def test_with_scope(self) -> None:
        unscoped_value = 'IamNotTheValueYouAreLookingFor'
        self._sut.set(self._KEY, unscoped_value)
        sut = self._sut.with_scope('Scope')
        sut.set(self._KEY, self._VALUE)
        self.assertEqual(self._VALUE, sut.get(self._KEY))
