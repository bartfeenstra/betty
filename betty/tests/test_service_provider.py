from betty.service_level import ServiceLevel
from betty.service_provider import ServiceProvider


class TestServiceProvider:
    async def test_new(self) -> None:
        services = ServiceLevel()
        sut = await ServiceProvider.new(services)
        assert isinstance(sut, ServiceProvider)
        assert sut.services is services
