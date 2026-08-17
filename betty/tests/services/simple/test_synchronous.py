from __future__ import annotations

from betty.prop import HasProps
from betty.service import Service
from betty.services.simple import SynchronousServiceManager


class TestSynchronousServiceManager:
    def test_get__with_service(self) -> None:
        my_first_service_value = object()

        class _Owner(HasProps):
            my_first_service = SynchronousServiceManager(
                Service(my_first_service_value)
            )

        owner = _Owner()
        assert owner.my_first_service is my_first_service_value

    def test_get__with_factory(self) -> None:
        my_first_service = object()

        class _Owner(HasProps):
            my_first_service = SynchronousServiceManager(lambda _: my_first_service)

        owner = _Owner()
        assert owner.my_first_service is my_first_service
