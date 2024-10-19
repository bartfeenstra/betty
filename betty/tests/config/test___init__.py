from json import loads, dumps
from pathlib import Path

import aiofiles
import pytest
from typing_extensions import override

from betty.assertion import assert_int
from betty.assertion.error import AssertionFailed
from betty.config import (
    Configurable,
    assert_configuration_file,
    write_configuration_file,
    Configuration,
)
from betty.error import FileNotFound
from betty.serde.dump import Dump
from betty.test_utils.config import DummyConfiguration


class TestConfiguration:
    class _DummyConfiguration(Configuration):
        def __init__(self, value: int):
            self.value = value

        @override
        def load(self, dump: Dump) -> None:
            self.value = assert_int()(dump)

        @override
        def dump(self) -> Dump:
            return self.value

    def test_update(self) -> None:
        sut = self._DummyConfiguration(123)
        value = 456
        other = self._DummyConfiguration(value)
        sut.update(other)
        assert sut.value == value


class TestConfigurable:
    class _DummyConfigurable(Configurable[DummyConfiguration]):
        def __init__(self, configuration: DummyConfiguration | None = None):
            if configuration is not None:
                self._configuration = configuration

    def test_configuration_without_configuration(self) -> None:
        sut = self._DummyConfigurable()
        with pytest.raises(RuntimeError):
            sut.configuration  # noqa B018

    def test_configuration_with_configuration(self) -> None:
        configuration = DummyConfiguration()
        sut = self._DummyConfigurable(configuration)
        assert sut.configuration is configuration


class TestAssertConfigurationFile:
    class _LoadingDummyConfiguration(DummyConfiguration):
        loaded_dump: Dump

        @override
        def load(self, dump: Dump) -> None:
            self.loaded_dump = dump

    async def test_with_file_not_found(self, tmp_path: Path) -> None:
        configuration = self._LoadingDummyConfiguration()
        configuration_file_path = tmp_path / "config.json"
        assertion = await assert_configuration_file(configuration)
        with pytest.raises(FileNotFound):
            assertion(configuration_file_path)

    async def test_with_invalid_configuration(self, tmp_path: Path) -> None:
        configuration = self._LoadingDummyConfiguration()
        configuration_file_path = tmp_path / "config.json"
        async with aiofiles.open(configuration_file_path, "w") as f:
            await f.write("this is not valid JSON")
        assertion = await assert_configuration_file(configuration)
        with pytest.raises(AssertionFailed):
            assertion(configuration_file_path)

    async def test_with_valid_configuration(self, tmp_path: Path) -> None:
        configuration = self._LoadingDummyConfiguration()
        configuration_file_path = tmp_path / "config.json"
        dump = {"hello": "world!"}
        async with aiofiles.open(configuration_file_path, "w") as f:
            await f.write(dumps(dump))
        assertion = await assert_configuration_file(configuration)
        assertion(configuration_file_path)
        assert configuration.loaded_dump == dump


class TestWriteConfigurationFile:
    class _DumpingDummyConfiguration(DummyConfiguration):
        @override
        def dump(self) -> Dump:
            return {
                "Hello": "world!",
            }

    async def test(self, tmp_path: Path) -> None:
        configuration = self._DumpingDummyConfiguration()
        configuration_file_path = tmp_path / "config.json"
        await write_configuration_file(configuration, configuration_file_path)
        async with aiofiles.open(configuration_file_path) as f:
            file_contents = await f.read()
        expected = {
            "Hello": "world!",
        }
        assert loads(file_contents) == expected
