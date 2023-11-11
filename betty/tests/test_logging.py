import io
from logging import Logger, CRITICAL, ERROR, WARNING, INFO, DEBUG

import pytest
from pytest_mock import MockerFixture

from betty.logging import CliHandler


class TestCliHandler:
    @pytest.mark.parametrize('expected, message, level', [
        ('\033[91mSomething went wrong!\033[0m\n',
         'Something went wrong!', CRITICAL),
        ('\033[91mSomething went wrong!\033[0m\n',
         'Something went wrong!', ERROR),
        ('\033[93mSomething went wrong!\033[0m\n',
         'Something went wrong!', WARNING),
        ('\033[92mSomething went wrong!\033[0m\n',
         'Something went wrong!', INFO),
        ('\033[97mSomething went wrong!\033[0m\n',
         'Something went wrong!', DEBUG),
    ])
    async def test_log(self, expected: str, message: str, level: int, mocker: MockerFixture) -> None:
        m_stderr = mocker.patch('sys.stderr', new_callable=io.StringIO)
        logger = Logger(__name__)
        logger.addHandler(CliHandler())
        logger.log(level, message)
        assert expected == m_stderr.getvalue()
