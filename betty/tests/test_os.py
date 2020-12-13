from os import path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from betty.os import link_or_copy
from betty.tests import TestCase


class LinkOrCopyTest(TestCase):
    def test(self):
        with TemporaryDirectory() as working_directory_path:
            content = 'I will say zis only once.'
            source_path = path.join(working_directory_path, 'source')
            destination_path = path.join(working_directory_path, 'destination')
            with open(source_path, 'a') as f:
                f.write(content)
            link_or_copy(source_path, destination_path)
            with open(destination_path) as f:
                self.assertEqual(content, f.read())

    @patch('os.link')
    def test_with_os_error(self, m_link):
        m_link.side_effect = OSError
        with TemporaryDirectory() as working_directory_path:
            content = 'I will say zis only once.'
            source_path = path.join(working_directory_path, 'source')
            destination_path = path.join(working_directory_path, 'destination')
            with open(source_path, 'a') as f:
                f.write(content)
            link_or_copy(source_path, destination_path)
            with open(destination_path) as f:
                self.assertEqual(content, f.read())
