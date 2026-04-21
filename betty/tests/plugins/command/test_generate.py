from json import dumps
from pathlib import Path
from unittest.mock import AsyncMock

from pytest_mock import MockerFixture

from betty.app import App
from betty.file import write
from betty.project.data import ProjectConfiguration
from betty.test_utils.console import run


class TestGenerate:
    async def test_configure(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        m_generate = mocker.patch(
            "betty.project.generate.generate", new_callable=AsyncMock
        )
        m_load = mocker.patch("betty.load.load", new_callable=AsyncMock)

        configuration = ProjectConfiguration(title="Betty", url="https://example.com")
        await write(
            tmp_path / "betty.json",
            dumps(configuration.data().porter.dump(configuration)),
        )
        await run(
            isolated_app,
            "generate",
            "--project",
            str(tmp_path / "betty.json"),
        )

        m_load.assert_called_once()
        await_args = m_load.await_args
        assert await_args is not None
        load_args, _ = await_args
        assert load_args[0].directory.resolve() == tmp_path.resolve()

        m_generate.assert_called_once()
        generate_args, _ = m_generate.call_args
        assert generate_args[0].directory.resolve() == tmp_path.resolve()
