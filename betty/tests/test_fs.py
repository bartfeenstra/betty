from pathlib import Path
from tempfile import TemporaryDirectory

from betty.fs import iterfiles, FileSystem, hashfile
from betty.asyncio import sync
from betty.tests import TestCase


class IterfilesTest(TestCase):
    @sync
    async def test_iterfiles(self):
        with TemporaryDirectory() as working_directory_path:
            working_subdirectory_path = Path(working_directory_path) / 'subdir'
            working_subdirectory_path.mkdir()
            open(Path(working_directory_path) / 'rootfile', 'a').close()
            open(Path(working_directory_path) / '.hiddenrootfile', 'a').close()
            open(Path(working_subdirectory_path) / 'subdirfile', 'a').close()
            actual = [str(actualpath)[len(working_directory_path) + 1:] async for actualpath in iterfiles(working_directory_path)]
        expected = [
            '.hiddenrootfile',
            'rootfile',
            str(Path('subdir') / 'subdirfile'),
        ]
        self.assertCountEqual(expected, actual)


class HashfileTest(TestCase):
    def test_hashfile_with_identical_file(self):
        file_path = Path(__file__).parents[1] / 'assets' / 'public' / 'static' / 'betty-16x16.png'
        self.assertEquals(hashfile(file_path), hashfile(file_path))

    def test_hashfile_with_different_files(self):
        file_path_1 = Path(__file__).parents[1] / 'assets' / 'public' / 'static' / 'betty-16x16.png'
        file_path_2 = Path(__file__).parents[1] / 'assets' / 'public' / 'static' / 'betty-512x512.png'
        self.assertNotEquals(hashfile(file_path_1), hashfile(file_path_2))


class FileSystemTest(TestCase):
    @sync
    async def test_open(self):
        with TemporaryDirectory() as source_path_1:
            with TemporaryDirectory() as source_path_2:
                with open(Path(source_path_1) / 'apples', 'w') as f:
                    f.write('apples')
                with open(Path(source_path_2) / 'apples', 'w') as f:
                    f.write('notapples')
                with open(Path(source_path_1) / 'oranges', 'w') as f:
                    f.write('oranges')
                with open(Path(source_path_2) / 'bananas', 'w') as f:
                    f.write('bananas')

                sut = FileSystem((source_path_1, None), (source_path_2, None))

                async with sut.open('apples') as f:
                    self.assertEquals('apples', await f.read())
                async with sut.open('oranges') as f:
                    self.assertEquals('oranges', await f.read())
                async with sut.open('bananas') as f:
                    self.assertEquals('bananas', await f.read())

                with self.assertRaises(FileNotFoundError):
                    async with sut.open('mangos'):
                        pass

    @sync
    async def test_open_with_first_file_path_alternative_first_source_path(self):
        with TemporaryDirectory() as source_path_1:
            with TemporaryDirectory() as source_path_2:
                with open(Path(source_path_1) / 'pinkladies', 'w') as f:
                    f.write('pinkladies')
                with open(Path(source_path_2) / 'pinkladies', 'w') as f:
                    f.write('notpinkladies')
                with open(Path(source_path_1) / 'apples', 'w') as f:
                    f.write('notpinkladies')
                with open(Path(source_path_2) / 'apples', 'w') as f:
                    f.write('notpinkladies')

                sut = FileSystem((source_path_1, None), (source_path_2, None))

                async with sut.open('pinkladies', 'apples') as f:
                    self.assertEquals('pinkladies', await f.read())

    @sync
    async def test_open_with_first_file_path_alternative_second_source_path(self):
        with TemporaryDirectory() as source_path_1:
            with TemporaryDirectory() as source_path_2:
                with open(Path(source_path_2) / 'pinkladies', 'w') as f:
                    f.write('pinkladies')
                with open(Path(source_path_1) / 'apples', 'w') as f:
                    f.write('notpinkladies')
                with open(Path(source_path_2) / 'apples', 'w') as f:
                    f.write('notpinkladies')

                sut = FileSystem((source_path_1, None), (source_path_2, None))

                async with sut.open('pinkladies', 'apples') as f:
                    self.assertEquals('pinkladies', await f.read())

    @sync
    async def test_open_with_second_file_path_alternative_first_source_path(self):
        with TemporaryDirectory() as source_path_1:
            with TemporaryDirectory() as source_path_2:
                with open(Path(source_path_1) / 'apples', 'w') as f:
                    f.write('apples')
                with open(Path(source_path_2) / 'apples', 'w') as f:
                    f.write('notapples')

                sut = FileSystem((source_path_1, None), (source_path_2, None))

                async with sut.open('pinkladies', 'apples') as f:
                    self.assertEquals('apples', await f.read())

    @sync
    async def test_copy2(self):
        with TemporaryDirectory() as source_path_1:
            with TemporaryDirectory() as source_path_2:
                with open(Path(source_path_1) / 'apples', 'w') as f:
                    f.write('apples')
                with open(Path(source_path_2) / 'apples', 'w') as f:
                    f.write('notapples')
                with open(Path(source_path_1) / 'oranges', 'w') as f:
                    f.write('oranges')
                with open(Path(source_path_2) / 'bananas', 'w') as f:
                    f.write('bananas')

                with TemporaryDirectory() as destination_path:
                    sut = FileSystem((source_path_1, None), (source_path_2, None))

                    await sut.copy2('apples', destination_path)
                    await sut.copy2('oranges', destination_path)
                    await sut.copy2('bananas', destination_path)

                    async with sut.open(Path(destination_path) / 'apples') as f:
                        self.assertEquals('apples', await f.read())
                    async with sut.open(Path(destination_path) / 'oranges') as f:
                        self.assertEquals('oranges', await f.read())
                    async with sut.open(Path(destination_path) / 'bananas') as f:
                        self.assertEquals('bananas', await f.read())

                    with self.assertRaises(FileNotFoundError):
                        await sut.copy2('mangos', destination_path)

    @sync
    async def test_copytree(self):
        with TemporaryDirectory() as source_path_1:
            (Path(source_path_1) / 'basket').mkdir()
            with TemporaryDirectory() as source_path_2:
                (Path(source_path_2) / 'basket').mkdir()
                with open(Path(source_path_1) / 'basket' / 'apples', 'w') as f:
                    f.write('apples')
                with open(Path(source_path_2) / 'basket' / 'apples', 'w') as f:
                    f.write('notapples')
                with open(Path(source_path_1) / 'basket' / 'oranges', 'w') as f:
                    f.write('oranges')
                with open(Path(source_path_2) / 'basket' / 'bananas', 'w') as f:
                    f.write('bananas')

                with TemporaryDirectory() as destination_path:
                    sut = FileSystem((source_path_1, None), (source_path_2, None))

                    await sut.copytree('', destination_path)

                    async with sut.open(Path(destination_path) / 'basket' / 'apples') as f:
                        self.assertEquals('apples', await f.read())
                    async with sut.open(Path(destination_path) / 'basket' / 'oranges') as f:
                        self.assertEquals('oranges', await f.read())
                    async with sut.open(Path(destination_path) / 'basket' / 'bananas') as f:
                        self.assertEquals('bananas', await f.read())
