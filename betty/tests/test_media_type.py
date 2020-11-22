from typing import Optional, List, Dict

from parameterized import parameterized

from betty.media_type import MediaType, InvalidMediaType
from betty.tests import TestCase


class MediaTypeTest(TestCase):
    @parameterized.expand([
        # The simplest possible media type.
        ('text', 'plain', ['plain'], None, {}, 'text/plain'),
        # A media type with a hyphenated subtype.
        ('multipart', 'form-data', ['form-data'], None, {}, 'multipart/form-data'),
        # A media type with a tree subtype.
        ('application', 'vnd.oasis.opendocument.text', ['vnd', 'oasis', 'opendocument', 'text'], None, {},
         'application/vnd.oasis.opendocument.text'),
        # A media type with a subtype suffix.
        ('application', 'ld+json', ['ld'], 'json', {}, 'application/ld+json'),
        # A media type with a parameter.
        ('text', 'html', ['html'], None, {
            'charset': 'UTF-8',
        }, 'text/html; charset=UTF-8'),
    ])
    def test(self, expected_type: str, expected_subtype: str, expected_subtypes: List[str], expected_suffix: Optional[str], expected_parameters: Dict[str, str], media_type: str):
        sut = MediaType(media_type)
        self.assertEquals(expected_type, sut.type)
        self.assertEquals(expected_subtype, sut.subtype)
        self.assertEquals(expected_subtypes, sut.subtypes)
        self.assertEquals(expected_suffix, sut.suffix)
        self.assertEquals(expected_parameters, sut.parameters)
        self.assertEquals(media_type, str(sut))

    @parameterized.expand([
        ('',),
        ('/',),
        ('text',),
        ('text/',),
    ])
    def test_invalid_type_should_raise_value_error(self, media_type: str):
        with self.assertRaises(InvalidMediaType):
            MediaType(media_type)
