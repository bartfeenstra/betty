from collections.abc import Iterable
from typing import override

import pytest

from betty.extension import ExtensionDefinition
from betty.extensions.maps import Maps
from betty.plugin.resolve import ResolvablePluginId
from betty.project.generate import generate
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.extensions.maps import MapsTestBase
from betty.tests.conftest import check_skip_webpack_entry_point_provider


class TestMaps:
    @pytest.mark.order(0)
    @check_skip_webpack_entry_point_provider
    async def test_generate(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(debug=True, extensions=[Maps]) as project:
            await generate(project)
            with open(
                project.www_directory / "js" / "webpack" / "maps.js",
                encoding="utf-8",
            ) as f:
                betty_js = f.read()
            assert Maps.plugin().id in betty_js
            with open(
                project.www_directory / "css" / "webpack" / "main.css",
                encoding="utf-8",
            ) as f:
                betty_css = f.read()
            assert Maps.plugin().id in betty_css


class TestMapsMaps(MapsTestBase):
    @override
    def get_other_extensions(
        self,
    ) -> Iterable[ResolvablePluginId[ExtensionDefinition]]:
        return ()
