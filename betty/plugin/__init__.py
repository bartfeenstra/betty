from typing import Type, Set, Optional, Any

from voluptuous import Schema

from betty.site import Site


NO_CONFIGURATION = None


class Plugin:
    configuration_schema: Schema = Schema(None)

    async def __aenter__(self):
        pass  # pragma: no cover

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass  # pragma: no cover

    @classmethod
    def name(cls) -> str:
        return '%s.%s' % (cls.__module__, cls.__name__)

    @classmethod
    def for_site(cls, site: Site, configuration: Any = NO_CONFIGURATION):
        """
        Creates a new instance for a specific site.
        :param site: betty.site.Site
        :param configuration: The configuration must be of the same type as returned by cls.configuration_schema.
        :return: Self
        """
        return cls()

    @classmethod
    def depends_on(cls) -> Set[Type['Plugin']]:
        return set()

    @classmethod
    def comes_after(cls) -> Set[Type['Plugin']]:
        return set()

    @classmethod
    def comes_before(cls) -> Set[Type['Plugin']]:
        return set()

    @property
    def assets_directory_path(self) -> Optional[str]:
        return None
