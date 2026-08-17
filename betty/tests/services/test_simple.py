from __future__ import annotations

from betty.prop import HasProps
from betty.services.simple import service


async def test_service__with_asynchronous_service() -> None:
    my_first_service = object()

    class _Owner(HasProps):
        @service
        async def my_first_service(self) -> object:
            return my_first_service

    assert await _Owner().my_first_service is my_first_service


def test_service__with_synchronous_service() -> None:
    my_first_service = object()

    class _Owner(HasProps):
        @service
        def my_first_service(self) -> object:
            return my_first_service

    assert _Owner().my_first_service is my_first_service
