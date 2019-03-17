import os
import re
import shutil
from os.path import join, splitext
from subprocess import Popen
from typing import Iterable

from jinja2 import Environment, select_autoescape, evalcontextfilter, escape, FileSystemLoader
from markupsafe import Markup

import betty
from betty.ancestry import Entity
from betty.npm import install, BETTY_INSTANCE_NPM_DIR
from betty.path import iterfiles
from betty.site import Site


def render(site: Site) -> None:
    environment = Environment(
        loader=FileSystemLoader(join(betty.RESOURCE_PATH, 'templates')),
        autoescape=select_autoescape(['html'])
    )
    environment.globals['site'] = site
    environment.filters['paragraphs'] = _render_html_paragraphs

    _render_public(site, environment)
    _render_webpack(site)
    _render_documents(site)
    _render_entity_type(site, environment,
                        site.ancestry.people.values(), 'person')
    _render_entity_type(site, environment,
                        site.ancestry.places.values(), 'place')
    _render_entity_type(site, environment,
                        site.ancestry.events.values(), 'event')


def _create_directory(path: str) -> None:
    os.makedirs(path, 0o755, True)


def _create_file(path: str) -> object:
    _create_directory(os.path.dirname(path))
    return open(path, 'w')


def _create_html_file(path: str) -> object:
    return _create_file(os.path.join(path, 'index.html'))


def _render_public(site: Site, environment: Environment) -> None:
    template_loader = FileSystemLoader('/')
    public_path = join(betty.RESOURCE_PATH, 'public')
    for file_path in iterfiles(public_path):
        destination_path = join(
            site.configuration.output_directory_path, file_path[len(public_path) + 1:])
        if file_path.endswith('.j2'):
            destination_path = destination_path[:-3]
            with _create_file(destination_path) as f:
                template = template_loader.load(
                    environment, file_path, environment.globals)
                f.write(template.render())
        else:
            shutil.copy2(file_path, destination_path)


def _render_webpack(site: Site) -> None:
    install()

    asset_types = ('css', 'js')

    # Set up Webpack's input directories.
    for asset_type in asset_types:
        webpack_asset_type_input_dir = join(
            BETTY_INSTANCE_NPM_DIR, 'input', asset_type)
        try:
            shutil.rmtree(webpack_asset_type_input_dir)
        except FileNotFoundError:
            pass
        shutil.copytree(join(betty.RESOURCE_PATH, asset_type),
                        webpack_asset_type_input_dir)

    # Build the assets.
    args = ['./node_modules/.bin/webpack', '--config', join(betty.RESOURCE_PATH,
                                                            'webpack.config.js')]
    Popen(args, cwd=BETTY_INSTANCE_NPM_DIR, shell=True).wait()

    # Move the Webpack output to the Betty output.
    for asset_type in asset_types:
        asset_filename = 'betty.%s' % asset_type
        shutil.copy2(join(BETTY_INSTANCE_NPM_DIR, 'output', asset_filename),
                     join(site.configuration.output_directory_path, asset_filename))


def _render_documents(site: Site) -> None:
    documents_directory_path = os.path.join(
        site.configuration.output_directory_path, 'document')
    _create_directory(documents_directory_path)
    for document in site.ancestry.documents.values():
        destination = os.path.join(documents_directory_path,
                                   document.id + splitext(document.file.path)[1])
        shutil.copy2(document.file.path, destination)


def _render_entity_type(site: Site, environment: Environment, entities: Iterable[Entity],
                        entity_type_name: str) -> None:
    entity_type_path = os.path.join(
        site.configuration.output_directory_path, entity_type_name)
    with _create_html_file(entity_type_path) as f:
        f.write(environment.get_template('list-%s.html.j2' % entity_type_name).render({
            'entity_type_name': entity_type_name,
            'entities': sorted(entities, key=lambda entity: entity.label),
        }))
    for entity in entities:
        _render_entity(site, environment, entity, entity_type_name)


def _render_entity(site: Site, environment: Environment, entity: Entity, entity_type_name: str) -> None:
    entity_path = os.path.join(
        site.configuration.output_directory_path, entity_type_name, entity.id)
    with _create_html_file(entity_path) as f:
        f.write(environment.get_template('%s.html.j2' % entity_type_name).render({
            entity_type_name: entity,
        }))


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@evalcontextfilter
def _render_html_paragraphs(eval_ctx, text: str) -> str:
    """Converts newlines to <p> and <br> tags.

    Taken from http://jinja.pocoo.org/docs/2.10/api/#custom-filters."""
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', Markup('<br>\n'))
                          for p in _paragraph_re.split(escape(text)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result
