from __future__ import annotations

from betty.service import ServiceProvider
from betty.service.simple import service
from betty.universe import UNIVERSE


async def test_service__with_asynchronous_service() -> None:
    my_first_service = object()

    class Cls(ServiceProvider):
        @service
        async def my_first_service(self) -> object:
            return my_first_service

    assert await Cls(services=UNIVERSE).my_first_service is my_first_service


def test_service__with_synchronous_service() -> None:
    my_first_service = object()

    class Cls(ServiceProvider):
        @service
        def my_first_service(self) -> object:
            return my_first_service

    assert Cls(services=UNIVERSE).my_first_service is my_first_service
