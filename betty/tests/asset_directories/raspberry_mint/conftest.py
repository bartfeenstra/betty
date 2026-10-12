import pytest

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.project import Project
from betty.test_utils.conftest import AssertJinja


@pytest.fixture
async def assert_raspberry_mint_jinja_file(
    assert_jinja_file: AssertJinja,
) -> AssertJinja:
    """
    Return an assertion to render a Raspberry Mint template file.
    """
    Project.asset_directories.add_init_plugins(
        assert_jinja_file.project, raspberry_mint
    )
    return assert_jinja_file
