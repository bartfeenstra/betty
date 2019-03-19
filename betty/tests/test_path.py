from os import mkdir
from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.path import iterfiles


class PathTest(TestCase):
    def test_iterfiles(self):
        with TemporaryDirectory() as path:
            subdirpath = join(path, 'subdir')
            mkdir(subdirpath)
            open(join(path, 'rootfile'), 'a').close()
            open(join(path, '.hiddenrootfile'), 'a').close()
            open(join(subdirpath, 'subdirfile'), 'a').close()
            actual = [actualpath[len(path) + 1:] for actualpath in iterfiles(path)]
        expected = [
            '.hiddenrootfile',
            'rootfile',
            'subdir/subdirfile',
        ]
        self.assertCountEqual(actual, expected)
