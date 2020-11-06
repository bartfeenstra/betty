from parameterized import parameterized

from betty.importlib import import_any
from betty.tests import TestCase


class ImportAnyTest(TestCase):
    @parameterized.expand([
        (3,),
        ({},),
        (True,),
    ])
    def test_with_invalid_type_should_raise_invalid(self, importable_value):
        with self.assertRaises(ImportError):
            import_any(importable_value)

    def test_with_unknown_module_should_raise_invalid(self):
        with self.assertRaises(ImportError):
            import_any('foo.bar.Baz')

    def test_with_unknown_type_should_raise_invalid(self):
        with self.assertRaises(ImportError):
            import_any('%s.Foo' % self.__module__)

    def test_with_importable_should_return(self):
        self.assertEqual(self.__class__, import_any('%s.%s' % (self.__module__, self.__class__.__name__)))
