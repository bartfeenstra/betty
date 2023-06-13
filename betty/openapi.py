from betty import about
from betty.app import App
from betty.media_type import EXTENSIONS
from betty.model import get_entity_type_name
from betty.serde.dump import DictDump, Dump
from betty.string import camel_case_to_kebab_case


class Specification:
    def __init__(self, app: App):
        self._app = app

    def build(self) -> DictDump[Dump]:
        specification: DictDump[Dump] = {
            'openapi': '3.1.0',
            'servers': [
                {
                    'url': self._app.static_url_generator.generate('/', absolute=True),
                }
            ],
            'info': {
                'title': 'Betty',
                'version': about.version_label()
            },
            'paths': {},
            'components': {
                'responses': {
                    '401': {
                        'description': self._app.localizer._('Unauthorized'),
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/betty/error',
                                },
                            },
                        },
                    },
                    '403': {
                        'description': self._app.localizer._('Forbidden'),
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/betty/error',
                                },
                            },
                        },
                    },
                    '404': {
                        'description': self._app.localizer._('Not found'),
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/betty/error',
                                },
                            },
                        },
                    },
                },
                'parameters': {
                    'id': {
                        'name': 'id',
                        'in': 'path',
                        'required': True,
                        'description': self._app.localizer._('The ID for the resource to retrieve.'),
                        'schema': {
                            'type': 'string',
                        },
                    },
                },
                'headers': {
                    'Content-Language': {
                        'description': self._app.localizer._('An HTTP [Content-Language](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Language) header.'),
                        'schema': {
                            'type': 'string',
                        },
                        'example': self._app.project.configuration.locales.default.locale,
                    },
                },
                'schemas': {
                    'betty': {
                        '$ref': self._app.static_url_generator.generate('/schema.json#/definitions'),
                    },
                },
            },
        }

        # Add entity operations.
        for entity_type in self._app.entity_types:
            entity_type_name = get_entity_type_name(entity_type)
            entity_type_url_name = camel_case_to_kebab_case(get_entity_type_name(entity_type))
            if self._app.project.configuration.content_negotiation:
                collection_path = f'/{entity_type_url_name}/'
                single_path = f'/{entity_type_url_name}/{{id}}/'
            else:
                collection_path = f'/{{locale}}/{entity_type_url_name}/index.json'
                single_path = f'/{{locale}}/{entity_type_url_name}/{{id}}/index.json'
            specification['paths'].update({  # type: ignore[union-attr]
                collection_path: {
                    'get': {
                        'summary': self._app.localizer._('Retrieve the collection of {entity_type} entities.').format(
                            entity_type=entity_type_name,
                        ),
                        'responses': {
                            '200': {
                                'description': self._app.localizer._('The collection of {entity_type} entities.').format(
                                    entity_type=entity_type_name,
                                ),
                                'content': {
                                    'application/json': {},
                                },
                            },
                        },
                    },
                },
                single_path: {
                    'get': {
                        'summary': self._app.localizer._('Retrieve a single {entity_type} entity.').format(
                            entity_type=entity_type_name,
                        ),
                        'responses': {
                            '200': {
                                'description': self._app.localizer._('The {entity_type} entity.').format(
                                    entity_type=entity_type_name,
                                ),
                                'content': {
                                    'application/json': {},
                                },
                            },
                        },
                    },
                },
            })

        # Add components for content negotiation.
        if self._app.project.configuration.content_negotiation:
            specification['components']['parameters']['Accept'] = {  # type: ignore[call-overload, index]
                'name': 'Accept',
                'in': 'header',
                'description': self._app.localizer._('An HTTP [Accept](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept) header.'),
                'schema': {
                    'enum': list(EXTENSIONS.keys()),
                },
            }
            specification['components']['parameters']['Accept-Language'] = {  # type: ignore[call-overload, index]
                'name': 'Accept-Language',
                'in': 'header',
                'description': self._app.localizer._('An HTTP [Accept-Language](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Language) header.'),
                'schema': {
                    'type': 'string',
                },
                'example': self._app.project.configuration.locales[self._app.project.configuration.locales.default.locale].alias,
            }
            specification['components']['schemas']['html'] = {  # type: ignore[call-overload, index]
                'type': 'string',
                'description': self._app.localizer._('An HTML5 document.'),
            }
        else:
            specification['components']['parameters']['locale'] = {  # type: ignore[call-overload, index]
                'name': 'locale',
                'in': 'path',
                'required': True,
                'description': self._app.localizer._('A locale name.'),
                'schema': {
                    'type': 'string',
                    'enum': [*self._app.project.configuration.locales],
                },
                'example': self._app.project.configuration.locales[self._app.project.configuration.locales.default.locale].alias,
            }

        # Add default behavior to all requests.
        for path in specification['paths']:  # type: ignore[union-attr]
            specification['paths'][path]['get']['responses'].update({  # type: ignore[call-overload, index, union-attr]
                '401': {
                    '$ref': '#/components/responses/401',
                },
                '403': {
                    '$ref': '#/components/responses/403',
                },
                '404': {
                    '$ref': '#/components/responses/404',
                },
            })
            if self._app.project.configuration.content_negotiation:
                specification['paths'][path]['parameters'] = [  # type: ignore[index]
                    {
                        '$ref': '#/components/parameters/Accept',
                    },
                    {
                        '$ref': '#/components/parameters/Accept-Language',
                    },
                ]
            else:
                specification['paths'][path]['parameters'] = [  # type: ignore[index]
                    {
                        '$ref': '#/components/parameters/locale',
                    },
                ]

        # Add default behavior to all responses.
        if self._app.project.configuration.content_negotiation:
            responses = list(specification['components']['responses'].values())  # type: ignore[call-overload, index, union-attr]
            for path in specification['paths']:  # type: ignore[union-attr]
                responses.append(
                    specification['paths'][path]['get']['responses']['200'])  # type: ignore[call-overload, index]
            for response in responses:
                response['content']['text/html'] = {  # type: ignore[call-overload, index]
                    'schema': {
                        '$ref': '#/components/schemas/html'
                    }
                }
                if 'headers' not in response:  # type: ignore[operator]
                    response['headers'] = {}  # type: ignore[index]
                response['headers']['Content-Language'] = {  # type: ignore[call-overload, index]
                    '$ref': '#/components/headers/Content-Language',
                }

        return specification
