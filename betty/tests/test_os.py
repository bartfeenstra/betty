from pathlib import Path
from tempfile import TemporaryDirectory

from pytest_mock import MockerFixture

from betty.os import link_or_copy


async def test_link_or_copy() -> None:
    with TemporaryDirectory() as working_directory_str:
        working_directory = Path(working_directory_str)
        content = "I will say zis only once."
        source_path = working_directory / "source"
        destination_path = working_directory / "destination"
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(content)
        await link_or_copy(source_path, destination_path)
        with open(destination_path, encoding="utf-8") as f:
            assert f.read() == content


async def test_link_or_copy__with_os_error(mocker: MockerFixture) -> None:
    m_link = mocker.patch("os.link")
    m_link.side_effect = OSError
    with TemporaryDirectory() as working_directory_str:
        working_directory = Path(working_directory_str)
        content = "I will say zis only once."
        source_path = working_directory / "source"
        destination_path = working_directory / "destination"
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(content)
        await link_or_copy(source_path, destination_path)
        with open(destination_path, encoding="utf-8") as f:
            assert f.read() == content
