"""
License configuration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.data.aggregate.record.object import ObjectDefinition
from betty.license import License, LicenseDefinition
from betty.locale.localizable.gettext import _
from betty.locale.localizable.property import LocalizableProperty
from betty.plugin.config import HumanFacingPluginDefinitionConfiguration
from betty.sample import Sample

if TYPE_CHECKING:
    from betty.locale.localizable import Localizable, ResolvableLocalizable


@final
@ObjectDefinition(
    label=_("License configuration"),
    samples=[
        lambda: Sample(
            LicenseDefinitionConfiguration(
                id="my-first-license",
                label="My First License",
                summary="My First License is my first license",
                text="My First License is my first license, and allows you o...",
            ),
            label="Default",
        )
    ],
)
class LicenseDefinitionConfiguration(
    HumanFacingPluginDefinitionConfiguration[LicenseDefinition]
):
    """
    Configure a :py:class:`betty.license.LicenseDefinition`.

    .. data:: betty.project.data:LicenseDefinitionConfiguration
    """

    summary = LocalizableProperty(label=_("Summary"))
    text = LocalizableProperty(label=_("Text"))

    def __init__(
        self,
        *,
        summary: ResolvableLocalizable,
        text: ResolvableLocalizable,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.summary = summary
        self.text = text

    @override
    def new_plugin(self) -> LicenseDefinition:
        configuration = self

        @LicenseDefinition(
            self.id,
            label=self.label,
            description=self.description,
        )
        class _ProjectConfigurationLicense(License):
            @override
            @property
            def summary(self) -> Localizable:
                return configuration.summary

            @override
            @property
            def text(self) -> Localizable:
                return configuration.text

        return _ProjectConfigurationLicense.plugin()
