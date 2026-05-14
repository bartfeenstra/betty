import pytest

from betty.attr import AttrNotInitialized
from betty.attrs.attr import AttrAttr
from betty.datas.str import StrDefinition
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestAttrAttr:
    def test___get__(self) -> None:
        class _Owner:
            my_first_property = AttrAttr(StrDefinition(label=DUMMY_LOCALIZABLE))

        owner = _Owner()
        with pytest.raises(AttrNotInitialized):
            owner.my_first_property  # noqa: B018

    def test_get(self) -> None:
        class _Owner:
            my_first_property = AttrAttr(StrDefinition(label=DUMMY_LOCALIZABLE))

        owner = _Owner()
        with pytest.raises(AttrNotInitialized):
            _Owner.my_first_property.get(owner)

    def test___set__(self) -> None:
        class _Owner:
            my_first_property = AttrAttr(StrDefinition(label=DUMMY_LOCALIZABLE))

        owner = _Owner()
        owner.my_first_property = "my-first-value"
        assert owner.my_first_property == "my-first-value"

    def test___set____with_resolver(self) -> None:
        class _Owner:
            my_first_property = AttrAttr[str, str | bool](
                StrDefinition(label=DUMMY_LOCALIZABLE), resolver=str
            )

        owner = _Owner()
        owner.my_first_property = True
        assert owner.my_first_property == "True"

    def test___set_name__(self) -> None:
        class _Owner:
            my_first_property = AttrAttr(StrDefinition(label=DUMMY_LOCALIZABLE))

        assert _Owner.my_first_property._attr_name == "_my_first_property"

    def test_attr(self) -> None:
        data = StrDefinition(label=DUMMY_LOCALIZABLE)

        class _Owner:
            my_first_property = AttrAttr(data)

        assert _Owner.my_first_property.attr.field("my_first_property").data is data
