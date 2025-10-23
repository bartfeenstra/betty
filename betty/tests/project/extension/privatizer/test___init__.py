from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.project import Project
from betty.project.extension.privatizer import Privatizer
from betty.test_utils.project.extension import ExtensionTestBase

if TYPE_CHECKING:
    from betty.app import App
    from betty.project.extension import Extension


class TestPrivatizer(ExtensionTestBase):
    @override
    @pytest.fixture
    async def sut(self, temporary_app: App) -> Extension:
        async with Project.new_temporary(temporary_app) as project, project:
            return await Privatizer.new_for_project(project)
