from typing import Callable, Tuple, Dict, Type, Set, List, Optional

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

    @classmethod
    def comes_after(cls) -> Set[Type]:
        return set()

    @classmethod
    def comes_before(cls) -> Set[Type]:
        return set()

    def subscribes_to(self) -> List[Tuple[Type, Callable]]:
        return []

    @property
    def resource_directory_path(self) -> Optional[str]:
        return None
