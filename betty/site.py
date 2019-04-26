from betty.ancestry import Ancestry
from betty.config import Configuration
from betty.event import EventDispatcher


class Site:
    def __init__(self, ancestry: Ancestry, configuration: Configuration):
        self._ancestry = ancestry
        self._configuration = configuration
        self._plugins = list([plugin_class.from_configuration_dict(plugin_configuration) for plugin_class, plugin_configuration in
                              configuration.plugins.items()])
        self._event_dispatcher = EventDispatcher()
        for plugin in self._plugins:
            for event_name, listener in plugin.subscribes_to():
                self._event_dispatcher.add_listener(event_name, listener)

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry

    @property
    def configuration(self):
        return self._configuration

    @property
    def event_dispatcher(self) -> EventDispatcher:
        return self._event_dispatcher
