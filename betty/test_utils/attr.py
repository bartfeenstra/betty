"""
Test utilities for :py:mod:`betty.attr`.
"""

from collections.abc import Sequence
from typing import TypeVar, Generic
from typing_extensions import override

from betty.attr import Attr

_InstanceT = TypeVar("_InstanceT")
_ValueT = TypeVar("_ValueT")
_SetT = TypeVar("_SetT")


class AttrTestBase(Generic[_InstanceT, _ValueT]):
    """
    A base class for testing :py:class:`betty.attr.Attr` implementations.
    """

    def get_instances(self) -> tuple[Sequence[_InstanceT], str]:
        """
        Get instances with an attribute under test.

        :return: A 2-tuple with the instances, and the name of the attribute containing the :py:class:`betty.attr.Attr` under test.
        """
        raise NotImplementedError(repr(self))

    def test_get_attr(self) -> None:
        """
        Tests :py:meth:`betty.attr.Attr.get_attr` implementations.
        """
        instances, attr_name = self.get_instances()
        for instance in instances:
            sut = getattr(type(instance), attr_name)
            assert sut.get_attr(instance) is sut.get_attr(instance)

    async def test___get___without_owner(self) -> None:
        """
        Tests ``__get__`` implementations.
        """
        instances, attr_name = self.get_instances()
        for instance in instances:
            assert isinstance(
                getattr(type(instance), attr_name),
                Attr,
            )

    async def test___get___with_owner(self) -> None:
        """
        Tests ``__get__`` implementations.
        """
        instances, attr_name = self.get_instances()
        for instance in instances:
            assert getattr(instance, attr_name) is getattr(instance, attr_name)


class MutableAttrTestBase(
    Generic[_InstanceT, _ValueT, _SetT], AttrTestBase[_InstanceT, _ValueT]
):
    """
    A base class for testing :py:class:`betty.attr.MutableAttr` implementations.
    """

    @override
    def get_instances(self) -> tuple[Sequence[_InstanceT], str]:
        instances, attr_name = self.get_mutable_instances()
        return ([instance for instance, _ in instances], attr_name)

    def get_mutable_instances(
        self,
    ) -> tuple[Sequence[tuple[_InstanceT, Sequence[_SetT]]], str]:
        """
        Get instances with a mutable attribute under test.

        :return: A 2-tuple with the instances, and the name of the attribute containing the :py:class:`betty.attr.MutableAttr` under test.
        """
        raise NotImplementedError(repr(self))

    def assert_eq(self, get_value: _ValueT, set_value: _SetT) -> None:
        """
        Assert that a get value and a set value are equal.
        """
        raise NotImplementedError(repr(self))

    def assert_ne(self, get_value: _ValueT, set_value: _SetT) -> None:
        """
        Assert that a get value and a set value are not equal.
        """
        try:
            self.assert_eq(get_value, set_value)
            raise AssertionError(  # pragma: no cover
                f"get value {get_value} and set value {set_value} were unexpectedly equal"
            )
        except AssertionError:
            return

    async def test___set__(self) -> None:
        """
        Tests ``__set__`` implementations.
        """
        instances, attr_name = self.get_mutable_instances()
        for instance, set_values in instances:
            for set_value in set_values:
                setattr(instance, attr_name, set_value)
                self.assert_eq(getattr(instance, attr_name), set_value)

    def test_set_attr(self) -> None:
        """
        Tests :py:meth:`betty.attr.MutableAttr.set_attr` implementations.
        """
        instances, attr_name = self.get_mutable_instances()
        for instance, set_values in instances:
            for set_value in set_values:
                getattr(type(instance), attr_name).set_attr(instance, set_value)
                self.assert_eq(getattr(instance, attr_name), set_value)

    async def test___delete__(self) -> None:
        """
        Tests ``__delete__`` implementations.
        """
        instances, attr_name = self.get_mutable_instances()
        for instance, set_values in instances:
            # Test deleting any default value.
            delattr(instance, attr_name)
            # Test deleting provided values.
            for set_value in set_values:
                setattr(instance, attr_name, set_value)
                delattr(instance, attr_name)
                self.assert_ne(getattr(instance, attr_name), set_value)

    def test_del_attr(self) -> None:
        """
        Tests :py:meth:`betty.attr.MutableAttr.del_attr` implementations.
        """
        instances, attr_name = self.get_mutable_instances()
        for instance, set_values in instances:
            # Test deleting any default value.
            delattr(instance, attr_name)
            # Test deleting provided values.
            for set_value in set_values:
                setattr(instance, attr_name, set_value)
                getattr(type(instance), attr_name).del_attr(instance)
                self.assert_ne(getattr(instance, attr_name), set_value)

    def test_new_attr(self) -> None:
        """
        Tests :py:meth:`betty.attr.MutableAttr.del_attr` implementations.
        """
        raise NotImplementedError(repr(self))
