import json

import pytest


@pytest.fixture
def minimal_configuration_file_path(tmpdir) -> str:
    configuration_file_path = tmpdir.join('betty.json')
    output_directory_path = str(tmpdir.join('output'))
    base_url = 'https://example.com'
    with open(configuration_file_path, 'w') as f:
        json.dump({
            'output': output_directory_path,
            'base_url': base_url,
        }, f)
    return configuration_file_path
