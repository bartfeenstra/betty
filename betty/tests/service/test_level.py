from betty.service.level import ServiceLevel


class _TargetType:
    pass


class TestServiceLevel:
    def test_plugins(self) -> None:
        sut = ServiceLevel()
        assert len(list(sut.plugins.types))

    async def test_factory(self) -> None:
        sut = ServiceLevel()
        assert isinstance(await sut.factory.new(_TargetType), _TargetType)
