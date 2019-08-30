import hashlib
import json
import os
import shutil
from os.path import join, dirname
from subprocess import check_call
from tempfile import mkdtemp
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


class _NodeModulesBackup:
    def __init__(self, package_path: str):
        self._package_path = package_path

    def __enter__(self):
        self._tmp = mkdtemp()
        try:
            # Remove Betty plugin packages from node_modules. If they're required, they'll be rebuilt, but if they're
            # not, they'll cause stale symbolic links, causing fatal npm errors.
            node_modules_path = join(self._package_path, 'node_modules')
            for package_path in os.listdir(node_modules_path):
                if package_path.startswith('betty-'):
                    os.unlink(join(node_modules_path, package_path))

            shutil.move(join(self._package_path, 'node_modules'), self._tmp)
        except FileNotFoundError:
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            shutil.move(join(self._tmp, 'node_modules'),
                        join(self._package_path, 'node_modules'))
        except FileNotFoundError:
            pass
        shutil.rmtree(self._tmp)


class Js(Plugin, JsPackageProvider):
    def __init__(self, file_system: FileSystem, plugins: Dict, www_directory_path: str, cache_directory_path: str):
        betty_instance_id = hashlib.sha1(
            betty.__path__[0].encode()).hexdigest()
        self._directory_path = join(
            cache_directory_path, 'js-%s' % betty_instance_id)
        self._js_package_path = join(self._directory_path, self.name())
        self._file_system = file_system
        self._plugins = plugins
        self._www_directory_path = www_directory_path

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(site.resources, site.plugins, site.configuration.www_directory_path, site.configuration.cache_directory_path)

    def subscribes_to(self):
        return [
            (PostRenderEvent, lambda event: self._build_instance_directory(
                event.environment)),
            (PostRenderEvent, lambda event: self._install()),
            (PostRenderEvent, lambda event: self._webpack()),
        ]

    def _build_instance_directory(self, environment: Environment) -> None:
        with _NodeModulesBackup(self._js_package_path):
            # Remove an existing instance directory, if it exists.
            try:
                shutil.rmtree(self.directory_path)
            except FileNotFoundError:
                pass
            dependencies = {}
            for plugin in self._plugins.values():
                if isinstance(plugin, JsPackageProvider):
                    shutil.copytree(plugin.package_directory_path,
                                    join(self.directory_path, plugin.name()))
                    render_tree(join(self.directory_path,
                                     plugin.name()), environment)
                    if not isinstance(plugin, self.__class__):
                        dependencies['betty-%s' % plugin.name()] = 'file:%s' % join(
                            self.directory_path, plugin.name())
                        with open(join(self.directory_path, plugin.name(), 'package.json'), 'r+') as package_json_f:
                            package_json = json.load(package_json_f)
                            package_json['name'] = plugin.name()
                            package_json_f.seek(0)
                            json.dump(package_json, package_json_f)
        with open(join(self._js_package_path, 'package.json'), 'r+') as package_json_f:
            package_json = json.load(package_json_f)
            package_json['dependencies'].update(dependencies)
            package_json['scripts'] = {
                'webpack': 'webpack --config ./webpack.config.js',
            }
            package_json_f.seek(0)
            json.dump(package_json, package_json_f)

    def _install(self) -> None:
        os.makedirs(self.directory_path, 0o700, True)
        check_call(['npm', 'install', '--production'],
                   cwd=self._js_package_path)

    def _webpack(self) -> None:
        self._file_system.copy2(
            join(self._www_directory_path, 'betty.css'), join(self._js_package_path, 'betty.css'))

        # Build the assets.
        check_call(['npm', 'run', 'webpack'], cwd=self._js_package_path)

        # Move the Webpack output to the Betty output.
        try:
            shutil.copytree(join(self.directory_path, 'output', 'images'),
                            join(self._www_directory_path, 'images'))
        except FileNotFoundError:
            # There may not be any images.
            pass
        shutil.copy2(join(self.directory_path, 'output', 'betty.css'),
                     join(self._www_directory_path, 'betty.css'))
        shutil.copy2(join(self.directory_path, 'output', 'betty.js'),
                     join(self._www_directory_path, 'betty.js'))

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
