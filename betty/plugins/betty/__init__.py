from os import path
from typing import List, Callable, Dict, Optional

from betty import parse, render
from betty.cli.command import Command, CommandProvider
from betty.plugin import Plugin
from betty.site import Site


class GenerateCommand(Command):
    def __init__(self, site: Site):
        self._site = site

    def build_parser(self, add_parser: Callable):
        return add_parser('generate', description='Generate a static site.')

    def run(self):
        parse.parse(self._site)
        render.render(self._site)


class Betty(Plugin, CommandProvider):
    def __init__(self, site: Site):
        self._site = site

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(site)

    @property
    def resource_directory_path(self) -> Optional[str]:
        return path.join(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))), 'resources')

    @property
    def commands(self) -> List[Command]:
        return [
            GenerateCommand(self._site)
        ]
