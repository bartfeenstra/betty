from betty.attrs.owner import OwnerAttr
from betty.attrs.proxy import ProxyAttr
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition


class TestProxyAttr:
    def test_field__without_field(self) -> None:
        proxied = OwnerAttr(DataDefinition(label="-"))
        assert ProxyAttr(proxied=proxied).field is proxied.field

    def test_field__with_field(self) -> None:
        field = FieldDefinition(DataDefinition(label="-"))
        assert (
            ProxyAttr(field, proxied=OwnerAttr(DataDefinition(label="-"))).field
            is field
        )
