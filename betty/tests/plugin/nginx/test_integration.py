import json
import subprocess
from os import path
from tempfile import TemporaryDirectory
from unittest import TestCase

import html5lib
import jsonschema
import requests
from requests import Response

from betty.plugin.nginx import DOCKER_PATH

CONTAINER_NAME = IMAGE_NAME = 'betty-test-nginx'

RESOURCES_PATH = path.join(path.dirname(path.dirname(
    path.dirname(__file__))), 'resources', 'nginx')


class NginxTest(TestCase):
    class Container:
        def __init__(self, configuration_template_file_path: str):
            self.address = None
            self._configuration_template_file_path = configuration_template_file_path

        def __enter__(self):
            self._cleanup_environment()
            self._working_directory = TemporaryDirectory()
            with open(path.join(RESOURCES_PATH, self._configuration_template_file_path)) as f:
                configuration = json.load(f)
            output_directory_path = path.join(
                self._working_directory.name, 'output')
            configuration['output'] = output_directory_path
            configuration_file_path = path.join(
                self._working_directory.name, 'betty.json')
            with open(configuration_file_path, 'w') as f:
                json.dump(configuration, f)
            subprocess.check_call(
                ['betty', '-c', configuration_file_path, 'generate'])
            subprocess.check_call(['docker', 'run', '--rm', '--name', CONTAINER_NAME, '-d', '-v',
                                   '%s:/etc/nginx/conf.d/betty.conf:ro' % path.join(output_directory_path,
                                                                                    'nginx', 'nginx.conf'), '-v',
                                   '%s:/var/www/betty:ro' % path.join(output_directory_path, 'www'), IMAGE_NAME])
            self.address = 'http://%s' % subprocess.check_output(
                ['docker', 'inspect', '-f', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}',
                 CONTAINER_NAME]).decode('utf-8').strip()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.address = None
            # self._cleanup_environment()
            # self._working_directory.cleanup()

        def _cleanup_environment(self):
            try:
                subprocess.check_call(['docker', 'stop', CONTAINER_NAME])
            except subprocess.CalledProcessError:
                # Maybe the container wasn't running, and that is fine.
                pass

    @classmethod
    def setUpClass(cls) -> None:
        subprocess.check_call(
            ['docker', 'build', '-t', IMAGE_NAME, DOCKER_PATH])

    def assert_betty_html(self, response: Response) -> None:
        self.assertEquals('text/html', response.headers['Content-Type'])
        parser = html5lib.HTMLParser()
        parser.parse(response.text)
        self.assertIn('Betty', response.text)

    def assert_betty_json(self, response: Response) -> None:
        self.assertEquals('application/json', response.headers['Content-Type'])
        data = response.json()
        with open(path.join(path.dirname(path.dirname(path.dirname(path.dirname(__file__)))), 'resources', 'public',
                            'static', 'schema.json')) as f:
            jsonschema.validate(data, json.load(f))

    def test_front_page(self):
        with self.Container('betty-monolingual.json') as c:
            response = requests.get(c.address)
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    def test_default_html_404(self):
        with self.Container('betty-monolingual.json') as c:
            response = requests.get('%s/non-existent' % c.address)
            self.assertEquals(404, response.status_code)
            self.assert_betty_html(response)

    def test_negotiated_json_404(self):
        with self.Container('betty-monolingual-content-negotiation.json') as c:
            response = requests.get('%s/non-existent' % c.address, headers={
                'Accept': 'application/json',
            })
            self.assertEquals(404, response.status_code)
            self.assert_betty_json(response)

    def test_default_localized_front_page(self):
        with self.Container('betty-multilingual.json') as c:
            response = requests.get(c.address)
            self.assertEquals(200, response.status_code)
            self.assertEquals('en', response.headers['Content-Language'])
            self.assertEquals('%s/en/' % c.address, response.url)
            self.assert_betty_html(response)

    def test_explicitly_localized_404(self):
        with self.Container('betty-multilingual.json') as c:
            response = requests.get('%s/nl/non-existent' % c.address)
            self.assertEquals(404, response.status_code)
            self.assertEquals('nl', response.headers['Content-Language'])
            self.assert_betty_html(response)

    def test_negotiated_localized_front_page(self):
        with self.Container('betty-multilingual-content-negotiation.json') as c:
            response = requests.get(c.address, headers={
                'Accept-Language': 'nl-NL',
            })
            self.assertEquals(200, response.status_code)
            self.assertEquals('nl', response.headers['Content-Language'])
            self.assertEquals('%s/nl/' % c.address, response.url)
            self.assert_betty_html(response)

    def test_negotiated_localized_default_html_404(self):
        with self.Container('betty-multilingual-content-negotiation.json') as c:
            response = requests.get('%s/non-existent' % c.address, headers={
                'Accept-Language': 'nl-NL',
            })
            self.assertEquals(404, response.status_code)
            self.assertEquals('nl', response.headers['Content-Language'])
            self.assert_betty_html(response)

    def test_negotiated_localized_negotiated_json_404(self):
        with self.Container('betty-multilingual-content-negotiation.json') as c:
            response = requests.get('%s/non-existent' % c.address, headers={
                'Accept': 'application/json',
                'Accept-Language': 'nl-NL',
            })
            self.assertEquals(404, response.status_code)
            self.assert_betty_json(response)

    def test_default_html_resource(self):
        with self.Container('betty-monolingual-content-negotiation.json') as c:
            response = requests.get('%s/place/' % c.address)
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    def test_negotiated_html_resource(self):
        with self.Container('betty-monolingual-content-negotiation.json') as c:
            response = requests.get('%s/place/' % c.address, headers={
                'Accept': 'text/html',
            })
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    def test_negotiated_json_resource(self):
        with self.Container('betty-monolingual-content-negotiation.json') as c:
            response = requests.get('%s/place/' % c.address, headers={
                'Accept': 'application/json',
            })
            self.assertEquals(200, response.status_code)
            self.assert_betty_json(response)

    def test_default_html_static_resource(self):
        with self.Container('betty-multilingual-content-negotiation.json') as c:
            response = requests.get('%s/api/' % c.address)
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    def test_negotiated_html_static_resource(self):
        with self.Container('betty-multilingual-content-negotiation.json') as c:
            response = requests.get('%s/api/' % c.address, headers={
                'Accept': 'text/html',
            })
            self.assertEquals(200, response.status_code)
            self.assert_betty_html(response)

    def test_negotiated_json_static_resource(self):
        with self.Container('betty-multilingual-content-negotiation.json') as c:
            response = requests.get('%s/api/' % c.address, headers={
                'Accept': 'application/json',
            })
            self.assertEquals(200, response.status_code)
            self.assert_betty_json(response)
            # Assert this is the exact JSON resource we are looking for.
            with open(path.join(path.dirname(path.dirname(path.dirname(__file__))), 'resources', 'openapi',
                                'schema.json')) as f:
                schema = json.load(f)
            jsonschema.validate(response.json(), schema)
