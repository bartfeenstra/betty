from typing import Optional, List, Dict

import pytest

from betty.media_type import MediaType, InvalidMediaType


class TestMediaType:
    @pytest.mark.parametrize('expected_type, expected_subtype, expected_subtypes, expected_suffix, expected_parameters, media_type', [
        # The simplest possible media type.
        ('text', 'plain', ['plain'], None, {}, 'text/plain'),
        # A media type with a hyphenated subtype.
        ('multipart', 'form-data', ['form-data'], None, {}, 'multipart/form-data'),
        # A media type with a tree subtype.
        ('application', 'vnd.oasis.opendocument.text', ['vnd', 'oasis', 'opendocument', 'text'], None, {}, 'application/vnd.oasis.opendocument.text'),
        # A media type with a subtype suffix.
        ('application', 'ld+json', ['ld'], 'json', {}, 'application/ld+json'),
        # A media type with a parameter.
        ('text', 'html', ['html'], None, {'charset': 'UTF-8'}, 'text/html; charset=UTF-8'),
    ])
    def test(self, expected_type: str, expected_subtype: str, expected_subtypes: List[str], expected_suffix: Optional[str], expected_parameters: Dict[str, str], media_type: str):
        sut = MediaType(media_type)
        assert expected_type == sut.type
        assert expected_subtype == sut.subtype
        assert expected_subtypes == sut.subtypes
        assert expected_suffix == sut.suffix
        assert expected_parameters == sut.parameters
        assert media_type == str(sut)

    @pytest.mark.parametrize('media_type', [
        '',
        '/',
        'text',
        'text/',
        'foo',
        'bar',
    ])
    def test_invalid_type_should_raise_error(self, media_type: str):
        with pytest.raises(InvalidMediaType):
            MediaType(media_type)
