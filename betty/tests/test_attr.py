from typing_extensions import override

from betty.attr import Attr, SettableAttr, DeletableAttr


class Value:
    pass


class DummyAttr(Attr[object, Value]):
    @override
    def new_attr(self, instance: object) -> Value:
        return Value()


class DummyAttrInstance:
    attr = DummyAttr("attr")


class TestAttr:
    def test_get_attr(self) -> None:
        instance = DummyAttrInstance()
        assert instance.attr is instance.attr

    async def test___get___without_owner(self) -> None:
        assert isinstance(
            DummyAttrInstance.attr,
            DummyAttr,
        )

    async def test___get___with_owner(self) -> None:
        instance = DummyAttrInstance()
        assert isinstance(instance.attr, Value)


class DummySettableAttr(SettableAttr[object, Value, Value], DummyAttr):
    @override
    def set_attr(self, instance: object, value: Value) -> None:
        setattr(instance, self._attr_name, value)


class DummySettableAttrInstance:
    attr = DummySettableAttr("attr")


class TestSettableAttr:
    async def test___set__(self) -> None:
        instance = DummySettableAttrInstance()
        value = Value()
        instance.attr = value
        assert instance.attr is value


class DummyDeletableAttr(DeletableAttr[object, Value | None, Value | None], DummyAttr):
    @override
    def set_attr(self, instance: object, value: Value | None) -> None:
        setattr(instance, self._attr_name, value)

    @override
    def del_attr(self, instance: object) -> None:
        setattr(instance, self._attr_name, None)


class DummyDeletableAttrInstance:
    attr = DummyDeletableAttr("attr")


class TestDeletableAttr:
    async def test___delete__(self) -> None:
        instance = DummyDeletableAttrInstance()
        value = Value()
        instance.attr = value
        del instance.attr
        assert instance.attr is None
