import fileinput
import json
import subprocess
from os import path
from tempfile import TemporaryDirectory
from unittest import TestCase

import html5lib
import requests

CONTAINER_NAME = IMAGE_NAME = 'betty-test-nginx'

RESOURCES_PATH = path.join(path.dirname(path.dirname(path.dirname(__file__))), 'resources', 'nginx')


class NginxIntegrationTest(TestCase):
    class Container:
        def __init__(self, configuration_template_file_path: str):
            self.address = None
            self._configuration_template_file_path = configuration_template_file_path

        def __enter__(self):
            self._cleanup_environment()
            self._working_directory = TemporaryDirectory()
            with open(path.join(RESOURCES_PATH, self._configuration_template_file_path)) as f:
                configuration = json.load(f)
            output_directory_path = path.join(self._working_directory.name, 'output')
            configuration['output'] = output_directory_path
            configuration_file_path = path.join(self._working_directory.name, 'betty.json')
            with open(configuration_file_path, 'w') as f:
                json.dump(configuration, f)
            subprocess.check_call(['betty', '-c', configuration_file_path, 'generate'])
            with fileinput.input(path.join(output_directory_path, 'nginx.conf'), inplace=True) as f:
                for line in f:
                    if 'root /tmp' in line:
                        print('root /var/www/betty/;')
                    else:
                        print(line)
            subprocess.check_call(['docker', 'run', '--rm', '--name', IMAGE_NAME, '-d', '-v', '%s:/etc/nginx/conf.d/betty.conf:ro' % path.join(output_directory_path, 'nginx.conf'), '-v', '%s:/var/www/betty:ro' % path.join(output_directory_path, 'www'), CONTAINER_NAME])
            self.address = 'http://%s' % subprocess.check_output(['docker', 'inspect', '-f', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}', CONTAINER_NAME]).decode('utf-8').strip()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.address = None
            self._cleanup_environment()
            self._working_directory.cleanup()

        def _cleanup_environment(self):
            try:
                subprocess.check_call(['docker', 'stop', CONTAINER_NAME])
            except subprocess.CalledProcessError:
                # Maybe the container wasn't running, and that is fine.
                pass

    @classmethod
    def setUpClass(cls) -> None:
        subprocess.check_call(['docker', 'build', '-t', IMAGE_NAME, RESOURCES_PATH])

    def assert_betty_html(self, content: str) -> None:
        parser = html5lib.HTMLParser()
        parser.parse(content)
        self.assertIn('Betty', content)

    def test_front_page(self):
        with self.Container('betty-monolingual.json') as c:
            response = requests.get(c.address)
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response.text)

    def test_404(self):
        with self.Container('betty-monolingual.json') as c:
            response = requests.get('%s/non-existent' % c.address)
            self.assertEquals(404, response.status_code)
            self.assert_betty_html(response.text)

    def test_multilingual_front_page(self):
        with self.Container('betty-multilingual.json') as c:
            response = requests.get(c.address)
            self.assertEquals(200, response.status_code)
            self.assertEquals('en', response.headers['Content-Language'])
            self.assertEquals('%s/en/' % c.address, response.url)
            self.assert_betty_html(response.text)

    def test_multilingual_404(self):
        with self.Container('betty-multilingual.json') as c:
            response = requests.get('%s/nl/non-existent' % c.address)
            self.assertEquals(404, response.status_code)
            self.assertEquals('nl', response.headers['Content-Language'])
            self.assert_betty_html(response.text)

    def test_multilingual_content_negotiation_front_page(self):
        with self.Container('betty-multilingual-content-negotiation.json') as c:
            response = requests.get(c.address, headers={
                'Accept-Language': 'nl-NL',
            })
            self.assertEquals(200, response.status_code)
            self.assertEquals('nl', response.headers['Content-Language'])
            self.assertEquals('%s/nl/' % c.address, response.url)
            self.assert_betty_html(response.text)

    def test_multilingual_content_negotiation_404(self):
        with self.Container('betty-multilingual-content-negotiation.json') as c:
            response = requests.get('%s/non-existent' % c.address, headers={
                'Accept-Language': 'nl-NL',
            })
            self.assertEquals(404, response.status_code)
            self.assertEquals('nl', response.headers['Content-Language'])
            self.assert_betty_html(response.text)
