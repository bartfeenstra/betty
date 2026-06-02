import pytest

from betty.attrs.attr import AttrAttr
from betty.datas.str import StrDefinition
from betty.prop import HasProps


class TestAttrAttr:
    class _Owner(HasProps):
        my_first_attr = AttrAttr(StrDefinition(label="-"))

    def test_get(self) -> None:
        owner = self._Owner()
        with pytest.raises(AttributeError):
            self._Owner.my_first_attr.get(owner)

    def test_set(self) -> None:
        owner = self._Owner()
        value = "Hello, world!"
        owner.my_first_attr = value
        assert owner.my_first_attr == value
