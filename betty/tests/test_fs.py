from pathlib import Path

import aiofiles
import pytest
from aiofiles.tempfile import TemporaryDirectory

from betty.fs import iterfiles, FileSystem, hashfile


class TestIterfiles:
    async def test_iterfiles(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            working_subdirectory_path = working_directory_path / 'subdir'
            working_subdirectory_path.mkdir()
            async with aiofiles.open(working_directory_path / 'rootfile', 'a'):
                pass
            async with aiofiles.open(working_directory_path / '.hiddenrootfile', 'a'):
                pass
            async with aiofiles.open(working_subdirectory_path / 'subdirfile', 'a'):
                pass
            actual = [str(actualpath)[len(str(working_directory_path)) + 1:] async for actualpath in iterfiles(working_directory_path)]
        expected = {
            '.hiddenrootfile',
            'rootfile',
            str(Path('subdir') / 'subdirfile'),
        }
        assert expected == set(actual)


class TestHashfile:
    async def test_hashfile_with_identical_file(self) -> None:
        file_path = Path(__file__).parents[1] / 'assets' / 'public' / 'static' / 'betty-16x16.png'
        assert hashfile(file_path) == hashfile(file_path)

    async def test_hashfile_with_different_files(self) -> None:
        file_path_1 = Path(__file__).parents[1] / 'assets' / 'public' / 'static' / 'betty-16x16.png'
        file_path_2 = Path(__file__).parents[1] / 'assets' / 'public' / 'static' / 'betty-512x512.png'
        assert hashfile(file_path_1) != hashfile(file_path_2)


class TestFileSystem:
    async def test_open(self) -> None:
        async with TemporaryDirectory() as actual_override_directory_path_str:
            actual_override_directory_path = Path(actual_override_directory_path_str)
            async with TemporaryDirectory() as actual_fallback_directory_path_str:
                actual_fallback_directory_path = Path(actual_fallback_directory_path_str)
                async with aiofiles.open(actual_override_directory_path / 'apples', 'w') as f:
                    await f.write('apples')
                async with aiofiles.open(actual_fallback_directory_path / 'apples', 'w') as f:
                    await f.write('notapples')
                async with aiofiles.open(actual_override_directory_path / 'oranges', 'w') as f:
                    await f.write('oranges')
                async with aiofiles.open(actual_fallback_directory_path / 'bananas', 'w') as f:
                    await f.write('bananas')

                sut = FileSystem((actual_override_directory_path, None), (actual_fallback_directory_path, None))

                async with sut.open(Path('apples')) as f:
                    assert 'apples' == await f.read()
                async with sut.open(Path('oranges')) as f:
                    assert 'oranges' == await f.read()
                async with sut.open(Path('bananas')) as f:
                    assert 'bananas' == await f.read()

                with pytest.raises(FileNotFoundError):
                    async with sut.open(Path('mangos')):
                        pass

    async def test_open_with_first_file_path_alternative_first_actual_directory_path(self) -> None:
        async with TemporaryDirectory() as actual_override_directory_path_str:
            actual_override_directory_path = Path(actual_override_directory_path_str)
            async with TemporaryDirectory() as actual_fallback_directory_path_str:
                actual_fallback_directory_path = Path(actual_fallback_directory_path_str)
                async with aiofiles.open(actual_override_directory_path / 'pinkladies', 'w') as f:
                    await f.write('pinkladies')
                async with aiofiles.open(actual_fallback_directory_path / 'pinkladies', 'w') as f:
                    await f.write('notpinkladies')
                async with aiofiles.open(actual_override_directory_path / 'apples', 'w') as f:
                    await f.write('notpinkladies')
                async with aiofiles.open(actual_fallback_directory_path / 'apples', 'w') as f:
                    await f.write('notpinkladies')

                sut = FileSystem((actual_override_directory_path, None), (actual_fallback_directory_path, None))

                async with sut.open(Path('pinkladies'), Path('apples')) as f:
                    assert 'pinkladies' == await f.read()

    async def test_open_with_first_file_path_alternative_second_actual_directory_path(self) -> None:
        async with TemporaryDirectory() as actual_override_directory_path_str:
            actual_override_directory_path = Path(actual_override_directory_path_str)
            async with TemporaryDirectory() as actual_fallback_directory_path_str:
                actual_fallback_directory_path = Path(actual_fallback_directory_path_str)
                async with aiofiles.open(actual_fallback_directory_path / 'pinkladies', 'w') as f:
                    await f.write('pinkladies')
                async with aiofiles.open(actual_override_directory_path / 'apples', 'w') as f:
                    await f.write('notpinkladies')
                async with aiofiles.open(actual_fallback_directory_path / 'apples', 'w') as f:
                    await f.write('notpinkladies')

                sut = FileSystem((actual_override_directory_path, None), (actual_fallback_directory_path, None))

                async with sut.open(Path('pinkladies'), Path('apples')) as f:
                    assert 'pinkladies' == await f.read()

    async def test_open_with_second_file_path_alternative_first_actual_directory_path(self) -> None:
        async with TemporaryDirectory() as actual_override_directory_path_str:
            actual_override_directory_path = Path(actual_override_directory_path_str)
            async with TemporaryDirectory() as actual_fallback_directory_path_str:
                actual_fallback_directory_path = Path(actual_fallback_directory_path_str)
                async with aiofiles.open(actual_override_directory_path / 'apples', 'w') as f:
                    await f.write('apples')
                async with aiofiles.open(actual_fallback_directory_path / 'apples', 'w') as f:
                    await f.write('notapples')

                sut = FileSystem((actual_override_directory_path, None), (actual_fallback_directory_path, None))

                async with sut.open(Path('pinkladies'), Path('apples')) as f:
                    assert 'apples' == await f.read()

    async def test_copy2(self) -> None:
        async with TemporaryDirectory() as actual_override_directory_path_str:
            actual_override_directory_path = Path(actual_override_directory_path_str)
            async with TemporaryDirectory() as actual_fallback_directory_path_str:
                actual_fallback_directory_path = Path(actual_fallback_directory_path_str)
                async with aiofiles.open(actual_override_directory_path / 'apples', 'w') as f:
                    await f.write('apples')
                async with aiofiles.open(actual_fallback_directory_path / 'apples', 'w') as f:
                    await f.write('notapples')
                async with aiofiles.open(actual_override_directory_path / 'oranges', 'w') as f:
                    await f.write('oranges')
                async with aiofiles.open(actual_fallback_directory_path / 'bananas', 'w') as f:
                    await f.write('bananas')

                async with TemporaryDirectory() as destination_path_str:
                    destination_path = Path(destination_path_str)
                    sut = FileSystem((actual_override_directory_path, None), (actual_fallback_directory_path, None))

                    await sut.copy2(Path('apples'), destination_path)
                    await sut.copy2(Path('oranges'), destination_path)
                    await sut.copy2(Path('bananas'), destination_path)

                    async with sut.open(destination_path / 'apples') as f:
                        assert 'apples' == await f.read()
                    async with sut.open(destination_path / 'oranges') as f:
                        assert 'oranges' == await f.read()
                    async with sut.open(destination_path / 'bananas') as f:
                        assert 'bananas' == await f.read()

                    with pytest.raises(FileNotFoundError):
                        await sut.copy2(Path('mangos'), destination_path)

    async def test_copytree(self) -> None:
        async with TemporaryDirectory() as actual_override_directory_path_str:
            actual_override_directory_path = Path(actual_override_directory_path_str)
            (actual_override_directory_path / 'basket').mkdir()
            async with TemporaryDirectory() as actual_fallback_directory_path_str:
                actual_fallback_directory_path = Path(actual_fallback_directory_path_str)
                (actual_fallback_directory_path / 'basket').mkdir()
                async with aiofiles.open(actual_override_directory_path / 'basket' / 'apples', 'w') as f:
                    await f.write('apples')
                async with aiofiles.open(actual_fallback_directory_path / 'basket' / 'apples', 'w') as f:
                    await f.write('notapples')
                async with aiofiles.open(actual_override_directory_path / 'basket' / 'oranges', 'w') as f:
                    await f.write('oranges')
                async with aiofiles.open(actual_fallback_directory_path / 'basket' / 'bananas', 'w') as f:
                    await f.write('bananas')

                async with TemporaryDirectory() as destination_path_str:
                    destination_path = Path(destination_path_str)
                    sut = FileSystem((actual_override_directory_path, None), (actual_fallback_directory_path, None))

                    async for _ in sut.copytree(Path(''), destination_path):
                        pass

                    async with sut.open(destination_path / 'basket' / 'apples') as f:
                        assert 'apples' == await f.read()
                    async with sut.open(destination_path / 'basket' / 'oranges') as f:
                        assert 'oranges' == await f.read()
                    async with sut.open(destination_path / 'basket' / 'bananas') as f:
                        assert 'bananas' == await f.read()

    async def test_iterfiles(self) -> None:
        async with TemporaryDirectory() as actual_override_directory_path_str:
            actual_override_directory_path = Path(actual_override_directory_path_str)
            (actual_override_directory_path / 'basket').mkdir()
            async with TemporaryDirectory() as actual_fallback_directory_path_str:
                actual_fallback_directory_path = Path(actual_fallback_directory_path_str)
                (actual_fallback_directory_path / 'basket').mkdir()
                (actual_override_directory_path / 'basket' / 'apples').touch()
                (actual_fallback_directory_path / 'basket' / 'apples').touch()
                (actual_override_directory_path / 'basket' / 'oranges').touch()
                (actual_fallback_directory_path / 'basket' / 'bananas').touch()

                sut = FileSystem((actual_override_directory_path, None), (actual_fallback_directory_path, None))

                actual = {
                    (fs_file_path, actual_file_path)
                    async for fs_file_path, actual_file_path
                    in sut.iterfiles(Path('basket'))
                }
                expected = {
                    (Path('basket') / 'apples', actual_override_directory_path / 'basket' / 'apples'),
                    (Path('basket') / 'oranges', actual_override_directory_path / 'basket' / 'oranges'),
                    (Path('basket') / 'bananas', actual_fallback_directory_path / 'basket' / 'bananas'),
                }
                assert actual == expected
