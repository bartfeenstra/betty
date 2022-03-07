from subprocess import CalledProcessError
from tempfile import TemporaryDirectory
from unittest.mock import patch

from parameterized import parameterized

from betty.app import Configuration, App
from betty.asyncio import sync
from betty.npm import _NpmRequirement
from betty.tests import TestCase


class NpmRequirementTest(TestCase):
    @sync
    async def test_check_met(self) -> None:
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            async with App(configuration):
                sut = _NpmRequirement.check()
        self.assertTrue(sut.met)

    @parameterized.expand([
        (CalledProcessError(1, ''),),
        (FileNotFoundError(),),
    ])
    @patch('betty.npm.npm')
    @sync
    async def test_check_unmet(self, e: Exception, m_npm) -> None:
        m_npm.side_effect = e
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://example.com')
            async with App(configuration):
                sut = _NpmRequirement.check()
        self.assertFalse(sut.met)
