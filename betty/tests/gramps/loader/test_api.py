from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry import Ancestry
from betty.gramps.loader import (
    GrampsLoader,
)
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer
from betty.plugin.static import StaticPluginRepository
from betty.tests.gramps.test_loader import GrampsLoaderFactoryBase, GrampsLoaderTestBase

if TYPE_CHECKING:
    from betty.ancestry.event_type import EventType
    from betty.ancestry.gender import Gender
    from betty.ancestry.place_type import PlaceType
    from betty.ancestry.presence_role import PresenceRole
    from betty.copyright_notice import CopyrightNotice
    from betty.gramps.loader import (
        PluginMapping,
    )
    from betty.license import License
    from betty.plugin import PluginRepository


class _GrampsLoaderFactory(GrampsLoaderFactoryBase):
    @override
    async def __call__(
        self,
        *,
        ancestry: Ancestry | None = None,
        attribute_prefix_key: str | None = None,
        copyright_notices: PluginRepository[CopyrightNotice] | None = None,
        event_type_mapping: PluginMapping[EventType] | None = None,
        genders: PluginRepository[Gender] | None = None,
        licenses: PluginRepository[License] | None = None,
        localizer: Localizer = DEFAULT_LOCALIZER,
        place_type_mapping: PluginMapping[PlaceType] | None = None,
        presence_role_mapping: PluginMapping[PresenceRole] | None = None,
    ) -> GrampsLoader:
        return GrampsLoader(
            ancestry or await Ancestry.new(),
            attribute_prefix_key=attribute_prefix_key,
            copyright_notices=copyright_notices or StaticPluginRepository(),
            event_type_mapping=event_type_mapping,
            genders=genders or StaticPluginRepository(),
            licenses=licenses or StaticPluginRepository(),
            localizer=localizer,
            place_type_mapping=place_type_mapping,
            presence_role_mapping=presence_role_mapping,
        )


class TestGrampsLoader(GrampsLoaderTestBase):
    @pytest.fixture
    async def gramps_loader_factory(self) -> _GrampsLoaderFactory:
        return _GrampsLoaderFactory()
