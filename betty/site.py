from betty.ancestry import Ancestry
from betty.config import Configuration


class Site:
    def __init__(self, ancestry: Ancestry, configuration: Configuration):
        self._ancestry = ancestry
        self._configuration = configuration

    @property
    def ancestry(self) -> Ancestry:
        return self._ancestry

    @property
    def configuration(self):
        return self._configuration
