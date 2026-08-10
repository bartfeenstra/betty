from betty.associations.optional_to_one import OptionalToOne
from betty.associations.to_one import ToOne
from betty.entity import Entity
from betty.project import Project
from betty.test_utils.entity import DummyEntityOne


class _Owner(Entity):
    to_one_associate = ToOne(DummyEntityOne, label="-")
    associate = OptionalToOne(to_one_associate)


class TestOptionalToOne:
    def test_resolve__without_none(self, isolated_project: Project) -> None:
        owner = _Owner()
        associate = DummyEntityOne()
        owner.associate = lambda: associate
        _Owner.associate.resolve(isolated_project, owner)
        assert owner.associate is associate

    def test_resolve__with_none(self, isolated_project: Project) -> None:
        owner = _Owner()
        _Owner.associate.resolve(isolated_project, owner)
        assert owner.associate is None

    def test_associate__without_existing(self) -> None:
        owner = _Owner()
        associate = DummyEntityOne()
        _Owner.associate.associate(owner, associate)
        assert owner.associate is associate

    def test_associate__with_existing(self) -> None:
        owner = _Owner()
        owner.associate = DummyEntityOne()
        associate = DummyEntityOne()
        _Owner.associate.associate(owner, associate)
        assert owner.associate is associate

    def test_disassociate__without_existing(self) -> None:
        owner = _Owner()
        _Owner.associate.disassociate(owner, DummyEntityOne())
        assert owner.associate is None

    def test_disassociate__with_existing(self) -> None:
        owner = _Owner()
        owner.associate = DummyEntityOne()
        _Owner.associate.disassociate(owner, DummyEntityOne())
        assert owner.associate is None

    async def test_dump_linked_data_for__without_associate(
        self, isolated_project: Project
    ) -> None:
        assert (
            await _Owner.associate.dump_linked_data_for(isolated_project, _Owner())
            is None
        )

    async def test_dump_linked_data_for__with_associate(
        self, isolated_project: Project
    ) -> None:
        owner = _Owner()
        owner.associate = DummyEntityOne(id="my-first-associate")
        assert (
            await _Owner.associate.dump_linked_data_for(isolated_project, owner)
            == "/dummy-one/my-first-associate/index.json"
        )

    def test_get_associates__without_associate(self) -> None:
        assert list(_Owner.associate.get_associates(_Owner())) == []

    def test_get_associates__with_associate(self) -> None:
        owner = _Owner()
        associate = DummyEntityOne()
        owner.associate = associate
        assert list(_Owner.associate.get_associates(owner)) == [associate]

    def test_init_owner(self) -> None:
        assert _Owner().associate is None

    def test_is_resolver__without_none(self) -> None:
        assert _Owner.associate.is_resolver(DummyEntityOne)

    def test_is_resolver__with_none(self) -> None:
        assert not _Owner.associate.is_resolver(None)
