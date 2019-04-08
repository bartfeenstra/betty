from typing import Iterable, Callable, Tuple, Dict

from betty.ancestry import Ancestry
from betty.event import POST_PARSE_EVENT


class Plugin:
    @classmethod
    def from_configuration_dict(cls, configuration: Dict):
        return cls()

    def subscribes_to(self) -> Iterable[Tuple[str, Callable]]:
        return []


class Anonimyzer(Plugin):
    @classmethod
    def from_configuration_dict(cls, configuration: Dict):
        return cls()

    def subscribes_to(self) -> Iterable[Tuple[str, Callable]]:
        return (
            (POST_PARSE_EVENT, self.anonymize),
        )

    def anonymize(self, ancestry: Ancestry):
        pass
