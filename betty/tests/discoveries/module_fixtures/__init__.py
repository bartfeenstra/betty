from typing import final

from betty.definition.cls import ClsDefinition
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.test_utils.locale.localizable import dummy_countable_localizable


@final
@PluginTypeDefinition(
    "plugin-definition",
    label="-",
    label_plural="-",
    label_countable=dummy_countable_localizable,
)
class PluginDefinitionDefinition(PluginDefinition):
    pass


@final
@PluginTypeDefinition(
    "plugin-cls",
    label="-",
    label_plural="-",
    label_countable=dummy_countable_localizable,
)
class PluginClsDefinition(PluginDefinition, ClsDefinition):
    pass
