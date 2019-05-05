import hashlib
import json
from collections import OrderedDict
from os import makedirs
from os.path import join, expanduser, dirname
from shutil import copy2, copytree
from subprocess import check_call
from typing import Tuple, List, Dict

from jinja2 import Environment

import betty
from betty import RESOURCE_PATH
from betty.event import POST_RENDER_EVENT
from betty.plugin import Plugin
from betty.render import _copytree
from betty.site import Site


class JsPackageProvider:
    @property
    def package_directory_path(self) -> str:
        raise NotImplementedError


class JsEntryPointProvider:
    @property
    def entry_point(self) -> Tuple[str, str]:
        raise NotImplementedError


class Js(Plugin, JsPackageProvider):
    def __init__(self, plugins: OrderedDict, output_directory_path: str):
        betty_instance_id = hashlib.sha1(
            betty.__path__[0].encode()).hexdigest()
        self._directory_path = join(
            expanduser('~'), '.betty', betty_instance_id)
        self._plugins = plugins
        self._output_directory_path = output_directory_path

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(site.plugins, site.configuration.output_directory_path)

    def subscribes_to(self):
        return [
            (POST_RENDER_EVENT, self._build_instance_directory),
            (POST_RENDER_EVENT, lambda *_: self._install()),
            (POST_RENDER_EVENT, lambda *_: self._webpack()),
        ]

    def _build_instance_directory(self, environment: Environment) -> None:
        dependencies = {}
        for plugin in self._plugins.values():
            if isinstance(plugin, JsPackageProvider):
                _copytree(environment, plugin.package_directory_path,
                          join(self.directory_path, plugin.name()))
                dependencies[plugin.name()] = 'file:%s' % join(
                    self.directory_path, plugin.name())
        with open(join(self.directory_path, self.name(), 'package.json'), 'r+') as package_json_f:
            package_json = json.load(package_json_f)
            package_json['dependencies'].update(dependencies)
            package_json['scripts'] = {
                'webpack': 'webpack --config ./webpack.config.js',
            }
            package_json_f.seek(0)
            json.dump(package_json, package_json_f)

    def _install(self) -> None:
        makedirs(self.directory_path, 0o700, True)
        check_call(['npm', 'install', '--production'],
                   cwd=join(self.directory_path, self.name()))

    def _webpack(self) -> None:
        copy2(join(RESOURCE_PATH, 'public/betty.css'),
              join(self.directory_path, self.name(), 'betty.css'))

        # Build the assets.
        check_call(['npm', 'run', 'webpack'], cwd=join(self.directory_path, self.name()))

        # Move the Webpack output to the Betty output.
        try:
            copytree(join(self.directory_path, 'output', 'images'),
                     join(self._output_directory_path, 'images'))
        except FileNotFoundError:
            # There may not be any images.
            pass
        copy2(join(self.directory_path, 'output', 'betty.css'),
              join(self._output_directory_path, 'betty.css'))
        copy2(join(self.directory_path, 'output', 'betty.js'),
              join(self._output_directory_path, 'betty.js'))

    @property
    def directory_path(self):
        return self._directory_path

    @property
    def entry_points(self) -> List[Tuple[str, str]]:
        entry_points = []
        for plugin in self._plugins.values():
            if isinstance(plugin, JsEntryPointProvider):
                entry_point, plugin_import_path = plugin.entry_point
                entry_points.append(
                    (entry_point, join(plugin.name(), plugin_import_path)))
        return entry_points

    @property
    def package_directory_path(self) -> str:
        return '%s/js' % dirname(__file__)
