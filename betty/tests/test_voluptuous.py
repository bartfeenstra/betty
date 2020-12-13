from os import path
from tempfile import TemporaryDirectory

from parameterized import parameterized
from voluptuous import Invalid

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

    def test_with_absolute_path(self):
        with TemporaryDirectory() as directory_path:
            self.assertEqual(directory_path, Path()(directory_path))

    def test_with_expanduser(self):
        self.assertEqual(path.join(path.expanduser('~'), 'foo', 'bar'), Path()(path.join(path.expanduser('~'), 'foo', 'bar')))

    def test_with_relative_path_made_absolute(self):
        with TemporaryDirectory() as directory_path:
            self.assertEqual(path.join(directory_path, 'sibling'), Path()(path.join(directory_path, 'child', '..', 'sibling', '.')))


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
