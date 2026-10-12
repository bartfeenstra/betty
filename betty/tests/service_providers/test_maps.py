from collections.abc import Iterable
from typing import override

import pytest

from betty.definition.id import ResolvableId
from betty.project import Project
from betty.project.generate import generate
from betty.service_provider import ServiceProviderDefinition
from betty.service_providers.maps import Maps
from betty.test_utils.conftest import NewIsolatedProject
from betty.test_utils.service_providers.maps import MapsTestBase
from betty.tests.conftest import check_skip_webpack_entry_point_provider


class TestMaps:
    @pytest.mark.order(0)
    @check_skip_webpack_entry_point_provider
    async def test_generate(self, new_isolated_project: NewIsolatedProject) -> None:
        async with new_isolated_project() as project:
            project.debug = True
            Project.service_providers.add_init_plugins(project, Maps)
            async with project:
                await generate(project)
                with open(
                    project.www_directory / "js" / "webpack" / "maps.js",
                    encoding="utf-8",
                ) as f:
                    betty_js = f.read()
                assert Maps.definition.id in betty_js
                with open(
                    project.www_directory / "css" / "webpack" / "main.css",
                    encoding="utf-8",
                ) as f:
                    betty_css = f.read()
                assert Maps.definition.id in betty_css


class TestMapsMaps(MapsTestBase):
    @override
    def get_other_extensions(
        self,
    ) -> Iterable[ResolvableId[ServiceProviderDefinition]]:
        return ()
