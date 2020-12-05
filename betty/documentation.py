import logging
import os
import shutil
from os import path
from contextlib import suppress
from subprocess import CalledProcessError
from tempfile import TemporaryDirectory

from betty import subprocess


def build(output_directory_path: str) -> None:
    with suppress(FileExistsError):
        os.makedirs(output_directory_path)
    with TemporaryDirectory() as working_directory_path:
        # shutil.copytree() got its dirs_exist_ok parameter in Python 3.8, so for compatibility with earlier versions
        # we use a non-existent source directory.
        source_directory_path = path.join(working_directory_path, 'source')
        shutil.copytree(path.join(path.dirname(path.dirname(__file__)), 'documentation'), source_directory_path)
        try:
            subprocess.run(['sphinx-apidoc', '--force', '--separate', '-d', '999', '-o', source_directory_path, 'betty'])
            subprocess.run(['sphinx-build', source_directory_path, output_directory_path])
        except CalledProcessError as e:
            if e.stderr is not None:
                logging.getLogger().error(e.stderr)
            raise
