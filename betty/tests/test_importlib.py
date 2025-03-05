import pytest

from betty.importlib import import_any


async def test_import_any__with_unknown_module_should_raise_invalid() -> None:
    with pytest.raises(ImportError):
        import_any("foo.bar:Baz")


async def test_import_any__with_unknown_type_should_raise_invalid() -> None:
    with pytest.raises(ImportError):
        import_any(
            f"{test_import_any__with_unknown_type_should_raise_invalid.__module__}.Foo"
        )


async def test_import_any__with_importable_should_return() -> None:
    assert (
        import_any(
            f"{test_import_any__with_importable_should_return.__module__}:{test_import_any__with_importable_should_return.__name__}"
        )
        is test_import_any__with_importable_should_return
    )
