from typing import override

from betty.descriptor import Descriptor, HasDescriptors


class _DummyInstance(HasDescriptors):
    """
    A typed subclass to ensure descriptors are generic over an instance type.
    """

    def __init__(self):
        self.init_descriptors = []
        super().__init__()


class _DummyDescriptorValue:
    """
    A typed descriptor value type.
    """


class _DummyDescriptor(
    Descriptor[_DummyInstance, tuple[_DummyInstance, _DummyDescriptorValue]]
):
    def __init__(self, value: _DummyDescriptorValue, /):
        self.__value = value

    @override
    def get(
        self, instance: _DummyInstance, /
    ) -> tuple[_DummyInstance, _DummyDescriptorValue]:
        return instance, self.__value

    @override
    def init_descriptor(self, instance: _DummyInstance, /) -> None:
        instance.init_descriptors.append(self)


class TestDescriptor:
    def test___get____class(self) -> None:
        class _Instance(_DummyInstance):
            my_first_descriptor = _DummyDescriptor(_DummyDescriptorValue())

        assert isinstance(_Instance.my_first_descriptor, _DummyDescriptor)
        assert _Instance.my_first_descriptor is _Instance.my_first_descriptor

    def test___get____instance(self) -> None:
        value = _DummyDescriptorValue()

        class _Instance(_DummyInstance):
            my_first_descriptor = _DummyDescriptor(value)

        instance = _Instance()
        assert instance.my_first_descriptor == (instance, value)

    def test_owner(self) -> None:
        class _Instance(_DummyInstance):
            my_first_descriptor = _DummyDescriptor(_DummyDescriptorValue())

        assert _Instance.my_first_descriptor.descriptor_owner is _Instance

    def test_init_descriptor(self) -> None:
        class _Instance(_DummyInstance):
            my_first_descriptor = _DummyDescriptor(_DummyDescriptorValue())

        instance = _Instance()
        assert _Instance.my_first_descriptor in instance.init_descriptors

    def test_name(self) -> None:
        class _Instance(_DummyInstance):
            my_first_descriptor = _DummyDescriptor(_DummyDescriptorValue())

        assert _Instance.my_first_descriptor.descriptor_name == "my_first_descriptor"
