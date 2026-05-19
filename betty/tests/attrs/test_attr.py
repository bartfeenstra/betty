import pytest

from betty.attrs.attr import AttrAttr
from betty.datas.str import StrDefinition
from betty.property import HasProperties


class TestAttrAttr:
    class _Owner(HasProperties):
        my_first_property = AttrAttr(StrDefinition(label="-"))

    def test_get(self) -> None:
        owner = self._Owner()
        with pytest.raises(AttributeError):
            self._Owner.my_first_property.get(owner)

    def test_set(self) -> None:
        owner = self._Owner()
        value = "Hello, world!"
        owner.my_first_property = value
        assert owner.my_first_property == value

    def test_init_owner__with_default(self) -> None:
        value = "Hello, world!"

        class _Owner(HasProperties):
            my_first_property = AttrAttr(
                StrDefinition(label="-"), default=lambda: value
            )

        assert _Owner().my_first_property == value
