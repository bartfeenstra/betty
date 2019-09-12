import hashlib
import json
import shutil
from os import path
from os.path import dirname
from subprocess import check_call
from tempfile import mkdtemp
from typing import Tuple, Dict, Iterable, Optional

from jinja2 import Environment

import betty
from betty.fs import FileSystem
from betty.plugin import Plugin
from betty.render import PostRenderEvent, render_tree
from betty.site import Site


class JsPackageProvider:
    pass


class JsEntryPointProvider:
    pass


class _NodeModulesBackup:
    def __init__(self, package_path: str):
        self._package_path = package_path

    def __enter__(self):
        self._tmp = mkdtemp()
        try:
            shutil.move(path.join(self._package_path,
                                  'node_modules'), self._tmp)
        except FileNotFoundError:
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            shutil.move(path.join(self._tmp, 'node_modules'),
                        path.join(self._package_path, 'node_modules'))
        except FileNotFoundError:
            pass
        shutil.rmtree(self._tmp)


def betty_instance_id():
    return hashlib.md5(betty.__path__[0].encode()).hexdigest()


class Js(Plugin, JsPackageProvider):
    def __init__(self, file_system: FileSystem, plugins: Dict, www_directory_path: str, cache_directory_path: str):
        self._cache_directory_path = cache_directory_path
        self._file_system = file_system
        self._plugins = plugins
        self._www_directory_path = www_directory_path

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(site.resources, site.plugins, site.configuration.www_directory_path,
                   site.configuration.cache_directory_path)

    def subscribes_to(self):
        return [
            (PostRenderEvent, lambda event: self._render(event.environment)),
        ]

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)

    def _render(self, environment: Environment) -> None:
        js_plugins = list([plugin for plugin in self._plugins.values(
        ) if isinstance(plugin, JsPackageProvider)])
        js_plugin_names = [plugin.name() for plugin in js_plugins]
        build_id = hashlib.md5(':'.join(js_plugin_names).encode()).hexdigest()
        build_directory_path = path.join(
            self._cache_directory_path, self.name(), betty_instance_id(), build_id)

        # Build plugins' JavaScript assets.
        dependencies = {}
        for plugin in [self] + js_plugins:
            plugin_build_directory_path = path.join(
                build_directory_path, plugin.name())
            with _NodeModulesBackup(plugin_build_directory_path):
                try:
                    shutil.rmtree(plugin_build_directory_path)
                except FileNotFoundError:
                    pass
                shutil.copytree(path.join(plugin.resource_directory_path, 'js'),
                                plugin_build_directory_path)
            render_tree(plugin_build_directory_path, environment)
            if not isinstance(plugin, self.__class__):
                dependencies['%s' % plugin.name(
                )] = 'file:%s' % plugin_build_directory_path
                with open(path.join(plugin_build_directory_path, 'package.json'), 'r+') as package_json_f:
                    package_json = json.load(package_json_f)
                    package_json['name'] = plugin.name()
                    package_json_f.seek(0)
                    json.dump(package_json, package_json_f)

        js_plugin_build_directory_path = path.join(
            build_directory_path, self.name())

        # Add dependencies to the JavaScript plugin.
        with open(path.join(js_plugin_build_directory_path, 'package.json'), 'r+') as package_json_f:
            package_json = json.load(package_json_f)
            package_json['dependencies'].update(dependencies)
            package_json['scripts'] = {
                'webpack': 'webpack --config ./webpack.config.js',
            }
            package_json_f.seek(0)
            json.dump(package_json, package_json_f)

        # Install third-party dependencies.
        check_call(['npm', 'install', '--production'],
                   cwd=js_plugin_build_directory_path)

        # Run Webpack.
        self._file_system.copy2(path.join(self._www_directory_path, 'betty.css'), path.join(
            js_plugin_build_directory_path, 'betty.css'))
        check_call(['npm', 'run', 'webpack'],
                   cwd=js_plugin_build_directory_path)
        try:
            shutil.copytree(path.join(build_directory_path, 'output', 'images'), path.join(
                self._www_directory_path, 'images'))
        except FileNotFoundError:
            # There may not be any images.
            pass
        shutil.copy2(path.join(build_directory_path, 'output', 'betty.css'), path.join(
            self._www_directory_path, 'betty.css'))
        shutil.copy2(path.join(build_directory_path, 'output', 'betty.js'), path.join(
            self._www_directory_path, 'betty.js'))

    @property
    def entry_points(self) -> Iterable[Tuple[str, str]]:
        for plugin in self._plugins.values():
            if isinstance(plugin, JsEntryPointProvider):
                entry_point_alias = 'betty%s' % hashlib.md5(
                    plugin.name().encode()).hexdigest()
                yield entry_point_alias, plugin.name()
