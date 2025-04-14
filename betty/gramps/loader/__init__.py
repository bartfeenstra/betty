"""
An API to load `Gramps <https://gramps-project.org>`_ family trees into Betty ancestries.
"""

from __future__ import annotations

import gzip
import os
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Generic,
    Iterable,
    TypeAlias,
    TypeVar,
    cast,
    final,
)

from aiofiles.tempfile import TemporaryDirectory
from typing_extensions import override

from betty.ancestry.event_type.event_types import (
    Adoption,
    Baptism,
    BarMitzvah,
    BatMitzvah,
    Birth,
    Burial,
    Confirmation,
    Cremation,
    Death,
    Divorce,
    DivorceAnnouncement,
    Emigration,
    Engagement,
    Immigration,
    Marriage,
    MarriageAnnouncement,
    Occupation,
    Residence,
    Retirement,
    Will,
)
from betty.ancestry.place_type.place_types import (
    Borough,
    Building,
    City,
    Country,
    County,
    Department,
    District,
    Farm,
    Hamlet,
    Locality,
    Municipality,
    Neighborhood,
    Number,
    Parish,
    Province,
    Region,
    State,
    Street,
    Town,
    Village,
)
from betty.ancestry.place_type.place_types import Unknown as UnknownPlaceType
from betty.ancestry.presence_role.presence_roles import (
    Attendee,
    Celebrant,
    Informant,
    Subject,
    Witness,
)
from betty.ancestry.presence_role.presence_roles import Unknown as UnknownPresenceRole
from betty.error import FileNotFound
from betty.gramps.error import GrampsError, UserFacingGrampsError
from betty.model import Entity
from betty.model.association import ToManyResolver, ToOneResolver
from betty.plugin import Plugin

if TYPE_CHECKING:
    from betty.ancestry import Ancestry
    from betty.ancestry.event_type import EventType
    from betty.ancestry.gender import Gender
    from betty.ancestry.place_type import PlaceType
    from betty.ancestry.presence_role import PresenceRole
    from betty.copyright_notice import CopyrightNotice
    from betty.license import License
    from betty.locale.localizer import Localizer
    from betty.plugin import PluginRepository

_PLuginT = TypeVar("_PLuginT", bound=Plugin)
_EntityT = TypeVar("_EntityT", bound=Entity)


class LoaderUsedAlready(GrampsError):
    """
    Raised when a :py:class:`betty.gramps.loader.GrampsLoader` is used more than once.
    """

    pass  # pragma: no cover


class GrampsFileNotFound(UserFacingGrampsError, FileNotFound):
    """
    Raised when a Gramps family tree file cannot be found.
    """

    pass  # pragma: no cover


class _ToOneResolver(Generic[_EntityT], ToOneResolver[_EntityT]):
    def __init__(self, handles_to_entities: Mapping[str, Entity], handle: str):
        self._handles_to_entities = handles_to_entities
        self._handle = handle

    @override
    def resolve(self) -> _EntityT:
        return cast("_EntityT", self._handles_to_entities[self._handle])


class _ToManyResolver(Generic[_EntityT], ToManyResolver[_EntityT]):
    def __init__(self, handles_to_entities: Mapping[str, Entity], *handles: str):
        self._handles_to_entities = handles_to_entities
        self._handles = handles

    @override
    def resolve(self) -> Iterable[_EntityT]:
        for handle in self._handles:
            yield cast("_EntityT", self._handles_to_entities[handle])


DEFAULT_EVENT_TYPES_MAPPING = {
    "Adopted": Adoption,
    "Adult Christening": Baptism,
    "Baptism": Baptism,
    "Bar Mitzvah": BarMitzvah,
    "Bat Mitzvah": BatMitzvah,
    "Birth": Birth,
    "Burial": Burial,
    "Christening": Baptism,
    "Confirmation": Confirmation,
    "Cremation": Cremation,
    "Death": Death,
    "Divorce": Divorce,
    "Divorce Filing": DivorceAnnouncement,
    "Emigration": Emigration,
    "Engagement": Engagement,
    "Immigration": Immigration,
    "Marriage": Marriage,
    "Marriage Banns": MarriageAnnouncement,
    "Occupation": Occupation,
    "Residence": Residence,
    "Retirement": Retirement,
    "Will": Will,
}

DEFAULT_PLACE_TYPES_MAPPING = {
    "Borough": Borough,
    "Building": Building,
    "City": City,
    "Country": Country,
    "County": County,
    "Department": Department,
    "District": District,
    "Farm": Farm,
    "Hamlet": Hamlet,
    "Locality": Locality,
    "Municipality": Municipality,
    "Neighborhood": Neighborhood,
    "Number": Number,
    "Parish": Parish,
    "Province": Province,
    "Region": Region,
    "State": State,
    "Street": Street,
    "Town": Town,
    "Unknown": UnknownPlaceType,
    "Village": Village,
}

DEFAULT_PRESENCE_ROLES_MAPPING = {
    "Aide": Attendee,
    "Bride": Subject,
    "Celebrant": Celebrant,
    "Clergy": Celebrant,
    "Family": Subject,
    "Groom": Subject,
    "Informant": Informant,
    "Primary": Subject,
    "Unknown": UnknownPresenceRole,
    "Witness": Witness,
}

PluginMapping: TypeAlias = Mapping[
    str, Callable[[], Awaitable[_PLuginT]] | type[_PLuginT]
]


@final
class GrampsLoader:
    """
    Load Gramps family history data into a project.
    """

    def __init__(
        self,
        ancestry: Ancestry,
        *,
        copyright_notices: PluginRepository[CopyrightNotice],
        genders: PluginRepository[Gender],
        licenses: PluginRepository[License],
        localizer: Localizer,
        attribute_prefix_key: str | None = None,
        event_type_mapping: PluginMapping[EventType] | None = None,
        place_type_mapping: PluginMapping[PlaceType] | None = None,
        presence_role_mapping: PluginMapping[PresenceRole] | None = None,
    ):
        self._loaded = False
        self._ancestry = ancestry
        self._localizer = localizer
        self._attribute_prefix_key = attribute_prefix_key
        self._copyright_notices = copyright_notices
        self._genders = genders
        self._licenses = licenses
        self._event_type_mapping = event_type_mapping or {}
        self._place_type_mapping = place_type_mapping or {}
        self._presence_role_mapping = presence_role_mapping or {}

    @property
    def ancestry(self) -> Ancestry:
        """
        The ancestry data was loaded into.
        """
        return self._ancestry

    async def load_file(self, file_path: Path) -> None:
        """
        Load family history data from any of the supported Gramps file types.

        :raises betty.gramps.error.GrampsError:
        """
        if self._loaded:
            raise LoaderUsedAlready("This loader has been used up.")

        self._loaded = True

        async with TemporaryDirectory() as directory_path_str:
            directory_path = Path(directory_path_str)
            try:
                original_gramps_home_override_directory_path_str = os.environ.get(
                    "GRAMPSHOME_ISOLATED", None
                )
                os.environ["GRAMPSHOME_ISOLATED"] = str(directory_path / "home")
                original_gramps_resources_override_directory_path_str = os.environ.get(
                    "GRAMPS_RESOURCES", None
                )
                os.environ["GRAMPS_RESOURCES"] = str(directory_path / "resources")

                from betty.gramps.loader._loader import _ImportUnsafeGrampsLoader

                loader = _ImportUnsafeGrampsLoader(
                    ancestry=self._ancestry,
                    copyright_notices=self._copyright_notices,
                    genders=self._genders,
                    licenses=self._licenses,
                    localizer=self._localizer,
                    attribute_prefix_key=self._attribute_prefix_key,
                    event_type_mapping=self._event_type_mapping,
                    place_type_mapping=self._place_type_mapping,
                    presence_role_mapping=self._presence_role_mapping,
                )
                await loader.load_file(file_path)
            finally:
                if original_gramps_home_override_directory_path_str is not None:
                    os.environ["GRAMPSHOME_ISOLATED"] = (
                        original_gramps_home_override_directory_path_str
                    )
                if original_gramps_resources_override_directory_path_str is not None:
                    os.environ["GRAMPS_RESOURCES"] = (
                        original_gramps_resources_override_directory_path_str
                    )

    async def load_xml(self, xml: str) -> None:
        """
        Load family history data from XML.

        :raises betty.gramps.error.GrampsError:
        """
        # Use a temporary directory instead of a file, because on Windows temporary files cannot
        # subsequently be opened by their names.
        async with TemporaryDirectory() as temporary_directory_path_str:
            gramps_path = Path(temporary_directory_path_str) / "tmp.gramps"
            with gzip.open(gramps_path, "w") as gzip_f:
                gzip_f.write(xml.encode("utf-8"))
            return await self.load_file(Path(gramps_path))
