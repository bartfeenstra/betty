from __future__ import annotations

from betty.service.provider import Service, ServiceProvider
from betty.service.simple import SynchronousServiceManager
from betty.universe import UNIVERSE


class TestSynchronousServiceManager:
    def test_get__with_service(self) -> None:
        my_first_service_value = object()

        class Cls(ServiceProvider):
            my_first_service = SynchronousServiceManager(
                Service(my_first_service_value)
            )

        service_provider = Cls(services=UNIVERSE)
        assert service_provider.my_first_service is my_first_service_value

    def test_get__with_factory(self) -> None:
        my_first_service = object()

        class Cls(ServiceProvider):
            my_first_service = SynchronousServiceManager(lambda _: my_first_service)

        service_provider = Cls(services=UNIVERSE)
        assert service_provider.my_first_service is my_first_service
