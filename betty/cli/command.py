from typing import Callable, List


class Command:
    def build_parser(self, add_parser: Callable):
        raise NotImplementedError

    def run(self, **kwargs):
        raise NotImplementedError


class CommandProvider:
    @property
    def commands(self) -> List[Command]:
        raise NotImplementedError
