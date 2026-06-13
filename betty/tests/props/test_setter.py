from pytest_mock import MockerFixture

from betty.datas.aggregate.record import FieldDefinition
from betty.datas.str import StrDefinition
from betty.prop import HasProps, Prop
from betty.props.setter import SetterProp


class TestSetterProp:
    def test_set(self, mocker: MockerFixture) -> None:
        def _setter(value: bool) -> str:
            return str(value)

        m_proxied = mocker.MagicMock(spec=Prop)
        m_proxied.field = FieldDefinition(StrDefinition(label="-"))
        sut = SetterProp(_setter, proxied=m_proxied)
        owner = HasProps()
        sut.set(owner, True)
        m_proxied.set.assert_called_once_with(owner, "True")
