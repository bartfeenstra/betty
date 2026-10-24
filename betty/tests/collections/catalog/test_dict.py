from typing import Any

from betty.collections.catalog.dict import DictCatalog, FrozenDictCatalog
from betty.pipeline import pipe


class TestFrozenDictCatalog:
    def test___contains__(self) -> None:
        sut = FrozenDictCatalog(
            {"ONE": "one"}, key_resolver=lambda key: str(key).upper()
        )
        assert "ONE" in sut

    def test___contains____with_resolved_key(self) -> None:
        sut = FrozenDictCatalog(
            {"TRUE": "True"}, key_resolver=lambda key: str(key).upper()
        )
        assert True in sut

    def test___contains____with_invalid_value(self) -> None:
        sut = FrozenDictCatalog(
            {"TRUE": "True"}, key_resolver=lambda key: str(key).upper()
        )
        assert object() not in sut

    def test___getitem__(self) -> None:
        sut = FrozenDictCatalog({"ONE": "one"})
        assert sut["ONE"] == "one"

    def test___getitem____with_resolved_key(self) -> None:
        sut = FrozenDictCatalog(
            {"TRUE": "True"}, key_resolver=lambda key: str(key).upper()
        )
        assert sut[True] == "True"

    def test___iter__(self) -> None:
        sut = FrozenDictCatalog({"ONE": "one"})
        assert list(iter(sut)) == ["one"]

    def test___len__(self) -> None:
        sut = FrozenDictCatalog({"ONE": "one"})
        assert len(sut) == 1

    def test_keys(self) -> None:
        sut = FrozenDictCatalog({"ONE": "one"})
        assert list(sut.keys()) == ["ONE"]


class TestDictCatalog:
    def test_remove(self) -> None:
        sut = DictCatalog(["one"], key=lambda value: value.upper())
        sut.remove("ONE")
        assert not sut

    def test___delitem__(self) -> None:
        sut = DictCatalog(["one"], key=lambda value: value.upper())
        del sut["ONE"]

    def test___delitem____with_resolved_key(self) -> None:
        sut = DictCatalog[str, Any, bool, str](["True"], key=pipe, key_resolver=str)
        del sut[True]

    def test_add__with_new_key(self) -> None:
        sut = DictCatalog[str, str, str, str]([], key=lambda value: value.upper())
        sut.add("one")
        assert sut["ONE"] == "one"

    def test_add__with_existing_key(self) -> None:
        sut = DictCatalog(["one"], key=lambda value: value.upper())
        sut.add("ONE")
        assert sut["ONE"] == "ONE"

    def test_add__with_value_resolver(self) -> None:
        sut = DictCatalog[str, str, str, bool]([], key=pipe, value_resolver=str)
        sut.add(True)
        assert sut["True"] == "True"

    def test_clear(self) -> None:
        sut = DictCatalog(["one"], key=pipe)
        sut.clear()
        assert list(sut) == []
