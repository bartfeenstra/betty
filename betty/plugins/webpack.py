import shutil
from os.path import join
from subprocess import Popen

from jinja2 import Environment

import betty
from betty.event import POST_RENDER_EVENT
from betty.plugin import Plugin
from betty.plugins.npm import NpmPlugin
from betty.render import _copytree
from betty.site import Site


class WebpackPlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return {NpmPlugin}

    def subscribes_to(self):
        return {
            (POST_RENDER_EVENT, self._render),
        }

    def _render(self, site: Site, environment: Environment) -> None:
        asset_types = ('css', 'js')

        # Set up Webpack's input directories.
        for asset_type in asset_types:
            webpack_asset_type_input_dir = join(
                BETTY_INSTANCE_NPM_DIR, 'input', asset_type)
            try:
                shutil.rmtree(webpack_asset_type_input_dir)
            except FileNotFoundError:
                pass
            _copytree(environment, join(betty.RESOURCE_PATH, asset_type),
                      webpack_asset_type_input_dir)

        # Build the assets.
        args = ['./node_modules/.bin/webpack', '--config', join(betty.RESOURCE_PATH,
                                                                'webpack.config.js')]
        Popen(args, cwd=BETTY_INSTANCE_NPM_DIR, shell=True).wait()

        # Move the Webpack output to the Betty output.
        shutil.copytree(join(BETTY_INSTANCE_NPM_DIR, 'output', 'images'), join(
            site.configuration.output_directory_path, 'images'))
        shutil.copy2(join(BETTY_INSTANCE_NPM_DIR, 'output', 'betty.css'), join(
            site.configuration.output_directory_path, 'betty.css'))
        shutil.copy2(join(BETTY_INSTANCE_NPM_DIR, 'output', 'betty.js'), join(
            site.configuration.output_directory_path, 'betty.js'))
