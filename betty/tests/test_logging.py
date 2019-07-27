import io
from logging import Logger, CRITICAL, ERROR, WARNING, INFO, DEBUG
from unittest import TestCase
from unittest.mock import patch

from parameterized import parameterized

from betty.logging import CliHandler


class CliHandlerTest(TestCase):
    @parameterized.expand([
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
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_log(self, expected: str, message: str, level: int, stderr: io.StringIO):
        logger = Logger(__name__)
        logger.addHandler(CliHandler())
        logger.log(level, message)
        self.assertEquals(expected, stderr.getvalue())
