import asyncio
import logging
import os
from contextlib import suppress
from json import dump
from os import chmod
from os.path import join
from typing import Iterable, Any, List, Union

import aiofiles
from babel import Locale
from jinja2 import Environment, TemplateNotFound

from betty import jinja2
from betty.ancestry import Resource, Identifiable
from betty.config import LocaleConfiguration
from betty.event import Event
from betty.fs import makedirs
from betty.json import JSONEncoder
from betty.openapi import build_specification
from betty.site import Site


class PostGenerateEvent(Event):
    pass  # pragma: no cover


async def generate(site: Site) -> None:
    # Render static assets first, because for monolingual sites, the static and localized www directories are the same,
    # and rendering their trees asynchronously would cause race conditions.
    await _generate_static(site)
    await asyncio.gather(*[_generate_localized(site, locale_configuration) for locale_configuration in site.configuration.locales.values()])
    await site.event_dispatcher.dispatch(PostGenerateEvent())
    chmod(site.configuration.www_directory_path, 0o755)
    for directory_path, subdirectory_names, file_names in os.walk(site.configuration.www_directory_path):
        for subdirectory_name in subdirectory_names:
            chmod(join(directory_path, subdirectory_name), 0o755)
        for file_name in file_names:
            chmod(join(directory_path, file_name), 0o644)


async def _generate_static(site: Site) -> None:
    await site.resources.copytree(join('public', 'static'),
                                  site.configuration.www_directory_path)
    await site.renderer.render_tree(site.configuration.www_directory_path)


async def _generate_localized(site: Site, locale_configuration: LocaleConfiguration) -> None:
    locale_label = Locale.parse(locale_configuration.locale, '-').get_display_name()
    logger = logging.getLogger()
    logger.info('Rendering the site in %s...' % locale_label)
    async with site.with_locale(locale_configuration.locale) as site:
        environment = jinja2.create_environment(site)
        if site.configuration.multilingual:
            www_directory_path = join(
                site.configuration.www_directory_path, locale_configuration.alias)
        else:
            www_directory_path = site.configuration.www_directory_path

        await site.resources.copytree(join('public', 'localized'), www_directory_path)
        await site.renderer.render_tree(www_directory_path)
        await asyncio.gather(
            _generate_resource_type(www_directory_path, site.ancestry.files.values(), 'file', site, locale_configuration.locale, environment),
            _generate_resource_type(www_directory_path, site.ancestry.people.values(), 'person', site, locale_configuration.locale, environment),
            _generate_resource_type(www_directory_path, site.ancestry.places.values(), 'place', site, locale_configuration.locale, environment),
            _generate_resource_type(www_directory_path, site.ancestry.events.values(), 'event', site, locale_configuration.locale, environment),
            _generate_resource_type(www_directory_path, site.ancestry.citations.values(), 'citation', site, locale_configuration.locale, environment),
            _generate_resource_type(www_directory_path, site.ancestry.sources.values(), 'source', site, locale_configuration.locale, environment),
            _generate_openapi(www_directory_path, site),
        )


def _create_file(path: str) -> object:
    makedirs(os.path.dirname(path))
    return aiofiles.open(path, 'w')


def _create_html_resource(path: str) -> object:
    return _create_file(os.path.join(path, 'index.html'))


def _create_json_resource(path: str) -> object:
    return _create_file(os.path.join(path, 'index.json'))


async def _generate_resource_type(www_directory_path: str, resources: List[Any], resource_type_name: str, site: Site,
                                  locale: str, environment: Environment) -> None:
    await asyncio.gather(
        _generate_resource_type_list_html(www_directory_path, resources, resource_type_name, environment),
        _generate_resource_type_list_json(www_directory_path, resources, resource_type_name, site),
        *[_generate_resource(www_directory_path, resource, site, locale, environment) for resource in resources]
    )
    locale_label = Locale.parse(locale, '-').get_display_name()
    logger = logging.getLogger()
    logger.info('Rendered %d %s resources in %s.' %
                (len(resources), resource_type_name, locale_label))


async def _generate_resource_type_list_html(www_directory_path: str, resources: Iterable[Any], resource_type_name: str,
                                            environment: Environment) -> None:
    resource_type_path = os.path.join(www_directory_path, resource_type_name)
    with suppress(TemplateNotFound):
        template = environment.get_template(
            'page/list-%s.html.j2' % resource_type_name)
        async with _create_html_resource(resource_type_path) as f:
            f.write(await template.render_async({
                'page_resource': '/%s/index.html' % resource_type_name,
                'resource_type_name': resource_type_name,
                'resources': resources,
            }))


async def _generate_resource_type_list_json(www_directory_path: str, resources: Iterable[Any], resource_type_name: str, site: Site) -> None:
    resource_type_path = os.path.join(www_directory_path, resource_type_name)
    async with _create_json_resource(resource_type_path) as f:
        data = {
            '$schema': site.static_url_generator.generate('schema.json#/definitions/%sCollection' % resource_type_name, absolute=True),
            'collection': []
        }
        for resource in resources:
            data['collection'].append(site.localized_url_generator.generate(
                resource, 'application/json', absolute=True))
        dump(data, f)


async def _generate_resource(www_directory_path: str, resource: Resource, site: Site, locale: str, environment: Environment) -> None:
    await _generate_resource_html(www_directory_path, resource, environment)
    await _generate_resource_json(www_directory_path, resource, site, locale)


async def _generate_resource_html(www_directory_path: str, resource: Union[Resource, Identifiable], environment: Environment) -> None:
    resource_path = os.path.join(www_directory_path, resource.resource_type_name, resource.id)
    async with _create_html_resource(resource_path) as f:
        f.write(await environment.get_template('page/%s.html.j2' % resource.resource_type_name).render_async({
            'page_resource': resource,
            resource.resource_type_name: resource,
        }))


async def _generate_resource_json(www_directory_path: str, resource: Union[Resource, Identifiable], site: Site, locale: str) -> None:
    resource_path = os.path.join(www_directory_path, resource.resource_type_name, resource.id)
    async with _create_json_resource(resource_path) as f:
        dump(resource, f, cls=JSONEncoder.get_factory(site, locale))


async def _generate_openapi(www_directory_path: str, site: Site) -> None:
    async with aiofiles.open(join(www_directory_path, 'api', 'index.json'), 'w') as f:
        dump(build_specification(site), f)
