import logging
import os
from json import dump
from os import chmod, path
from typing import Iterable, Union

from babel import Locale

from betty.ancestry import Resource, Identifiable
from betty.openapi import build_specification
from betty.site import Site


IdentifiableResource = Union[Resource, Identifiable]


class PostStaticGenerator:
    async def post_static_generate(self) -> None:
        raise NotImplementedError


class PostGenerator:
    async def post_generate(self) -> None:
        raise NotImplementedError


async def generate(site: Site) -> None:
    logger = logging.getLogger()
    await site.assets.copy_tree(path.join('public', 'static'),
                                site.configuration.www_directory_path)
    await site.renderer.render_tree(site.configuration.www_directory_path)
    await site.dispatcher.dispatch(PostStaticGenerator, 'post_static_generate')()
    for locale, locale_configuration in site.configuration.locales.items():
        async with site.with_locale(locale) as site:
            if site.configuration.multilingual:
                www_directory_path = path.join(
                    site.configuration.www_directory_path, locale_configuration.alias)
            else:
                www_directory_path = site.configuration.www_directory_path

            await site.assets.copy_tree(path.join('public', 'localized'), www_directory_path)
            await site.renderer.render_tree(www_directory_path)

            locale_label = Locale.parse(locale, '-').get_display_name()
            resources_by_type = {
                'file': site.ancestry.files.values(),
                'person': site.ancestry.people.values(),
                'place': site.ancestry.places.values(),
                'event': site.ancestry.events.values(),
                'citation': site.ancestry.citations.values(),
                'source': site.ancestry.sources.values(),
            }
            for resource_type, resources in resources_by_type.items():
                await _generate_resource_type(www_directory_path, resources, resource_type, site)
                logger.info('Generated %d %s resources in %s.' %
                            (len(site.ancestry.files), resource_type, locale_label))
            _generate_openapi(www_directory_path, site)
            logger.info('Generated OpenAPI documentation in %s.', locale_label)
    chmod(site.configuration.www_directory_path, 0o755)
    for directory_path, subdirectory_names, file_names in os.walk(site.configuration.www_directory_path):
        for subdirectory_name in subdirectory_names:
            chmod(path.join(directory_path, subdirectory_name), 0o755)
        for file_name in file_names:
            chmod(path.join(directory_path, file_name), 0o644)
    await site.dispatcher.dispatch(PostGenerator, 'post_generate')()


async def _generate_resource_type(www_directory_path: str, resources: Iterable[IdentifiableResource], resource_type_name: str, site: Site) -> None:
    resources_template_directory_path = path.join('templates', 'resource-collection', resource_type_name)
    resources_destination_path = path.join(www_directory_path, resource_type_name)
    await site.assets.copy_tree(resources_template_directory_path, resources_destination_path)
    if path.exists(resources_destination_path):
        await site.renderer.render_tree(resources_destination_path, {
            'file_resources': resources,
        })

    resource_template_directory_path = path.join('templates', 'resource', resource_type_name)
    async with site.assets.copy_tree_to(resource_template_directory_path) as copy_tree_to:
        for resource in resources:
            resource_destination_path = path.join(www_directory_path, resource.resource_type_name, resource.id)
            await copy_tree_to(resource_destination_path)
            await site.renderer.render_tree(resource_destination_path, {
                'file_resource': resource,
            })


def _generate_openapi(www_directory_path: str, site: Site) -> None:
    with open(path.join(www_directory_path, 'api', 'index.json'), 'w') as f:
        dump(build_specification(site), f)
