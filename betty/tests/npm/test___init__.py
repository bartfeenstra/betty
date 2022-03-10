from subprocess import CalledProcessError
from unittest.mock import patch

from parameterized import parameterized

from betty.app import App
from betty.npm import _NpmRequirement
from betty.tests import TestCase


class NpmRequirementTest(TestCase):
    def test_check_met(self) -> None:
        with App():
            sut = _NpmRequirement.check()
        self.assertTrue(sut.met)

    @parameterized.expand([
        (CalledProcessError(1, ''),),
        (FileNotFoundError(),),
    ])
    @patch('betty.npm.npm')
    def test_check_unmet(self, e: Exception, m_npm) -> None:
        m_npm.side_effect = e
        with App():
            sut = _NpmRequirement.check()
        self.assertFalse(sut.met)
