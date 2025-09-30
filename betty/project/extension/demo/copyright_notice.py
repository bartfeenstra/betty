"""
Copyright notices for the Betty demonstration site.
"""

from typing_extensions import override

from betty.copyright_notice import CopyrightNotice
from betty.locale.localizable import Localizable, StaticTranslations
from betty.plugin import ShorthandPluginBase


class Streetmix(ShorthandPluginBase, CopyrightNotice):
    """
    The copyright for Streetmix resources.
    """

    _plugin_id = "streetmix"
    _plugin_label = StaticTranslations("Streetmix LLC")

    @override
    @property
    def summary(self) -> Localizable:
        return self.plugin_label()

    @override
    @property
    def text(self) -> Localizable:
        return self.plugin_label()

    @override
    @property
    def url(self) -> Localizable:
        return StaticTranslations("https://github.com/streetmix/streetmix")
