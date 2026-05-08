"""
The descriptor API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from inspect import getmembers
from typing import TYPE_CHECKING, Any, Self, final, overload, override

if TYPE_CHECKING:
    from collections.abc import Callable


class HasDescriptors:
    """
    An object that has :py:class:`descriptors <betty.descriptor.Descriptors>`.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        # @todo Can we do this once per class? getmembers() is quite slow and we don't want this to impact entities negatively.
        for _, member in getmembers(type(self)):
            # @todo This can result in descriptors to be initialized with the wrong HasDescriptions subclass?
            if isinstance(member, Descriptor):
                member.init_descriptor(self)


class Descriptor[OwnerT: HasDescriptors, GetT](ABC):
    """
    A `descriptor <https://docs.python.org/3/howto/descriptor.html>`_.
    """

    __name: str
    __owner: type[OwnerT]

    def __set_name__(self, owner: type[OwnerT], name: str) -> None:
        self.__owner = owner
        self.__name = name

    @final
    @property
    def descriptor_owner(self) -> type[OwnerT]:
        """
        The descriptor owner.
        """
        return self.__owner

    @final
    @property
    def descriptor_name(self) -> str:
        """
        The descriptor name.
        """
        return self.__name

    def init_descriptor(self, owner: OwnerT, /) -> None:  # noqa: B027
        """
        Initialize the descriptor.
        """

    @overload
    def __get__(self, instance: None, owner: type[OwnerT], /) -> Self:
        pass

    @overload
    def __get__(self, instance: OwnerT, owner: type[OwnerT] | None = None, /) -> GetT:
        pass

    @final
    def __get__(self, instance, owner=None, /):
        if instance is None:
            return self
        return self.get(instance)

    @abstractmethod
    def get(self, owner: OwnerT, /) -> GetT:
        """
        Get the descriptor value from the owner.
        """

    def getter(
        self, getter: Callable[[OwnerT, GetT], GetT], /
    ) -> Descriptor[OwnerT, GetT]:
        """
        Return a new descriptor with the given getter.
        """
        return GetterDescriptor(self, getter)

    def __call__(
        self, getter: Callable[[OwnerT, GetT], GetT], /
    ) -> Descriptor[OwnerT, GetT]:
        """
        Return a new descriptor with the given getter.
        """
        return self.getter(getter)


class GettableDescriptor[OwnerT: HasDescriptors, GetT](Descriptor[OwnerT, GetT], ABC):
    """
    A descriptor that can get a value.
    """

    @overload
    def getter(
        self, getter: Callable[[OwnerT, GetT], GetT], /
    ) -> Descriptor[OwnerT, GetT]:
        pass

    @overload
    def getter[GetterGetT](
        self, getter: Callable[[OwnerT, GetT], GetterGetT], /
    ) -> GettableDescriptor[OwnerT, GetterGetT]:
        pass

    @override
    def getter(self, getter, /):
        return GetterDescriptor(self, getter)

    @override
    def __call__[GetterGetT](
        self, getter: Callable[[OwnerT, GetT], GetterGetT], /
    ) -> Descriptor[OwnerT, GetterGetT]:
        return self.__call__(getter)


class SettableDescriptor[OwnerT: HasDescriptors, GetT, SetT](
    Descriptor[OwnerT, GetT], ABC
):
    """
    A descriptor that can set a value.
    """

    @abstractmethod
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        """
        Set the value on the owner.

        :raises AttributeError: Raised if the descriptor is not settable.
        """

    @final
    def __set__(self, owner: OwnerT, value: SetT) -> None:
        """
        Set the value on the owner.

        :raises AttributeError: Raised if the descriptor is not settable.
        """
        self.set(owner, value)

    @final
    def setter[SetterSetT](
        self, setter: Callable[[OwnerT, SetterSetT], SetT], /
    ) -> SetterDescriptor[OwnerT, GetT, SetterSetT]:
        """
        Return a new descriptor with the given setter.
        """
        return SetterDescriptor(self, setter)


class DeletableDescriptor[OwnerT: HasDescriptors, GetT](Descriptor[OwnerT, GetT], ABC):
    """
    A descriptor that can delete a value.
    """

    @abstractmethod
    def delete(self, owner: OwnerT, /) -> None:
        """
        Delete the value from the owner.

        :raises AttributeError: Raised if the descriptor is not deletable.
        """

    @final
    def __delete__(self, owner: OwnerT) -> None:
        """
        Delete the value from the owner.

        :raises AttributeError: Raised if the descriptor is not deletable.
        """
        self.delete(owner)


class DescriptorProxy[OwnerT: HasDescriptors, GetT](Descriptor[OwnerT, GetT]):
    """
    A descriptor proxy.
    """

    def __init__(self, proxied: Descriptor, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.__proxied = proxied

    @override
    def __set_name__(self, owner: type[OwnerT], name: str) -> None:
        super().__set_name__(owner, name)
        self.__proxied.__set_name__(owner, name)

    @override
    def get(self, owner: OwnerT, /) -> GetT:
        return self.__proxied.get(owner)


class SettableDescriptorProxy[OwnerT: HasDescriptors, GetT, SetT](
    DescriptorProxy[OwnerT, GetT],
    SettableDescriptor[OwnerT, GetT, SetT],
):
    """
    A descriptor that proxies the setting of a value to another upstream descriptor.
    """

    def __init__(
        self,
        proxied: SettableDescriptor[OwnerT, GetT, SetT],
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(proxied, *args, **kwargs)
        self.__settable_proxied = proxied

    @final
    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        self.__settable_proxied.set(owner, value)


class DeletableDescriptorProxy[OwnerT: HasDescriptors, GetT](
    DescriptorProxy[OwnerT, GetT], DeletableDescriptor[OwnerT, GetT]
):
    """
    A descriptor that proxies the deletion of a value to another upstream descriptor.
    """

    def __init__(
        self, proxied: DeletableDescriptor[OwnerT, GetT], *args: Any, **kwargs: Any
    ):
        super().__init__(proxied, *args, **kwargs)
        self.__deletable_proxied = proxied

    @final
    @override
    def delete(self, owner: OwnerT, /) -> None:
        self.__deletable_proxied.delete(owner)


class DataDescriptorProxy(SettableDescriptorProxy, DeletableDescriptorProxy):
    """
    A data descriptor that proxies to another upstream descriptor.
    """


@final
class GetterDescriptor[OwnerT: HasDescriptors, GetT, SetT](
    GettableDescriptor[OwnerT, GetT],
    SettableDescriptorProxy[OwnerT, GetT, SetT],
    DeletableDescriptorProxy[OwnerT, GetT],
):
    """
    Decorate a descriptor with a getter callable.
    """

    def __init__[UpstreamGetT](
        self,
        proxied: Descriptor[OwnerT, UpstreamGetT],
        getter: Callable[[OwnerT, UpstreamGetT], GetT],
        /,
    ):
        super().__init__(
            # @todo Can we type this better?
            proxied,  # ty:ignore[invalid-argument-type]
        )
        self._proxied = proxied
        self._getter = getter

    @override
    def get(self, owner: OwnerT, /) -> GetT:
        return self._getter(owner, self._proxied.get(owner))


@final
class SetterDescriptor[OwnerT: HasDescriptors, GetT, SetT](
    SettableDescriptor[OwnerT, GetT, SetT],
    DeletableDescriptorProxy[OwnerT, GetT],
):
    """
    Decorate a descriptor with a setter callable.
    """

    def __init__[UpstreamSetT](
        self,
        proxied: SettableDescriptor[OwnerT, GetT, UpstreamSetT],
        setter: Callable[[OwnerT, SetT], UpstreamSetT],
        /,
    ):
        super().__init__(
            # @todo Can we type this better?
            proxied,  # ty:ignore[invalid-argument-type]
        )
        self._proxied = proxied
        self._setter = setter

    @override
    def set(self, owner: OwnerT, value: SetT, /) -> None:
        return self._proxied.set(owner, self._setter(owner, value))


@final
class DescriptorNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for a :py:class:`betty.descriptor.Descriptor`.
    """
