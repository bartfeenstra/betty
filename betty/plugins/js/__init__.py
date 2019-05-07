import hashlib
import json
from os import makedirs
from os.path import join, expanduser, dirname
from shutil import copy2, copytree, rmtree
from subprocess import check_call
from typing import Tuple, Dict, Iterable

from jinja2 import Environment

import betty
from betty.fs import FileSystem
from betty.plugin import Plugin
from betty.render import PostRenderEvent, render_tree
from betty.site import Site


class JsPackageProvider:
    @property
    def package_directory_path(self) -> str:
        raise NotImplementedError


class JsEntryPointProvider:
    pass


class Js(Plugin, JsPackageProvider):
    def __init__(self, file_system: FileSystem, plugins: Dict, output_directory_path: str):
        betty_instance_id = hashlib.sha1(
            betty.__path__[0].encode()).hexdigest()
        self._directory_path = join(
            expanduser('~'), '.betty', betty_instance_id)
        self._file_system = file_system
        self._plugins = plugins
        self._output_directory_path = output_directory_path

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(site.file_system, site.plugins, site.configuration.output_directory_path)

    def subscribes_to(self):
        return [
            (PostRenderEvent, lambda event: self._build_instance_directory(
                event.environment)),
            (PostRenderEvent, lambda event: self._install()),
            (PostRenderEvent, lambda event: self._webpack()),
        ]

    def _build_instance_directory(self, environment: Environment) -> None:
        # Remove an existing instance directory, if it exists.
        try:
            rmtree(self.directory_path)
        except FileNotFoundError:
            pass
        dependencies = {}
        for plugin in self._plugins.values():
            if isinstance(plugin, JsPackageProvider):
                copytree(plugin.package_directory_path,
                         join(self.directory_path, plugin.name()))
                render_tree(join(self.directory_path, plugin.name()), environment)
                if not isinstance(plugin, self.__class__):
                    dependencies[plugin.name()] = 'file:%s' % join(
                        self.directory_path, plugin.name())
                    with open(join(self.directory_path, plugin.name(), 'package.json'), 'r+') as package_json_f:
                        package_json = json.load(package_json_f)
                        package_json['name'] = plugin.name()
                        package_json_f.seek(0)
                        json.dump(package_json, package_json_f)
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
        self._file_system.copy2(join('resources', 'public/betty.css'),
                                join(self.directory_path, self.name(), 'betty.css'))

        # Build the assets.
        check_call(['npm', 'run', 'webpack'], cwd=join(
            self.directory_path, self.name()))

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
    def entry_points(self) -> Iterable[Tuple[str, str]]:
        for plugin in self._plugins.values():
            if isinstance(plugin, JsEntryPointProvider):
                entry_point_alias = 'betty%s' % hashlib.sha256(
                    plugin.name().encode()).hexdigest()
                yield entry_point_alias, plugin.name()

    @property
    def package_directory_path(self) -> str:
        return '%s/js' % dirname(__file__)
