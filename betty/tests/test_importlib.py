import pytest

from betty.importlib import import_any


class TestImportAny:
    def test_with_unknown_module_should_raise_invalid(self) -> None:
        with pytest.raises(ImportError):
            import_any('foo.bar.Baz')

    def test_with_unknown_type_should_raise_invalid(self) -> None:
        with pytest.raises(ImportError):
            import_any('%s.Foo' % self.__module__)

    def test_with_importable_should_return(self) -> None:
        assert self.__class__ == import_any(f'{self.__module__}.{self.__class__.__name__}')
