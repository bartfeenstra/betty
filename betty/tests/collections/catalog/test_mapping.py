from betty.collections.catalog.mapping import MappingCatalog, MutableMappingCatalog
from betty.pipeline import pipe


class TestMappingCatalog:
    def test_resolve_key(self) -> None:
        sut = MappingCatalog({}, key=str.lower)
        assert sut.resolve_key("ONE") == "one"

    def test___contains__(self) -> None:
        sut = MappingCatalog({"ONE": "one"})
        assert "ONE" in sut

    def test___contains____with_invalid_value(self) -> None:
        sut = MappingCatalog({"TRUE": "True"})
        assert object() not in sut

    def test___getitem__(self) -> None:
        sut = MappingCatalog({"ONE": "one"})
        assert sut["ONE"] == "one"

    def test___iter__(self) -> None:
        sut = MappingCatalog({"ONE": "one"})
        assert list(iter(sut)) == ["one"]

    def test___len__(self) -> None:
        sut = MappingCatalog({"ONE": "one"})
        assert len(sut) == 1

    def test_keys(self) -> None:
        sut = MappingCatalog({"ONE": "one"})
        assert list(sut.keys()) == ["ONE"]


class TestMutableMappingCatalog:
    def test_resolve_value(self) -> None:
        sut = MutableMappingCatalog({}, pipe, value=str.lower)
        assert sut.resolve_value("ONE") == "one"

    def test_remove(self) -> None:
        sut = MutableMappingCatalog({"ONE": "one"}, str.upper)
        sut.remove("ONE")
        assert not sut

    def test___delitem__(self) -> None:
        sut = MutableMappingCatalog({"ONE": "one"}, str.upper)
        del sut["ONE"]

    def test___delitem____with_resolved_key(self) -> None:
        sut = MutableMappingCatalog({"True": "True"}, pipe, key=str)
        del sut[True]

    def test_add__with_new_key(self) -> None:
        sut = MutableMappingCatalog({}, str.upper)
        sut.add("one")
        assert sut["ONE"] == "one"

    def test_add__with_existing_key(self) -> None:
        sut = MutableMappingCatalog({"ONE": "one"}, str.upper)
        sut.add("ONE")
        assert sut["ONE"] == "ONE"

    def test_add__with_value_resolver(self) -> None:
        sut = MutableMappingCatalog({}, pipe, value=str)
        sut.add(True)
        assert sut["True"] == "True"

    def test_clear(self) -> None:
        sut = MutableMappingCatalog({"one": "one"}, pipe)
        sut.clear()
        assert list(sut) == []
