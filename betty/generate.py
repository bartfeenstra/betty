import logging
import os
from json import dump
from os import chmod, path
from typing import Iterable, Any, Union

from betty.ancestry import Resource, Identifiable
from betty.event import Event
from betty.openapi import build_specification
from betty.site import Site


IdentifiableResource = Union[Resource, Identifiable]


class PostGenerateEvent(Event):
    pass  # pragma: no cover


async def generate(site: Site) -> None:
    logger = logging.getLogger()
    await site.assets.copy_tree(path.join('public', 'static'),
                                site.configuration.www_directory_path)
    await site.renderer.render_tree(site.configuration.www_directory_path)
    for locale, locale_configuration in site.configuration.locales.items():
        async with site.with_locale(locale) as site:
            if site.configuration.multilingual:
                www_directory_path = path.join(
                    site.configuration.www_directory_path, locale_configuration.alias)
            else:
                www_directory_path = site.configuration.www_directory_path

            await site.assets.copy_tree(path.join('public', 'localized'), www_directory_path)
            await site.renderer.render_tree(www_directory_path)

            await _generate_resource_type(www_directory_path, site.ancestry.files.values(
            ), 'file', site)
            logger.info('Rendered %d files in %s.' %
                        (len(site.ancestry.files), locale))
            await _generate_resource_type(www_directory_path, site.ancestry.people.values(
            ), 'person', site)
            logger.info('Rendered %d people in %s.' %
                        (len(site.ancestry.people), locale))
            await _generate_resource_type(www_directory_path, site.ancestry.places.values(
            ), 'place', site)
            logger.info('Rendered %d places in %s.' %
                        (len(site.ancestry.places), locale))
            await _generate_resource_type(www_directory_path, site.ancestry.events.values(
            ), 'event', site)
            logger.info('Rendered %d events in %s.' %
                        (len(site.ancestry.events), locale))
            await _generate_resource_type(www_directory_path, site.ancestry.citations.values(
            ), 'citation', site)
            logger.info('Rendered %d citations in %s.' %
                        (len(site.ancestry.citations), locale))
            await _generate_resource_type(www_directory_path, site.ancestry.sources.values(
            ), 'source', site)
            logger.info('Rendered %d sources in %s.' %
                        (len(site.ancestry.sources), locale))
            _generate_openapi(www_directory_path, site)
            logger.info('Rendered OpenAPI documentation.')
    chmod(site.configuration.www_directory_path, 0o755)
    for directory_path, subdirectory_names, file_names in os.walk(site.configuration.www_directory_path):
        for subdirectory_name in subdirectory_names:
            chmod(path.join(directory_path, subdirectory_name), 0o755)
        for file_name in file_names:
            chmod(path.join(directory_path, file_name), 0o644)
    await site.event_dispatcher.dispatch(PostGenerateEvent())


async def _generate_resource_type(www_directory_path: str, resources: Iterable[IdentifiableResource], resource_type_name: str, site: Site) -> None:
    await _generate_resource_list(site, www_directory_path, resources, resource_type_name)
    # @todo We now generate each resource in isolation.
    # @todo This means that for each resource, the FileSystem goes over each FS path to copy files.
    # @todo For each resource, the same files are overridden, added, and, in the future, removed.
    # @todo If we need to copy a tree to many destinations, we want to 'compile' the steps above.
    # @todo 1) Either refactor FileSystem.copytree() to become a context manager: `with FileSystem.copytree(source_path) as copytree: copytree(desination_path)`
    # @todo 2) Or refactor FileSystem.copytree() to take an Iterable[str] destination_path argument.
    # @todo Internally, FileSystem.copytree() would first copy all files to a temporary directory, from which everything is then copied to all destination directories.
    # @todo If the destination directory does not exist, the source directory
    # @todo
    resource_template_directory_path = path.join('templates', 'resource', resource_type_name)
    async with site.assets.copy_tree_to(resource_template_directory_path) as copy_tree_to:
        for resource in resources:
            destination_path = path.join(www_directory_path, resource.resource_type_name, resource.id)
            await copy_tree_to.copy_to(destination_path)
            await site.renderer.render_tree(destination_path, {
                'file_resource': resource,
            })


async def _generate_resource_list(site: Site, www_directory_path: str, resources: Iterable[IdentifiableResource], resource_type_name: str, ) -> None:
    template_directory_path = path.join('templates', 'resource-list', resource_type_name)
    destination_path = path.join(www_directory_path, resource_type_name)
    await site.assets.copy_tree(template_directory_path, destination_path)
    await site.renderer.render_tree(destination_path, {
        'file_resources': resources,
    })


# @todo Move this to the list *.json.j2 files.
def _generate_entity_type_list_json(www_directory_path: str, entities: Iterable[Any], entity_type_name: str, site: Site) -> None:
    entity_type_path = os.path.join(www_directory_path, entity_type_name)
    with _create_json_resource(entity_type_path) as f:
        data = {
            '$schema': site.static_url_generator.generate('schema.json#/definitions/%sCollection' % entity_type_name, absolute=True),
            'collection': []
        }
        for entity in entities:
            data['collection'].append(site.localized_url_generator.generate(
                entity, 'application/json', absolute=True))
        dump(data, f)


def _generate_openapi(www_directory_path: str, site: Site) -> None:
    with open(path.join(www_directory_path, 'api', 'index.json'), 'w') as f:
        dump(build_specification(site), f)
