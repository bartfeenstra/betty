from betty.ancestry import Ancestry
from betty.config import Configuration


class Site:
    def __init__(self, ancestry: Ancestry, configuration: Configuration):
        self._ancestry = ancestry
        self._configuration = configuration

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry

    @propertyw
    def configuration(self):
        return self._configuration

    def dispatch(self, event_name, *args, **kwargs):
        if event_name not in self._listeners:
            return
        for listener in self._listeners[event_name]:
            listener(*args, **kwargs)
