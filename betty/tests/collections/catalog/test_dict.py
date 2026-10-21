from typing import Any

from betty.collections.catalog.dict import DictCatalog, FrozenDictCatalog
from betty.pipeline import pipe


class TestFrozenDictCatalog:
    def test___contains__(self) -> None:
        sut = FrozenDictCatalog(str.upper, {"ONE": "one"})
        assert "ONE" in sut

    def test___contains____with_resolved_key(self) -> None:
        sut = FrozenDictCatalog(str.upper, {"TRUE": "True"})
        assert "True" in sut

    def test___contains____with_invalid_value(self) -> None:
        sut = FrozenDictCatalog(str.upper, {"TRUE": "True"})
        assert object() not in sut

    def test___getitem__(self) -> None:
        sut = FrozenDictCatalog(str.upper, {"ONE": "one"})
        assert sut["ONE"] == "one"

    def test___getitem____with_resolved_key(self) -> None:
        sut = FrozenDictCatalog(str.upper, {"TRUE": "True"})
        assert sut[True] == "True"

    def test___iter__(self) -> None:
        sut = FrozenDictCatalog(str.upper, {"ONE": "one"})
        assert list(iter(sut)) == ["one"]

    def test___len__(self) -> None:
        sut = FrozenDictCatalog(str.upper, {"ONE": "one"})
        assert len(sut) == 1

    def test_keys(self) -> None:
        sut = FrozenDictCatalog(str.upper, {"ONE": "one"})
        assert list(sut.keys()) == ["ONE"]


class TestDictCatalog:
    def test_remove(self) -> None:
        sut = DictCatalog(str.upper, ["one"])
        sut.remove("ONE")
        assert not sut

    def test___delitem__(self) -> None:
        sut = DictCatalog(str.upper, ["one"])
        del sut["ONE"]

    def test___delitem____with_resolved_key(self) -> None:
        sut = DictCatalog[str, Any, bool, str](pipe, ["True"], key=str)
        del sut[True]

    def test_add__with_new_key(self) -> None:
        sut = DictCatalog[str, str, str, str](str.upper, [])
        sut.add("one")
        assert sut["ONE"] == "one"

    def test_add__with_existing_key(self) -> None:
        sut = DictCatalog(str.upper, ["one"])
        sut.add("ONE")
        assert sut["ONE"] == "ONE"

    def test_add__with_value_resolver(self) -> None:
        sut = DictCatalog[str, str, str, bool](pipe, [], value=str)
        sut.add(True)
        assert sut["True"] == "True"

    def test_clear(self) -> None:
        sut = DictCatalog(pipe, ["one"])
        sut.clear()
        assert list(sut) == []
