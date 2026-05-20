import pytest

from betty.association import UnresolvedAssociate
from betty.associations.to_many import ToMany
from betty.collections.to_many import ToManyCollection
from betty.entity import Entity, EntityDefinition
from betty.project import Project
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE


@EntityDefinition(
    "owner",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _Owner(Entity):
    associates = ToMany("betty.tests.collections.test_to_many:_Associate", label="-")


@EntityDefinition(
    "associate",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _Associate(Entity):
    pass


@EntityDefinition(
    "bi-owner",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _BiOwner(Entity):
    associates = ToMany(
        "betty.tests.collections.test_to_many:_BiAssociate", "owners", label="-"
    )


@EntityDefinition(
    "bi-associate",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _BiAssociate(Entity):
    owners = ToMany(
        "betty.tests.collections.test_to_many:_BiOwner", "associates", label="-"
    )


class TestToManyCollection:
    def test___contains____without_associates(self) -> None:
        assert _Associate() not in ToManyCollection(_Owner(), _Owner.associates)

    def test___contains____with_associates_without_contains(self) -> None:
        assert _Associate() not in ToManyCollection(
            _Owner(), _Owner.associates, _Associate()
        )

    def test___contains____with_associates_with_contains(self) -> None:
        associate = _Associate()
        assert associate in ToManyCollection(_Owner(), _Owner.associates, associate)

    def test___getitem____without_associates(self) -> None:
        sut = ToManyCollection(_Owner(), _Owner.associates)
        with pytest.raises(IndexError):
            sut[0]

    def test___getitem____with_associates(self) -> None:
        associate = _Associate()
        sut = ToManyCollection(_Owner(), _Owner.associates, associate)
        assert sut[0] is associate

    def test___iter____without_associates(self) -> None:
        sut = ToManyCollection(_Owner(), _Owner.associates)
        with pytest.raises(StopIteration):
            next(iter(sut))

    def test___iter____with_associates(self) -> None:
        associate = _Associate()
        sut = ToManyCollection(_Owner(), _Owner.associates, associate)
        assert list(iter(sut)) == [associate]

    def test___len____without_associates(self) -> None:
        assert len(ToManyCollection(_Owner(), _Owner.associates)) == 0

    def test___len____with_associates(self) -> None:
        assert len(ToManyCollection(_Owner(), _Owner.associates, _Associate())) == 1

    def test_add(self) -> None:
        sut = ToManyCollection(_Owner(), _Owner.associates)
        associate = _Associate()
        sut.add(associate)
        assert sut[0] is associate

    def test_add__existing_associate(self) -> None:
        associate = _Associate()
        sut = ToManyCollection(_Owner(), _Owner.associates, associate)
        sut.add(associate)
        assert sut[0] is associate
        assert len(sut) == 1

    def test_add__bidirectional__without_associate(self) -> None:
        owner = _BiOwner()
        sut = ToManyCollection(owner, _BiOwner.associates)
        associate = _BiAssociate()
        sut.add(lambda: associate)
        assert owner not in associate.owners

    def test_add__bidirectional__with_associate(self) -> None:
        owner = _BiOwner()
        sut = ToManyCollection(owner, _BiOwner.associates)
        associate = _BiAssociate()
        sut.add(associate)
        assert owner in associate.owners

    def test_associate(self) -> None:
        owner = _BiOwner()
        associate = _BiAssociate()
        _Owner.associates.associate(owner, associate)
        assert associate in owner.associates
        assert owner not in associate.owners

    def test_clear(self) -> None:
        sut = ToManyCollection(_Owner(), _Owner.associates, _Associate())
        sut.clear()
        assert not sut

    def test_disassociate(self) -> None:
        owner = _BiOwner()
        associate = _BiAssociate()
        owner.associates.add(associate)
        _Owner.associates.disassociate(owner, associate)
        assert associate not in owner.associates
        assert owner in associate.owners

    def test_remove__without_associates(self) -> None:
        sut = ToManyCollection(_Owner(), _Owner.associates, _Associate())
        sut.remove(_Associate())

    def test_remove__without_associate(self) -> None:
        sut = ToManyCollection(_Owner(), _Owner.associates)
        sut.remove(_Associate())

    def test_remove__with_associate(self) -> None:
        associate = _Associate()
        sut = ToManyCollection(_Owner(), _Owner.associates, associate)
        sut.remove(associate)
        assert associate not in sut

    def test_remove__bidirectional_without_associate(self) -> None:
        sut = ToManyCollection(_BiOwner(), _BiOwner.associates)
        sut.remove(_BiAssociate())

    def test_remove__bidirectional_with_associate(self) -> None:
        owner = _BiOwner()
        associate = _BiAssociate()
        sut = ToManyCollection(owner, _BiOwner.associates, associate)
        sut.remove(associate)
        assert associate not in sut
        assert owner not in associate.owners

    def test_replace__without_associates(self) -> None:
        ToManyCollection(_Owner(), _Owner.associates).replace()

    def test_replace__without_existing_associates(self) -> None:
        sut = ToManyCollection(_Owner(), _Owner.associates)
        associate = _Associate()
        sut.replace(associate)
        assert list(sut) == [associate]

    def test_replace__without_new_associates(self) -> None:
        sut = ToManyCollection(_Owner(), _Owner.associates, _Associate())
        sut.replace()
        assert not sut

    def test_replace__with_existing_and_new_associates(self) -> None:
        sut = ToManyCollection(_Owner(), _Owner.associates, _Associate())
        associate = _Associate()
        sut.replace(associate)
        assert list(sut) == [associate]

    def test_resolve__without_associates(self, isolated_project: Project) -> None:
        ToManyCollection(_Owner(), _Owner.associates).resolve(isolated_project)

    def test_resolve__without_resolvers(self, isolated_project: Project) -> None:
        ToManyCollection(_Owner(), _Owner.associates, _Associate()).resolve(
            isolated_project
        )

    def test_resolve__with_resolver(self, isolated_project: Project) -> None:
        associate = _Associate()
        sut = ToManyCollection(_Owner(), _Owner.associates, lambda: associate)
        sut.resolve(isolated_project)
        assert list(sut) == [associate]

    def test_assert_resolved__without_associations(self) -> None:
        ToManyCollection(_Owner(), _Owner.associates).assert_resolved()

    def test_assert_resolved__with_associate(self) -> None:
        ToManyCollection(_Owner(), _Owner.associates, _Associate())

    def test_assert_resolved__with_resolver(self) -> None:
        sut = sut = ToManyCollection(_Owner(), _Owner.associates, _Associate)
        with pytest.raises(UnresolvedAssociate):
            sut.assert_resolved()
