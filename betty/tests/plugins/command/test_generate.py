from unittest.mock import AsyncMock

from pytest_mock import MockerFixture

from betty.app import App
from betty.portable.file import dump_file
from betty.project import Project
from betty.test_utils.console import run


class TestGenerate:
    async def test_configure(self, mocker: MockerFixture, isolated_app: App) -> None:
        m_generate = mocker.patch(
            "betty.project.generate.generate", new_callable=AsyncMock
        )
        m_load = mocker.patch("betty.project.load.load", new_callable=AsyncMock)

        async with Project.new_isolated(isolated_app) as project:
            await dump_file(
                project.configuration.data().porter.dump(project.configuration),
                project.configuration_file,
            )
            await run(
                isolated_app,
                "generate",
                "--project",
                str(project.configuration_file),
            )

            m_load.assert_called_once()
            await_args = m_load.await_args
            assert await_args is not None
            load_args, _ = await_args
            assert (
                load_args[0].configuration_file
                == project.configuration_file.expanduser().resolve()
            )

            m_generate.assert_called_once()
            generate_args, _ = m_generate.call_args
            assert (
                generate_args[0].configuration_file
                == project.configuration_file.expanduser().resolve()
            )
