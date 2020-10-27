import cgi
from typing import Dict, Optional, List

EXTENSIONS = {
    'text/html': 'html',
    'application/json': 'json',
}


class InvalidMediaType(ValueError):
    pass


class MediaType:
    def __init__(self, type: str, subtype: str, parameters: Dict[str, str]):
        self._type = type
        self._subtype = subtype
        self._parameters = parameters

    @classmethod
    def from_string(cls, media_type: str) -> 'MediaType':
        type_part, parameters = cgi.parse_header(media_type)
        try:
            type, subtype = type_part.split('/')
        except ValueError:
            raise InvalidMediaType('"%s" is not a valid media type.', media_type)

        return cls(type, subtype, parameters)

    @property
    def type(self) -> str:
        return self._type

    @property
    def subtype(self) -> Optional[str]:
        return self._subtype

    @property
    def subtypes(self) -> List[str]:
        if self._subtype is None:
            return []

        return self._subtype.split('+')[0].split('.')

    @property
    def suffix(self) -> Optional[str]:
        if self._subtype is None:
            return None

        if '+' not in self._subtype:
            return None

        return self._subtype.split('+')[-1]

    @property
    def parameters(self) -> Dict[str, str]:
        return self._parameters
