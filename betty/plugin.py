from typing import Callable, Tuple, Dict, Type, Set, List

from betty.site import Site


class Plugin:
    @classmethod
    def name(cls) -> str:
        return '%s.%s' % (cls.__module__, cls.__name__)

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls()

    @classmethod
    def depends_on(cls) -> Set[Type]:
        return set()

    def subscribes_to(self) -> List[Tuple[str, Callable]]:
        return set()
