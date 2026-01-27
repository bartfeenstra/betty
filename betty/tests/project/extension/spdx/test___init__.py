from collections.abc import Iterator

import pytest
from typing_extensions import override

from betty.app import App
from betty.project import Extension, Project
from betty.project.extension.spdx import Spdx
from betty.test_utils.project.extension import ExtensionTestBase


class TestSpdx(ExtensionTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> Iterator[Extension]:  # ty:ignore[invalid-return-type]
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            await Spdx.new_for_services(project) as sut,
        ):
            yield sut

    async def test_license_repository(self, sut: Spdx) -> None:
        await sut.license_repository
