import pytest

from betty.importlib import import_any


class TestImportAny:
    @pytest.mark.parametrize('importable_value', [
        3,
        {},
        True,
    ])
    def test_with_invalid_type_should_raise_invalid(self, importable_value):
        with pytest.raises(ImportError):
            import_any(importable_value)

    def test_with_unknown_module_should_raise_invalid(self):
        with pytest.raises(ImportError):
            import_any('foo.bar.Baz')

    def test_with_unknown_type_should_raise_invalid(self):
        with pytest.raises(ImportError):
            import_any('%s.Foo' % self.__module__)

    def test_with_importable_should_return(self):
        assert self.__class__ == import_any(f'{self.__module__}.{self.__class__.__name__}')
