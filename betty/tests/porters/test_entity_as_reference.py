from betty.porters.entity_as_reference import EntityAsReferencePorter
from betty.test_utils.entity import DummyEntityOne


class TestEntityAsReferencePorter:
    def test_load(self) -> None:
        sut = EntityAsReferencePorter()
        loaded = sut.load({
            "type": DummyEntityOne.plugin().id,
            "id": "my-first-entity",
        })
        assert loaded.type == DummyEntityOne.plugin().id
        assert loaded.id == "my-first-entity"

    def test_dump(self) -> None:
        sut = EntityAsReferencePorter()
        assert sut.dump(DummyEntityOne(id="my-first-entity")) == {
            "type": DummyEntityOne.plugin().id,
            "id": "my-first-entity",
        }
