from asyncio.subprocess import Process
from pathlib import Path
from shutil import which

import pytest

from betty.file import write
from betty.subprocess import CalledSubprocessError, SubprocessError, run_process
from betty.test_utils.user import StaticUser
from betty.user import Verbosity


class TestCalledSubprocessError:
    def test___str____minimal(self) -> None:
        code = 9
        command = "betty my-first-command --my-first-argument My-First-Argument"
        sut = CalledSubprocessError(code, command, None, None)
        message = str(sut)
        assert str(code) in message
        assert command in message
        assert "stdout" not in message
        assert "stderr" not in message

    def test___str____full(self) -> None:
        code = 9
        command = "betty my-first-command --my-first-argument My-First-Argument"
        stdout = "Hello, Stdout!"
        stderr = "Hello, Stderr!"
        sut = CalledSubprocessError(code, command, stdout, stderr)
        message = str(sut)
        assert str(code) in message
        assert command in message
        assert f"stdout:\n{stdout}" in message
        assert f"stderr:\n{stderr}" in message


_parameterize_shell = pytest.mark.parametrize("shell", [True, False])


@_parameterize_shell
async def test_run_process__without_errors(shell: bool) -> None:
    process = await run_process(["true"], shell=shell, user=StaticUser())
    assert isinstance(process, Process)


@_parameterize_shell
async def test_run_process__without_errors_with_most_verbose(
    shell: bool, tmp_path: Path
) -> None:
    await write(
        tmp_path / "process.py",
        """
from sys import stderr

print('Hello, Stdout!')
print('Hello, Stderr!', file=stderr)
""",
    )
    user = StaticUser()
    user.verbosity = Verbosity.MOST_VERBOSE
    await run_process(["python", str(tmp_path / "process.py")], shell=shell, user=user)
    user.assert_message_debug("stdout:\nHello, Stdout!")
    user.assert_message_debug("stderr:\nHello, Stderr!")


@_parameterize_shell
async def test_run_process__with_errors_without_output(
    shell: bool, tmp_path: Path
) -> None:
    user = StaticUser()
    script_path = tmp_path / "test.py"
    python_script = """
import sys
sys.exit(1)"""
    await write(script_path, python_script)
    with pytest.raises(SubprocessError):
        await run_process(
            [which("python"), "-W", "ignore", str(script_path)],  # ty:ignore[invalid-argument-type]
            shell=shell,
            user=user,
        )
    user.assert_not_message_debug("stdout:\n")
    user.assert_not_message_debug("stderr:\n")


@_parameterize_shell
async def test_run_process__with_errors_with_output(
    shell: bool, tmp_path: Path
) -> None:
    user = StaticUser()
    stdout = "Hello, stdout!"
    stderr = "Hello, stderr!"
    script_path = tmp_path / "test.py"
    python_script = f"""
import sys
print("{stdout}")
print("{stderr}", file=sys.stderr)
sys.exit(1)"""
    await write(script_path, python_script)
    with pytest.raises(SubprocessError):
        await run_process(
            [which("python"), "-W", "ignore", str(script_path)],  # ty:ignore[invalid-argument-type]
            shell=shell,
            user=user,
        )
    user.assert_message_debug(["stdout:", stdout])
    user.assert_message_debug(["stderr:", stderr])


@_parameterize_shell
async def test_run_process__with_command_not_found(shell: bool, tmp_path: Path) -> None:
    with pytest.raises(SubprocessError):
        await run_process(["non-existent-command"], shell=shell, user=StaticUser())
