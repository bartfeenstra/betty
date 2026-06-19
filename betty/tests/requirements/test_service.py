from unittest.mock import AsyncMock

from betty.requirements.service import UnmetServiceRequirement
from betty.service import ServiceManager


class TestUnmetServiceRequirement:
    def test_service(self) -> None:
        service = AsyncMock(spec=ServiceManager)
        assert UnmetServiceRequirement(service, "Oops!").service is service
