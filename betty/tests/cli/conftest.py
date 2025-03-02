import pytest
from betty.app import App
from pytest_mock import MockerFixture


@pytest.fixture
async def new_temporary_app_cli(mocker: MockerFixture, new_temporary_app: App) -> App:
    m_new_from_environment = mocker.AsyncMock()
    m_new_from_environment.__aenter__.return_value = new_temporary_app
    mocker.patch(
        "betty.app.App.new_from_environment", return_value=m_new_from_environment
    )
    return new_temporary_app
