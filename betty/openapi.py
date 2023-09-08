from betty import about
from betty.app import App
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
                        'description': 'Unauthorized',
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/betty/error',
                                },
                            },
                        },
                    },
                    '403': {
                        'description': 'Forbidden',
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/betty/error',
                                },
                            },
                        },
                    },
                    '404': {
                        'description': 'Not found',
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
                        'description': 'The ID for the resource to retrieve.',
                        'schema': {
                            'type': 'localizering',
                        },
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
                collection_path = f'/{entity_type_url_name}/index.json'
                single_path = f'/{entity_type_url_name}/{{id}}/index.json'
            specification['paths'].update({  # type: ignore[union-attr]
                collection_path: {
                    'get': {
                        'summary': f'Retrieve the collection of {entity_type_name} entities.',
                        'responses': {
                            '200': {
                                'description': f'The collection of {entity_type_name} entities.',
                                'content': {
                                    'application/json': {},
                                },
                            },
                        },
                    },
                },
                single_path: {
                    'get': {
                        'summary': f'Retrieve a single {entity_type_name} entity.',
                        'responses': {
                            '200': {
                                'description': f'The {entity_type_name} entity.',
                                'content': {
                                    'application/json': {},
                                },
                            },
                        },
                    },
                },
            })

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

        return specification
