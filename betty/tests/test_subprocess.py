from subprocess import CompletedProcess, CalledProcessError

from betty import subprocess
from betty.tests import TestCase


class RunTest(TestCase):
    def test_without_errors(self):
        process = subprocess.run(['true'])
        self.assertIsInstance(process, CompletedProcess)

    def test_with_errors(self):
        with self.assertRaises(CalledProcessError):
            subprocess.run(['false'])
