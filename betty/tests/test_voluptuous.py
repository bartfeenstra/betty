from os import path

from parameterized import parameterized
from voluptuous import Invalid

from betty import os
from betty.tests import TestCase
from betty.voluptuous import Path, Importable


class PathTest(TestCase):
    @parameterized.expand([
        (3,),
        ({},),
        (True,),
    ])
    def test_with_invalid_type_should_raise_invalid(self, path_value):
        with self.assertRaises(Invalid):
            Path()(path_value)

    @parameterized.expand([
        ('/foo/bar', '/foo/bar'),
        (path.join(path.expanduser('~'), 'foo', 'bar'), '~/foo/bar'),
        (path.join(path.expanduser('~'), 'foo', 'bar'), './foo/bar'),
        (path.join(path.expanduser('~'), 'bar'), './foo/../bar'),
    ])
    def test_with_path_should_return(self, expected: str, path_value: str):
        with os.ChDir(path.expanduser('~')):
            self.assertEqual(expected, Path()(path_value))


class ImportableTest(TestCase):
    @parameterized.expand([
        (3,),
        ({},),
        (True,),
    ])
    def test_with_invalid_type_should_raise_invalid(self, importable_value):
        with self.assertRaises(Invalid):
            Importable()(importable_value)

    def test_with_unknown_module_should_raise_invalid(self):
        with self.assertRaises(Invalid):
            Importable()('foo.bar.Baz')

    def test_with_unknown_type_should_raise_invalid(self):
        with self.assertRaises(Invalid):
            Importable()('%s.Foo' % self.__module__)

    def test_with_importable_should_return(self):
        self.assertEqual(self.__class__, Importable()('%s.%s' % (self.__module__, self.__class__.__name__)))
