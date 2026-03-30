from unittest.mock import AsyncMock

from betty.service.provider import ServiceManager
from betty.service.requirement import UnmetServiceRequirement


class TestUnmetServiceRequirement:
    def test_service(self) -> None:
        service = AsyncMock(spec=ServiceManager)
        assert UnmetServiceRequirement(service, "Oops!").service is service
