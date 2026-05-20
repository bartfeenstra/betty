"""
Collections for to-many associations.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, final, overload, override

from betty.association import (
    Associate,
    AssociateResolver,
    UnresolvedAssociate,
    resolve_associate,
)
from betty.collection import MutableCollection
from betty.entity import Entity
from betty.functools import unique

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.associations.to_many import ToMany
    from betty.collection.keyed import MutableKeyedCollection
    from betty.project import Project


@final
class ToManyCollection[OwnerT: Entity, AssociateT: Entity](
    MutableCollection[AssociateT],
    Sequence[AssociateT],
):
    r"""
    A collection of \*-to-many associates.
    """

    _upstream: MutableKeyedCollection[
        tuple[type[AssociateT], str],
        tuple[type[AssociateT], str],
        Associate[OwnerT, AssociateT],
        Associate[OwnerT, AssociateT],
    ]

    def __init__(
        self,
        owner: OwnerT,
        association: ToMany[OwnerT, AssociateT],
        *associates: Associate[OwnerT, AssociateT],
    ):
        self._association = association
        self._owner = owner
        self._unresolved: AssociateResolver[OwnerT, AssociateT] | None = None
        self._associates = []
        self.add(*associates)

    def assert_resolved(self) -> None:
        """
        Assert that all associates in this collection have been resolved.
        """
        if self._unresolved:
            raise UnresolvedAssociate(self._owner, self._association, self._unresolved)

    def associate(self, *associates: AssociateT) -> None:
        """
        Add associates.

        This behaves similar to :py:meth:betty.association.Association.associate` and **MUST** only be called by
        :py:class:`betty.associations.to_many.ToMany`.
        """
        existing_associates = tuple(self)
        for associate in unique(associates):
            assert associate not in existing_associates
            self._associates.append(associate)

    def disassociate(self, *associates: AssociateT) -> None:
        """
        Remove associates.

        This behaves similar to :py:meth:betty.association.Association.disassociate` and **MUST** only be called by
        :py:class:`betty.associations.to_many.ToMany`.
        """
        for associate in associates:
            self._associates.remove(associate)

    def add(self, *associates: Associate[OwnerT, AssociateT]) -> None:
        """
        Add the given associates.
        """
        associate_type = self._association.associate_type
        associate_attr = self._association.associate_attr
        existing_associates = tuple(self)
        for associate in unique(associates):
            if self._association.is_resolver(associate):
                self._unresolved = associate
            elif associate in existing_associates:
                continue
            self._associates.append(associate)
            if isinstance(associate, associate_type) and associate_attr:
                associate_attr.associate(associate, self._owner)

    def remove(self, *associates: AssociateT) -> None:
        """
        Remove the given associates.
        """
        self.assert_resolved()
        associate_attr = self._association.associate_attr
        for associate in associates:
            try:
                self._associates.remove(associate)
            except ValueError:
                continue
            else:
                if associate_attr:
                    associate_attr.disassociate(associate, self._owner)

    @override
    def clear(self) -> None:
        self.remove(*self)

    def replace(self, *associates: Associate[OwnerT, AssociateT]) -> None:
        """
        Replace all associates with the given ones.
        """
        self.clear()
        for associate in associates:
            self.add(associate)

    @override
    def __contains__(self, value: Any) -> bool:
        self.assert_resolved()
        return value in self._associates

    @override
    def __iter__(self) -> Iterator[AssociateT]:
        self.assert_resolved()
        return self._associates.__iter__()

    @override
    def __len__(self) -> int:
        self.assert_resolved()
        return self._associates.__len__()

    @overload
    def __getitem__(self, index: int, /) -> AssociateT:
        pass

    @overload
    def __getitem__(self, index: slice[int | None], /) -> Sequence[AssociateT]:
        pass

    @override
    def __getitem__(self, index, /):
        self.assert_resolved()
        return self._associates.__getitem__(index)

    def resolve(self, project: Project, /) -> None:
        """
        Resolve all associates in this collection.
        """
        for i, associate in enumerate(self._associates):
            if not isinstance(associate, Entity):
                self._associates[i] = resolve_associate(
                    project, self._owner, self._association, associate
                )
        self._unresolved = None
