from betty.datas.entity_as_reference import EntityAsReferenceDefinition
from betty.test_utils.entity import DummyEntityOne


class TestEntityAsReferenceDefinition:
    def test_porter_load(self) -> None:
        sut = EntityAsReferenceDefinition(label="-")
        loaded = sut.porter.load(
            {
                "type": DummyEntityOne.plugin().id,
                "id": "my-first-entity",
            },
        )
        assert loaded.type == DummyEntityOne.plugin().id
        assert loaded.id == "my-first-entity"

    def test_porter_dump(self) -> None:
        sut = EntityAsReferenceDefinition(label="-")
        assert sut.porter.dump(DummyEntityOne(id="my-first-entity")) == {
            "type": DummyEntityOne.plugin().id,
            "id": "my-first-entity",
        }
