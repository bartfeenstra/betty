from enum import Enum

from betty.datas.enum import EnumDefinition


class EnumDefinitionTestEnum(Enum):
    HELLO_WORLD = "Hello, World!"


class TestEnumDefinition:
    def test_load(self) -> None:
        sut = EnumDefinition(cls=EnumDefinitionTestEnum, label="-")
        assert (
            sut.porter.load(EnumDefinitionTestEnum.HELLO_WORLD.value)
            is EnumDefinitionTestEnum.HELLO_WORLD
        )

    def test_dump(self) -> None:
        sut = EnumDefinition(cls=EnumDefinitionTestEnum, label="-")
        assert (
            sut.porter.dump(EnumDefinitionTestEnum.HELLO_WORLD)
            == EnumDefinitionTestEnum.HELLO_WORLD.value
        )
