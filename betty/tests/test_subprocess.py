from subprocess import CompletedProcess
from unittest import TestCase

from betty import subprocess


class RunTest(TestCase):
    def test_without_errors(self):
        process = subprocess.run(['true'])
        self.assertIsInstance(process, CompletedProcess)

    def test_with_errors(self):
        with self.assertRaises(RuntimeError):
            subprocess.run(['false'])
