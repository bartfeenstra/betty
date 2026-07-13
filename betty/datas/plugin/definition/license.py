"""
License definition data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.attrs.localizable import new_localizable_attr
from betty.datas.plugin.definition import PluginDefinitionDefinition
from betty.datas.plugin.definition.human_facing import HumanFacingPluginDefinitionData
from betty.license import License, LicenseDefinition
from betty.localizables.gettext import _
from betty.sample import Sample

if TYPE_CHECKING:
    from betty.localizable import Localizable, ResolvableLocalizable


@final
@PluginDefinitionDefinition(
    LicenseDefinition,
    samples=[
        lambda: Sample(
            LicenseDefinitionData(
                id="my-first-license",
                label="My First License",
                summary="My First License is my first license",
                text="My First License is my first license, and allows you o…",
            ),
            label="Default",
        )
    ],
)
class LicenseDefinitionData(HumanFacingPluginDefinitionData[LicenseDefinition]):
    """
    Configure a :py:class:`betty.license.LicenseDefinition`.

    .. data:: betty.datas.license_definition:LicenseDefinitionData
    """

    summary = new_localizable_attr(label=_("Summary"))
    text = new_localizable_attr(label=_("Text"))

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
        class _LicenseDefinitionDataLicense(License):
            @override
            @property
            def summary(self) -> Localizable:
                return configuration.summary

            @override
            @property
            def text(self) -> Localizable:
                return configuration.text

        return _LicenseDefinitionDataLicense.plugin()
