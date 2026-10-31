import pytest
from pytest_mock import MockerFixture

from betty.console import CommandDefinition, ExitCode
from betty.consoles.app import main, run
from betty.test_utils.conftest import IsolatedAppFactory
from betty.test_utils.console import NoOpCommand, new_raising_command


@pytest.mark.parametrize(
    ("expected", "command"),
    [
        (ExitCode.OK, NoOpCommand.definition),
        (ExitCode.ERROR_UNEXPECTED_UNRECOVERABLE, new_raising_command(RuntimeError())),
    ],
)
async def test_run(
    expected: ExitCode,
    command: CommandDefinition,
    isolated_app_factory: IsolatedAppFactory,
) -> None:
    async with isolated_app_factory(plugins={CommandDefinition: [command]}) as app:
        with pytest.raises(SystemExit) as exc_info:
            await run(app, command.id)
    assert exc_info.value.code == expected.value


@pytest.mark.parametrize(
    ("expected", "command"),
    [
        (ExitCode.OK, NoOpCommand.definition),
        (ExitCode.ERROR_UNEXPECTED_UNRECOVERABLE, new_raising_command(RuntimeError())),
    ],
)
def test_main(
    expected: ExitCode,
    command: CommandDefinition,
    isolated_app_factory: IsolatedAppFactory,
    mocker: MockerFixture,
) -> None:
    app = isolated_app_factory(plugins={CommandDefinition: [command]})
    mocker.patch("betty.app.App.new_from_environment", return_value=app)
    mocker.patch("sys.argv", new=["betty", command.id])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == expected.value
