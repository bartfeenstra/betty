"""
Dynamic content.
"""

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Self

from typing_extensions import override

from betty.assertion import (
    OptionalField,
    RequiredField,
    assert_bool,
    assert_record,
    assert_setattr,
)
from betty.config import Configuration, DefaultConfigurable
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.content_provider.content_providers import Jinja2TemplateContentProvider
from betty.locale.localizable import ShorthandStaticTranslations, _
from betty.locale.localizable.assertion import assert_static_translations
from betty.locale.localizable.config import RequiredStaticTranslationsConfigurationAttr
from betty.machine_name import MachineName, assert_machine_name
from betty.model.config import EntityReferenceSequence
from betty.plugin.config import (
    PluginInstanceConfiguration,
    PluginInstanceConfigurationSequence,
)
from betty.project import Project
from betty.resource import Context
from betty.serde.dump import Dump

if TYPE_CHECKING:
    from collections.abc import MutableSequence

    from betty.model import Entity


class SectionConfiguration(Configuration):
    """
    Configuration for :py:class:`betty.project.extension.raspberry_mint.content_provider.Section`.
    """

    heading = RequiredStaticTranslationsConfigurationAttr("heading")
    """
    The human-readable heading text.
    """

    def __init__(
        self,
        *,
        heading: ShorthandStaticTranslations,
        content: Sequence[
            PluginInstanceConfiguration[ContentProviderDefinition, ContentProvider]
        ]
        | None = None,
        name: MachineName | None = None,
        visually_hide_heading: bool = False,
    ):
        super().__init__()
        self.heading = heading
        self._content = PluginInstanceConfigurationSequence[
            ContentProviderDefinition, ContentProvider
        ]()
        if content:
            self._content.append(*content)
        self.name = name
        self.visually_hide_heading = visually_hide_heading

    @property
    def content(
        self,
    ) -> PluginInstanceConfigurationSequence[
        ContentProviderDefinition, ContentProvider
    ]:
        """
        The content within this section.
        """
        return self._content

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            OptionalField("name", assert_machine_name() | assert_setattr(self, "name")),
            RequiredField(
                "heading",
                assert_static_translations() | assert_setattr(self, "heading"),
            ),
            RequiredField("content", self.content.load),
            OptionalField(
                "visually_hide_heading",
                assert_bool() | assert_setattr(self, "visually_hide_heading"),
            ),
        )(dump)

    @override
    def dump(self) -> Dump:
        dump = {
            "heading": self.heading.dump(),
            "content": self.content.dump(),
        }
        if self.name:
            dump["name"] = self.name
        if self.visually_hide_heading:
            dump["visually_hide_heading"] = True
        return dump


@ContentProviderDefinition(
    id="raspberry-mint-section",
    label=_("Section"),
)
class Section(Jinja2TemplateContentProvider, DefaultConfigurable[SectionConfiguration]):
    """
    A section on the page with a heading and a permanent link.
    """

    _template = "component/content-section.html.j2"

    def __init__(self, project: Project, configuration: SectionConfiguration):
        super().__init__(project, configuration=configuration)

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project, configuration=cls.new_default_configuration())

    @override
    @classmethod
    def new_default_configuration(cls) -> SectionConfiguration:
        return SectionConfiguration(name="", heading="")

    @override
    async def _provide_data(self, resource: Context) -> Mapping[str, Any]:
        return {
            "section_name": self.configuration.name,
            "section_heading": self.configuration.heading,
            "section_visually_hide_heading": self.configuration.visually_hide_heading,
            "section_content_configurations": self.configuration.content,
        }


@ContentProviderDefinition(
    id="raspberry-mint-featured-entities",
    label=_("Featured entities"),
)
class FeaturedEntities(
    Jinja2TemplateContentProvider, DefaultConfigurable[EntityReferenceSequence]
):
    """
    Featured entities.
    """

    _template = "component/featured-entities.html.j2"

    def __init__(self, project: Project, configuration: EntityReferenceSequence):
        super().__init__(project, configuration=configuration)

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project, configuration=cls.new_default_configuration())

    @override
    @classmethod
    def new_default_configuration(cls) -> EntityReferenceSequence:
        return EntityReferenceSequence()

    @override
    async def _provide_data(self, resource: Context) -> Mapping[str, Any]:
        entities: MutableSequence[Entity] = []
        for entity in self.configuration:
            assert entity.entity_type is not None
            assert entity.entity_id is not None
            entities.append(
                self._project.ancestry[
                    self._project.app.entity_type_repository.get(entity.entity_type)
                ][entity.entity_id]
            )
        return {
            "entities": entities,
        }
