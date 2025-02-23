"""
Provide demonstration site functionality.
"""

from __future__ import annotations

from asyncio import to_thread
from contextlib import suppress
from shutil import rmtree
from typing import TYPE_CHECKING, final, Sequence

from typing_extensions import override

from betty.html import NavigationLinkProvider, NavigationLink
from betty.locale.localizable import static, _
from betty.plugin import ShorthandPluginBase
from betty.project import generate
from betty.project.extension import Extension
from betty.project.extension.demo.project import load_ancestry
from betty.project.extension.deriver import Deriver
from betty.project.extension.http_api_doc import HttpApiDoc
from betty.project.extension.maps import Maps
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.trees import Trees
from betty.project.extension.wikipedia import Wikipedia
from betty.project.load import LoadAncestryEvent
from betty.typing import internal

if TYPE_CHECKING:
    from betty.project import Project
    from betty.plugin import PluginIdentifier
    from betty.event_dispatcher import EventHandlerRegistry


@internal
async def generate_with_cleanup(project: Project) -> None:
    """
    Generate a demonstration site, and clean up the project directory on any errors.
    """
    with suppress(FileNotFoundError):
        await to_thread(rmtree, project.configuration.project_directory_path)
    try:
        await generate.generate(project)
    except BaseException:
        with suppress(FileNotFoundError):
            await to_thread(rmtree, project.configuration.project_directory_path)
        raise


@final
class Demo(ShorthandPluginBase, NavigationLinkProvider, Extension):
    """
    Provide demonstration site functionality.
    """

    _plugin_id = "demo"
    _plugin_label = static("Demo")

    @override
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {
            Deriver,
            HttpApiDoc,
            Maps,
            RaspberryMint,
            Trees,
            Wikipedia,
        }

    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(
            LoadAncestryEvent, lambda event: load_ancestry(event.project)
        )

    @override
    def secondary_navigation_links(self) -> Sequence[NavigationLink]:
        return [
            NavigationLink(
                "https://github.com/bartfeenstra/betty", _("Find Betty on GitHub")
            ),
            NavigationLink(
                "https://betty.readthedocs.io/", _("Read the Betty documentation")
            ),
        ]
