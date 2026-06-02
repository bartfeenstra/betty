from pytest_mock import MockerFixture

from betty.attr import Attr
from betty.attrs.setter import SetterAttr
from betty.datas.aggregate.record import FieldDefinition
from betty.datas.str import StrDefinition
from betty.prop import HasProps


class TestSetterAttr:
    def test_set(self, mocker: MockerFixture) -> None:
        def _setter(value: bool) -> str:
            return str(value)

        m_proxied = mocker.MagicMock(spec=Attr)
        m_proxied.field = FieldDefinition(StrDefinition(label="-"))
        sut = SetterAttr(m_proxied, _setter)
        owner = HasProps()
        sut.set(owner, True)
        m_proxied.set.assert_called_once_with(owner, "True")
