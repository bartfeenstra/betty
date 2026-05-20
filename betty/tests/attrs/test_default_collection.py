from collections.abc import Iterable, MutableSequence
from typing import override

from betty.attrs.collection_attr import CollectionAttrAttr
from betty.attrs.default_collection import DefaultCollectionAttr
from betty.datas.aggregate.collection import CollectionDefinition
from betty.datas.str import StrDefinition
from betty.indicator.selector import Index
from betty.property import HasProperties


class _CollectionDefinition(
    CollectionDefinition[MutableSequence[str], Iterable[str], Index]
):
    def __init__(self):
        super().__init__(
            label="-", item=StrDefinition(label="-"), factory=lambda: ["Hello, world!"]
        )

    @override
    def replace(self, data: MutableSequence[str], values: Iterable[str], /) -> None:
        data.clear()
        data.extend(values)


class TestDefaultCollectionAttr:
    def test_init_owner(self) -> None:
        default = ["Hello, my other world!"]

        class _Owner(HasProperties):
            my_first_property = DefaultCollectionAttr(
                CollectionAttrAttr(_CollectionDefinition()), lambda: default
            )

        assert _Owner().my_first_property == default

    def test_omit_dump__with_default(self) -> None:
        default = ["Hello, my other world!"]

        class _Owner(HasProperties):
            my_first_property = DefaultCollectionAttr(
                CollectionAttrAttr(_CollectionDefinition()), lambda: default
            )

        assert _Owner.my_first_property.field.omit_dump(_Owner(), default)

    def test_omit_dump__with_proxied_false(self) -> None:
        class _Owner(HasProperties):
            my_first_property = DefaultCollectionAttr(
                CollectionAttrAttr(_CollectionDefinition(), omit_dump=lambda _: False),
                lambda: [""],
            )

        assert not _Owner.my_first_property.field.omit_dump(_Owner(), "Hello, world!")

    def test_omit_dump__with_proxied_true(self) -> None:
        class _Owner(HasProperties):
            my_first_property = DefaultCollectionAttr(
                CollectionAttrAttr(_CollectionDefinition(), omit_dump=lambda _: True),
                lambda: [""],
            )

        assert _Owner.my_first_property.field.omit_dump(_Owner(), "Hello, world!")
