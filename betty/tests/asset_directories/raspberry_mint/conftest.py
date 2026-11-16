from collections.abc import AsyncGenerator

import pytest
from jinja2 import Environment

from betty.asset_directories import raspberry_mint
from betty.project import Project
from betty.test_utils.conftest import AssertJinja, NewIsolatedProject


@pytest.fixture
async def assert_raspberry_mint_jinja_file(
    new_isolated_project: NewIsolatedProject,
) -> AsyncGenerator[AssertJinja]:
    """
    Return an assertion to render a Raspberry Mint template file.
    """
    async with new_isolated_project() as project:
        Project.asset_directories.add_init_plugins(project, raspberry_mint)
        yield AssertJinja(project, Environment.get_template)
