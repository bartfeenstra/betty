import cgi
from typing import Dict, Optional, List

EXTENSIONS = {
    'text/html': 'html',
    'application/json': 'json',
}


class InvalidMediaType(ValueError):
    pass


class MediaType:
    def __init__(self, media_type: str):
        self._str = media_type
        type_part, self._parameters = cgi.parse_header(media_type)
        try:
            self._type, self._subtype = type_part.split('/')
            if not self._subtype:
                raise ValueError('The subtype must not be empty.')
        except ValueError:
            raise InvalidMediaType('"%s" is not a valid media type.', media_type)

    @property
    def type(self) -> str:
        return self._type

    @property
    def subtype(self) -> str:
        return self._subtype

    @property
    def subtypes(self) -> List[str]:
        return self._subtype.split('+')[0].split('.')

    @property
    def suffix(self) -> Optional[str]:
        if '+' not in self._subtype:
            return None

        return self._subtype.split('+')[-1]

    @property
    def parameters(self) -> Dict[str, str]:
        return self._parameters

    def __str__(self):
        return self._str

    def __eq__(self, other):
        if not isinstance(other, MediaType):
            return NotImplemented
        return (self.type, self.subtype, self.parameters) == (other.type, other.subtype, other.parameters)
