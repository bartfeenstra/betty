from unittest.mock import AsyncMock

from betty.app import App
from betty.config import write_configuration_file
from betty.project import Project
from betty.test_utils.cli import run
from pytest_mock import MockerFixture


class TestGenerate:
    async def test(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        m_generate = mocker.patch(
            "betty.project.generate.generate", new_callable=AsyncMock
        )
        m_load = mocker.patch("betty.project.load.load", new_callable=AsyncMock)

        async with Project.new_temporary(new_temporary_app) as project:
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            await run(
                new_temporary_app,
                "generate",
                "-c",
                str(project.configuration.configuration_file_path),
            )

            m_load.assert_called_once()
            await_args = m_load.await_args
            assert await_args is not None
            load_args, _ = await_args
            assert (
                load_args[0].configuration.configuration_file_path
                == project.configuration.configuration_file_path.expanduser().resolve()
            )

            m_generate.assert_called_once()
            generate_args, _ = m_generate.call_args
            assert (
                generate_args[0].configuration.configuration_file_path
                == project.configuration.configuration_file_path.expanduser().resolve()
            )
