import os
from os import mkdir
from os.path import join, dirname
from tempfile import TemporaryDirectory

from betty.fs import iterfiles, FileSystem, hashfile
from betty.asyncio import sync
from betty.tests import TestCase


class IterfilesTest(TestCase):
    @sync
    async def test_iterfiles(self):
        with TemporaryDirectory() as path:
            subdirpath = join(path, 'subdir')
            mkdir(subdirpath)
            open(join(path, 'rootfile'), 'a').close()
            open(join(path, '.hiddenrootfile'), 'a').close()
            open(join(subdirpath, 'subdirfile'), 'a').close()
            actual = [actualpath[len(path) + 1:]
                      async for actualpath in iterfiles(path)]
        expected = [
            '.hiddenrootfile',
            'rootfile',
            'subdir/subdirfile',
        ]
        self.assertCountEqual(expected, actual)


class HashfileTest(TestCase):
    def test_hashfile_with_identical_file(self):
        file_path = join(dirname(dirname(__file__)),
                         'assets', 'public', 'static', 'betty-16x16.png')
        self.assertEquals(hashfile(file_path), hashfile(file_path))

    def test_hashfile_with_different_files(self):
        file_path_1 = join(dirname(dirname(__file__)),
                           'assets', 'public', 'static', 'betty-16x16.png')
        file_path_2 = join(dirname(dirname(__file__)),
                           'assets', 'public', 'static', 'betty-512x512.png')
        self.assertNotEquals(hashfile(file_path_1), hashfile(file_path_2))


class FileSystemTest(TestCase):
    @sync
    async def test_open(self):
        with TemporaryDirectory() as source_path_1:
            with TemporaryDirectory() as source_path_2:
                with open(join(source_path_1, 'apples'), 'w') as f:
                    f.write('apples')
                with open(join(source_path_2, 'apples'), 'w') as f:
                    f.write('notapples')
                with open(join(source_path_1, 'oranges'), 'w') as f:
                    f.write('oranges')
                with open(join(source_path_2, 'bananas'), 'w') as f:
                    f.write('bananas')

                sut = FileSystem(source_path_1, source_path_2)

                with await sut.open('apples') as f:
                    self.assertEquals('apples', f.read())
                with await sut.open('oranges') as f:
                    self.assertEquals('oranges', f.read())
                with await sut.open('bananas') as f:
                    self.assertEquals('bananas', f.read())

                with self.assertRaises(FileNotFoundError):
                    with await sut.open('mangos'):
                        pass

    @sync
    async def test_open_with_first_file_path_alternative_first_source_path(self):
        with TemporaryDirectory() as source_path_1:
            with TemporaryDirectory() as source_path_2:
                with open(join(source_path_1, 'pinkladies'), 'w') as f:
                    f.write('pinkladies')
                with open(join(source_path_2, 'pinkladies'), 'w') as f:
                    f.write('notpinkladies')
                with open(join(source_path_1, 'apples'), 'w') as f:
                    f.write('notpinkladies')
                with open(join(source_path_2, 'apples'), 'w') as f:
                    f.write('notpinkladies')

                sut = FileSystem(source_path_1, source_path_2)

                with await sut.open('pinkladies', 'apples') as f:
                    self.assertEquals('pinkladies', f.read())

    @sync
    async def test_open_with_first_file_path_alternative_second_source_path(self):
        with TemporaryDirectory() as source_path_1:
            with TemporaryDirectory() as source_path_2:
                with open(join(source_path_2, 'pinkladies'), 'w') as f:
                    f.write('pinkladies')
                with open(join(source_path_1, 'apples'), 'w') as f:
                    f.write('notpinkladies')
                with open(join(source_path_2, 'apples'), 'w') as f:
                    f.write('notpinkladies')

                sut = FileSystem(source_path_1, source_path_2)

                with await sut.open('pinkladies', 'apples') as f:
                    self.assertEquals('pinkladies', f.read())

    @sync
    async def test_open_with_second_file_path_alternative_first_source_path(self):
        with TemporaryDirectory() as source_path_1:
            with TemporaryDirectory() as source_path_2:
                with open(join(source_path_1, 'apples'), 'w') as f:
                    f.write('apples')
                with open(join(source_path_2, 'apples'), 'w') as f:
                    f.write('notapples')

                sut = FileSystem(source_path_1, source_path_2)

                with await sut.open('pinkladies', 'apples') as f:
                    self.assertEquals('apples', f.read())

    @sync
    async def test_copy2(self):
        with TemporaryDirectory() as source_path_1:
            with TemporaryDirectory() as source_path_2:
                with open(join(source_path_1, 'apples'), 'w') as f:
                    f.write('apples')
                with open(join(source_path_2, 'apples'), 'w') as f:
                    f.write('notapples')
                with open(join(source_path_1, 'oranges'), 'w') as f:
                    f.write('oranges')
                with open(join(source_path_2, 'bananas'), 'w') as f:
                    f.write('bananas')

                with TemporaryDirectory() as destination_path:
                    sut = FileSystem(source_path_1, source_path_2)

                    await sut.copy2('apples', destination_path)
                    await sut.copy2('oranges', destination_path)
                    await sut.copy2('bananas', destination_path)

                    with await sut.open(join(destination_path, 'apples')) as f:
                        self.assertEquals('apples', f.read())
                    with await sut.open(join(destination_path, 'oranges')) as f:
                        self.assertEquals('oranges', f.read())
                    with await sut.open(join(destination_path, 'bananas')) as f:
                        self.assertEquals('bananas', f.read())

                    with self.assertRaises(FileNotFoundError):
                        await sut.copy2('mangos', destination_path)

    @sync
    async def test_copytree(self):
        with TemporaryDirectory() as source_path_1:
            os.makedirs(join(source_path_1, 'basket'))
            with TemporaryDirectory() as source_path_2:
                os.makedirs(join(source_path_2, 'basket'))
                with open(join(source_path_1, 'basket', 'apples'), 'w') as f:
                    f.write('apples')
                with open(join(source_path_2, 'basket', 'apples'), 'w') as f:
                    f.write('notapples')
                with open(join(source_path_1, 'basket', 'oranges'), 'w') as f:
                    f.write('oranges')
                with open(join(source_path_2, 'basket', 'bananas'), 'w') as f:
                    f.write('bananas')

                with TemporaryDirectory() as destination_path:
                    sut = FileSystem(source_path_1, source_path_2)

                    await sut.copytree('', destination_path)

                    with await sut.open(join(destination_path, 'basket', 'apples')) as f:
                        self.assertEquals('apples', f.read())
                    with await sut.open(join(destination_path, 'basket', 'oranges')) as f:
                        self.assertEquals('oranges', f.read())
                    with await sut.open(join(destination_path, 'basket', 'bananas')) as f:
                        self.assertEquals('bananas', f.read())
