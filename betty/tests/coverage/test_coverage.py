from __future__ import annotations

from _ast import Expr, Constant
from ast import parse, iter_child_nodes
from collections import defaultdict
from collections.abc import (
    Sequence,
    Callable,
    Mapping,
    AsyncIterable,
    MutableMapping,
    Iterable,
)
from configparser import ConfigParser
from importlib import import_module
from inspect import getmembers, isfunction, isclass, isdatadescriptor
from pathlib import Path
from typing import Protocol, Any, cast, TypeAlias

import aiofiles
import pytest

from betty.fs import iterfiles, ROOT_DIRECTORY_PATH
from betty.string import snake_case_to_upper_camel_case
from betty.tests.coverage.fixtures import (
    module_function_with_test,
    module_function_without_test,
    module_class_with_test,
    module_class_without_test,
    module_class_function_with_test,
    module_class_function_without_test,
    _module_private,
    module_with_test,
    module_without_test,
)
from betty.warnings import BettyDeprecationWarning


class TestKnownToBeMissing:
    pass  # pragma: no cover


_ModuleFunctionExistsIgnore: TypeAlias = None
_ModuleFunctionIgnore = _ModuleFunctionExistsIgnore | type[TestKnownToBeMissing]
_ModuleClassExistsIgnore = Mapping[str, _ModuleFunctionIgnore]
_ModuleClassIgnore = _ModuleClassExistsIgnore | type[TestKnownToBeMissing]
_ModuleMemberIgnore = _ModuleFunctionIgnore | _ModuleClassIgnore
_ModuleExistsIgnore = Mapping[str, _ModuleMemberIgnore]
_ModuleIgnore = _ModuleExistsIgnore | type[TestKnownToBeMissing]


# Keys are paths to module files with ignore rules. These paths area relative to the project root directory.
# Values are either the type :py:class:`TestModuleKnownToBeMissing` as a value, or a set containing the names
# of the module's top-level functions and classes to ignore.
# This baseline MUST NOT be extended. It SHOULD decrease in size as more coverage is added to Betty over time.
_BASELINE: Mapping[str, _ModuleIgnore] = {
    "betty/__init__.py": TestKnownToBeMissing,
    "betty/_patch.py": TestKnownToBeMissing,
    "betty/about.py": {
        "is_development": TestKnownToBeMissing,
        "is_stable": TestKnownToBeMissing,
        "report": TestKnownToBeMissing,
    },
    "betty/app/__init__.py": {
        "App": {
            "__aenter__": TestKnownToBeMissing,
            "__aexit__": TestKnownToBeMissing,
            "__del__": TestKnownToBeMissing,
            "discover_extension_types": TestKnownToBeMissing,
            "assets": TestKnownToBeMissing,
            "binary_file_cache": TestKnownToBeMissing,
            "cache": TestKnownToBeMissing,
            "dispatcher": TestKnownToBeMissing,
            "entity_types": TestKnownToBeMissing,
            "event_types": TestKnownToBeMissing,
            "http_client": TestKnownToBeMissing,
            "jinja2_environment": TestKnownToBeMissing,
            "localizer": TestKnownToBeMissing,
            "localizers": TestKnownToBeMissing,
            "process_pool": TestKnownToBeMissing,
            "project": TestKnownToBeMissing,
            "renderer": TestKnownToBeMissing,
            "servers": TestKnownToBeMissing,
            "start": TestKnownToBeMissing,
            "static_url_generator": TestKnownToBeMissing,
            "stop": TestKnownToBeMissing,
            "url_generator": TestKnownToBeMissing,
        },
        "AppConfiguration": TestKnownToBeMissing,
    },
    "betty/app/extension/__init__.py": {
        "ConfigurableExtension": TestKnownToBeMissing,
        "CyclicDependencyError": TestKnownToBeMissing,
        "Dependencies": TestKnownToBeMissing,
        "Dependents": TestKnownToBeMissing,
        "Extension": {
            "app": TestKnownToBeMissing,
            "disable_requirement": TestKnownToBeMissing,
        },
        "ExtensionDispatcher": {
            "dispatch": TestKnownToBeMissing,
        },
        # This is an empty class.
        "ExtensionError": TestKnownToBeMissing,
        # This is an interface.
        "Extensions": TestKnownToBeMissing,
        # This is an empty class.
        "ExtensionTypeError": TestKnownToBeMissing,
        "ExtensionTypeImportError": TestKnownToBeMissing,
        "ExtensionTypeInvalidError": TestKnownToBeMissing,
        "format_extension_type": TestKnownToBeMissing,
        "get_extension_type": TestKnownToBeMissing,
        "get_extension_type_by_extension": TestKnownToBeMissing,
        "get_extension_type_by_name": TestKnownToBeMissing,
        "get_extension_type_by_type": TestKnownToBeMissing,
        "ListExtensions": TestKnownToBeMissing,
        # This is an empty class.
        "Theme": TestKnownToBeMissing,
        # This is an interface.
        "UserFacingExtension": TestKnownToBeMissing,
    },
    # This is deprecated.
    "betty/app/extension/requirement.py": TestKnownToBeMissing,
    "betty/asyncio.py": {
        "gather": TestKnownToBeMissing,
    },
    "betty/cache/__init__.py": {
        # This is an interface.
        "Cache": TestKnownToBeMissing,
        "CacheItem": TestKnownToBeMissing,
        # This is deprecated.
        "FileCache": TestKnownToBeMissing,
    },
    "betty/cache/_base.py": TestKnownToBeMissing,
    "betty/classtools.py": TestKnownToBeMissing,
    "betty/cli.py": {
        "app_command": TestKnownToBeMissing,
        # This is an interface.
        "CommandProvider": TestKnownToBeMissing,
        "global_command": TestKnownToBeMissing,
    },
    "betty/concurrent.py": {
        "AsynchronizedLock": {
            "release": TestKnownToBeMissing,
        },
        "MultiLock": {
            "release": TestKnownToBeMissing,
        },
        "RateLimiter": {
            "__aenter__": TestKnownToBeMissing,
            "__aexit__": TestKnownToBeMissing,
        },
    },
    "betty/config.py": {
        "Configurable": TestKnownToBeMissing,
        "Configuration": TestKnownToBeMissing,
        "ConfigurationCollection": TestKnownToBeMissing,
        "ConfigurationMapping": {
            "__getitem__": TestKnownToBeMissing,
            "__iter__": TestKnownToBeMissing,
            "dump": TestKnownToBeMissing,
            "replace": TestKnownToBeMissing,
            "to_index": TestKnownToBeMissing,
            "to_key": TestKnownToBeMissing,
            "update": TestKnownToBeMissing,
        },
        "ConfigurationSequence": {
            "__getitem__": TestKnownToBeMissing,
            "__iter__": TestKnownToBeMissing,
            "dump": TestKnownToBeMissing,
            "to_index": TestKnownToBeMissing,
            "to_key": TestKnownToBeMissing,
            "update": TestKnownToBeMissing,
        },
        "FileBasedConfiguration": {
            "__del__": TestKnownToBeMissing,
            "autowrite": TestKnownToBeMissing,
            "read": TestKnownToBeMissing,
            "write": TestKnownToBeMissing,
        },
    },
    "betty/contextlib.py": {
        "SynchronizedContextManager": {
            "__enter__": TestKnownToBeMissing,
            "__exit__": TestKnownToBeMissing,
        },
    },
    "betty/deriver.py": {
        # This is an enum.
        "Derivation": TestKnownToBeMissing
    },
    "betty/dispatch.py": TestKnownToBeMissing,
    "betty/documentation.py": {
        "DocumentationServer": {
            "public_url": TestKnownToBeMissing,
            "start": TestKnownToBeMissing,
            "stop": TestKnownToBeMissing,
        },
    },
    "betty/error.py": TestKnownToBeMissing,
    "betty/extension/__init__.py": TestKnownToBeMissing,
    "betty/extension/cotton_candy/__init__.py": {
        "person_descendant_families": TestKnownToBeMissing,
        "person_timeline_events": TestKnownToBeMissing,
        "CottonCandy": TestKnownToBeMissing,
        "CottonCandyConfiguration": {
            "featured_entities": TestKnownToBeMissing,
            "link_active_color": TestKnownToBeMissing,
            "link_inactive_color": TestKnownToBeMissing,
            "primary_active_color": TestKnownToBeMissing,
            "primary_inactive_color": TestKnownToBeMissing,
        },
    },
    "betty/extension/demo/__init__.py": {
        "DemoServer": {
            "public_url": TestKnownToBeMissing,
            "start": TestKnownToBeMissing,
            "stop": TestKnownToBeMissing,
        },
    },
    "betty/extension/gramps/__init__.py": {
        "Gramps": {
            "gui_build": TestKnownToBeMissing,
        },
    },
    "betty/extension/gramps/config.py": {
        "FamilyTreeConfiguration": {
            "file_path": TestKnownToBeMissing,
        },
        "FamilyTreeConfigurationSequence": TestKnownToBeMissing,
        "GrampsConfiguration": {
            "family_trees": TestKnownToBeMissing,
        },
    },
    "betty/extension/http_api_doc/__init__.py": {
        "HttpApiDoc": {
            "webpack_entry_point_cache_keys": TestKnownToBeMissing,
        },
    },
    "betty/extension/maps/__init__.py": {
        "Maps": {
            "webpack_entry_point_cache_keys": TestKnownToBeMissing,
        },
    },
    "betty/extension/nginx/__init__.py": {
        "Nginx": {
            "commands": TestKnownToBeMissing,
            "gui_build": TestKnownToBeMissing,
            "https": TestKnownToBeMissing,
            "servers": TestKnownToBeMissing,
            "www_directory_path": TestKnownToBeMissing,
        },
    },
    "betty/extension/nginx/config.py": {
        "NginxConfiguration": {
            "https": TestKnownToBeMissing,
            "www_directory_path": TestKnownToBeMissing,
        },
    },
    "betty/extension/nginx/docker.py": TestKnownToBeMissing,
    "betty/extension/nginx/serve.py": {
        "DockerizedNginxServer": {
            "start": TestKnownToBeMissing,
            "stop": TestKnownToBeMissing,
        },
    },
    "betty/extension/privatizer/__init__.py": {
        "Privatizer": {
            "privatize": TestKnownToBeMissing,
        },
    },
    "betty/extension/trees/__init__.py": {
        "Trees": {
            "webpack_entry_point_cache_keys": TestKnownToBeMissing,
        },
    },
    "betty/extension/webpack/__init__.py": {
        "PrebuiltAssetsRequirement": {
            "summary": TestKnownToBeMissing,
        },
        "Webpack": {
            "build_requirement": TestKnownToBeMissing,
            "filters": TestKnownToBeMissing,
            "new_context_vars": TestKnownToBeMissing,
            "public_css_paths": TestKnownToBeMissing,
        },
        # This is an interface.
        "WebpackEntryPointProvider": TestKnownToBeMissing,
    },
    "betty/extension/webpack/build.py": {
        "webpack_build_id": TestKnownToBeMissing,
    },
    "betty/extension/webpack/jinja2/__init__.py": TestKnownToBeMissing,
    "betty/extension/webpack/jinja2/filter.py": TestKnownToBeMissing,
    "betty/extension/wikipedia/__init__.py": {
        "Wikipedia": {
            "filters": TestKnownToBeMissing,
            "gui_build": TestKnownToBeMissing,
        },
    },
    "betty/extension/wikipedia/config.py": {
        "WikipediaConfiguration": {
            "populate_images": TestKnownToBeMissing,
        },
    },
    "betty/fetch.py": {
        "FetchResponse": {
            # This is inherited from @dataclass.
            "__eq__": TestKnownToBeMissing,
        },
    },
    "betty/fs.py": {
        "FileSystem": {
            "__len__": TestKnownToBeMissing,
            "clear": TestKnownToBeMissing,
            "paths": TestKnownToBeMissing,
            "prepend": TestKnownToBeMissing,
        },
    },
    "betty/functools.py": {
        "filter_suppress": TestKnownToBeMissing,
        "Uniquifier": {
            "__iter__": TestKnownToBeMissing,
            "__next__": TestKnownToBeMissing,
        },
    },
    "betty/generate.py": {
        "create_file": TestKnownToBeMissing,
        "create_html_resource": TestKnownToBeMissing,
        "create_json_resource": TestKnownToBeMissing,
        "GenerationContext": TestKnownToBeMissing,
        # This is an interface.
        "Generator": TestKnownToBeMissing,
        # This is deprecated.
        "getLogger": TestKnownToBeMissing,
    },
    "betty/gramps/error.py": TestKnownToBeMissing,
    "betty/gramps/loader.py": {
        "GrampsEntityReference": TestKnownToBeMissing,
        "GrampsEntityType": TestKnownToBeMissing,
        # This is an empty class.
        "GrampsFileNotFoundError": TestKnownToBeMissing,
        "GrampsLoader": {
            "add_association": TestKnownToBeMissing,
            "add_entity": TestKnownToBeMissing,
            "load_file": TestKnownToBeMissing,
            "load_tree": TestKnownToBeMissing,
        },
        # This is an empty class.
        "GrampsLoadFileError": TestKnownToBeMissing,
        # This is an empty class.
        "XPathError": TestKnownToBeMissing,
    },
    "betty/gui/__init__.py": TestKnownToBeMissing,
    "betty/gui/app.py": {
        "ApplicationConfiguration": {
            "window_title": TestKnownToBeMissing,
        },
        "BettyPrimaryWindow": {
            "new_project": TestKnownToBeMissing,
            "open_application_configuration": TestKnownToBeMissing,
            "open_project": TestKnownToBeMissing,
            "report_bug": TestKnownToBeMissing,
            "request_feature": TestKnownToBeMissing,
            "window_title": TestKnownToBeMissing,
        },
    },
    "betty/gui/error.py": TestKnownToBeMissing,
    "betty/gui/locale.py": TestKnownToBeMissing,
    "betty/gui/logging.py": TestKnownToBeMissing,
    "betty/gui/model.py": TestKnownToBeMissing,
    "betty/gui/project.py": {
        "AddLocaleWindow": {
            "window_title": TestKnownToBeMissing,
        },
        "GenerateWindow": {
            "window_title": TestKnownToBeMissing,
        },
        "ProjectWindow": {
            "close": TestKnownToBeMissing,
            "window_title": TestKnownToBeMissing,
        },
    },
    "betty/gui/serve.py": {
        "ServeDemoWindow": {
            "window_title": TestKnownToBeMissing,
        },
        "ServeDocsWindow": {
            "window_title": TestKnownToBeMissing,
        },
        "ServeProjectWindow": {
            "window_title": TestKnownToBeMissing,
        },
    },
    "betty/gui/window.py": TestKnownToBeMissing,
    "betty/importlib.py": {
        "fully_qualified_type_name": TestKnownToBeMissing,
    },
    "betty/html.py": TestKnownToBeMissing,
    "betty/jinja2/__init__.py": TestKnownToBeMissing,
    "betty/jinja2/filter.py": TestKnownToBeMissing,
    "betty/jinja2/test.py": TestKnownToBeMissing,
    "betty/job.py": {
        "Context": {
            "cache": TestKnownToBeMissing,
        },
    },
    "betty/json/linked_data.py": TestKnownToBeMissing,
    "betty/json/schema.py": {
        "add_property": TestKnownToBeMissing,
        "ref_json_schema": TestKnownToBeMissing,
        "ref_locale": TestKnownToBeMissing,
        "Schema": {
            "validate": TestKnownToBeMissing,
        },
    },
    "betty/load.py": {
        # This is deprecated.
        "getLogger": TestKnownToBeMissing,
        # This is an interface.
        "Loader": TestKnownToBeMissing,
        # This is an interface.
        "PostLoader": TestKnownToBeMissing,
    },
    "betty/locale.py": {
        "Date": {
            "__contains__": TestKnownToBeMissing,
            "__ge__": TestKnownToBeMissing,
            "__le__": TestKnownToBeMissing,
            "datey_dump_linked_data": TestKnownToBeMissing,
            "dump_linked_data": TestKnownToBeMissing,
        },
        "DateRange": {
            "__contains__": TestKnownToBeMissing,
            "__ge__": TestKnownToBeMissing,
            "__le__": TestKnownToBeMissing,
            "comparable": TestKnownToBeMissing,
            "datey_dump_linked_data": TestKnownToBeMissing,
            "dump_linked_data": TestKnownToBeMissing,
        },
        "get_data": TestKnownToBeMissing,
        "get_display_name": TestKnownToBeMissing,
        # This is an empty class.
        "IncompleteDateError": TestKnownToBeMissing,
        "init_translation": TestKnownToBeMissing,
        "LocaleNotFoundError": TestKnownToBeMissing,
        # This is an interface.
        "Localizable": TestKnownToBeMissing,
        "Localized": TestKnownToBeMissing,
        "Localizer": TestKnownToBeMissing,
        "LocalizerRepository": {
            "__getitem__": TestKnownToBeMissing,
            "coverage": TestKnownToBeMissing,
            "get": TestKnownToBeMissing,
            "get_negotiated": TestKnownToBeMissing,
            "locales": TestKnownToBeMissing,
        },
        "ref_date": TestKnownToBeMissing,
        "ref_date_range": TestKnownToBeMissing,
        "ref_datey": TestKnownToBeMissing,
        "Str": TestKnownToBeMissing,
        "run_babel": TestKnownToBeMissing,
        "to_babel_identifier": TestKnownToBeMissing,
        "to_locale": TestKnownToBeMissing,
        "update_translations": TestKnownToBeMissing,
    },
    "betty/logging.py": {
        "CliHandler": {
            "format": TestKnownToBeMissing,
        },
    },
    "betty/media_type.py": {
        # This is an empty class.
        "InvalidMediaType": TestKnownToBeMissing,
        "MediaType": {
            "__eq__": TestKnownToBeMissing,
            "__hash__": TestKnownToBeMissing,
            "__str__": TestKnownToBeMissing,
            "parameters": TestKnownToBeMissing,
            "subtype": TestKnownToBeMissing,
            "subtypes": TestKnownToBeMissing,
            "suffix": TestKnownToBeMissing,
            "type": TestKnownToBeMissing,
        },
    },
    "betty/model/__init__.py": {
        "record_added": TestKnownToBeMissing,
        "unalias": TestKnownToBeMissing,
        "AliasedEntity": TestKnownToBeMissing,
        "BidirectionalEntityTypeAssociation": TestKnownToBeMissing,
        "BidirectionalToManyEntityTypeAssociation": TestKnownToBeMissing,
        "BidirectionalToOneEntityTypeAssociation": TestKnownToBeMissing,
        "Entity": {
            "__hash__": TestKnownToBeMissing,
            "ancestry_id": TestKnownToBeMissing,
            "dump_linked_data": TestKnownToBeMissing,
            "label": TestKnownToBeMissing,
            "type": TestKnownToBeMissing,
        },
        "EntityGraphBuilder": {
            "add_association": TestKnownToBeMissing,
            "add_entity": TestKnownToBeMissing,
        },
        "EntityCollection": TestKnownToBeMissing,
        # This is an empty class.
        "EntityTypeError": TestKnownToBeMissing,
        "EntityTypeImportError": TestKnownToBeMissing,
        "EntityTypeInvalidError": TestKnownToBeMissing,
        # This is an interface.
        "EntityTypeProvider": TestKnownToBeMissing,
        "GeneratedEntityId": TestKnownToBeMissing,
        "MultipleTypesEntityCollection": {
            "__delitem__": TestKnownToBeMissing,
            "__getitem__": TestKnownToBeMissing,
            "__iter__": TestKnownToBeMissing,
            "__len__": TestKnownToBeMissing,
            "clear": TestKnownToBeMissing,
        },
        "SingleTypeEntityCollection": {
            "__delitem__": TestKnownToBeMissing,
            "__getitem__": TestKnownToBeMissing,
            "__iter__": TestKnownToBeMissing,
            "__len__": TestKnownToBeMissing,
        },
        "ToMany": {
            "initialize": TestKnownToBeMissing,
        },
        "ToManyEntityTypeAssociation": TestKnownToBeMissing,
        "ToOneEntityTypeAssociation": TestKnownToBeMissing,
        # This is an interface.
        "UserFacingEntity": TestKnownToBeMissing,
    },
    "betty/model/ancestry.py": {
        "ref_link": TestKnownToBeMissing,
        "ref_link_collection": TestKnownToBeMissing,
        "ref_media_type": TestKnownToBeMissing,
        "ref_role": TestKnownToBeMissing,
        "resolve_privacy": TestKnownToBeMissing,
        # This is deprecated.
        "AnonymousCitation": TestKnownToBeMissing,
        # This is deprecated.
        "AnonymousSource": TestKnownToBeMissing,
        # This is static.
        "Attendee": TestKnownToBeMissing,
        # This is static.
        "Beneficiary": TestKnownToBeMissing,
        "Celebrant": TestKnownToBeMissing,
        "Citation": {
            "label": TestKnownToBeMissing,
        },
        "Dated": {
            "dump_linked_data": TestKnownToBeMissing,
        },
        "Described": {
            "dump_linked_data": TestKnownToBeMissing,
        },
        "Event": {
            "label": TestKnownToBeMissing,
        },
        "File": {
            "label": TestKnownToBeMissing,
        },
        "HasLinksEntity": TestKnownToBeMissing,
        "HasCitations": {
            "dump_linked_data": TestKnownToBeMissing,
        },
        "HasFiles": {
            "associated_files": TestKnownToBeMissing,
        },
        "HasLinks": {
            "dump_linked_data": TestKnownToBeMissing,
        },
        "HasMediaType": {
            "dump_linked_data": TestKnownToBeMissing,
        },
        "HasNotes": {
            "dump_linked_data": TestKnownToBeMissing,
        },
        "HasPrivacy": {
            "dump_linked_data": TestKnownToBeMissing,
            "own_privacy": TestKnownToBeMissing,
            "privacy": TestKnownToBeMissing,
            "private": TestKnownToBeMissing,
            "public": TestKnownToBeMissing,
        },
        "Note": {
            "entity": TestKnownToBeMissing,
            "label": TestKnownToBeMissing,
        },
        # This is static.
        "Organizer": TestKnownToBeMissing,
        "Person": {
            "label": TestKnownToBeMissing,
        },
        "PersonName": {
            "dump_linked_data": TestKnownToBeMissing,
            "label": TestKnownToBeMissing,
        },
        "Place": {
            "associated_files": TestKnownToBeMissing,
            "label": TestKnownToBeMissing,
        },
        "PlaceName": {
            "dump_linked_data": TestKnownToBeMissing,
        },
        "Presence": {
            "label": TestKnownToBeMissing,
        },
        "PresenceRole": TestKnownToBeMissing,
        "Privacy": TestKnownToBeMissing,
        "Source": {
            "label": TestKnownToBeMissing,
        },
        # This is static.
        "Speaker": TestKnownToBeMissing,
        # This is static.
        "Subject": TestKnownToBeMissing,
        # This is static.
        "Witness": TestKnownToBeMissing,
    },
    "betty/model/event_type.py": {
        "Adoption": TestKnownToBeMissing,
        "Baptism": TestKnownToBeMissing,
        "Birth": TestKnownToBeMissing,
        "Burial": TestKnownToBeMissing,
        "Conference": TestKnownToBeMissing,
        "Confirmation": TestKnownToBeMissing,
        "Correspondence": TestKnownToBeMissing,
        "CreatableDerivableEventType": TestKnownToBeMissing,
        "CreatableEventType": TestKnownToBeMissing,
        "Cremation": TestKnownToBeMissing,
        "DerivableEventType": TestKnownToBeMissing,
        "Divorce": TestKnownToBeMissing,
        "DivorceAnnouncement": TestKnownToBeMissing,
        "DuringLifeEventType": TestKnownToBeMissing,
        "Emigration": TestKnownToBeMissing,
        "EndOfLifeEventType": TestKnownToBeMissing,
        "Engagement": TestKnownToBeMissing,
        "EventTypeProvider": TestKnownToBeMissing,
        "FinalDispositionEventType": TestKnownToBeMissing,
        "Funeral": TestKnownToBeMissing,
        "Immigration": TestKnownToBeMissing,
        "Marriage": TestKnownToBeMissing,
        "MarriageAnnouncement": TestKnownToBeMissing,
        "Missing": TestKnownToBeMissing,
        "Occupation": TestKnownToBeMissing,
        "PostDeathEventType": TestKnownToBeMissing,
        "PreBirthEventType": TestKnownToBeMissing,
        "Residence": TestKnownToBeMissing,
        "Retirement": TestKnownToBeMissing,
        "StartOfLifeEventType": TestKnownToBeMissing,
        "UnknownEventType": TestKnownToBeMissing,
        "Will": TestKnownToBeMissing,
    },
    "betty/path.py": TestKnownToBeMissing,
    "betty/privatizer.py": {
        "Privatizer": {
            "has_expired": TestKnownToBeMissing,
        },
    },
    "betty/project.py": {
        "EntityReference": {
            "__eq__": TestKnownToBeMissing,
            "entity_type_is_constrained": TestKnownToBeMissing,
            "update": TestKnownToBeMissing,
        },
        "EntityTypeConfiguration": {
            "update": TestKnownToBeMissing,
        },
        "ExtensionConfiguration": {
            "dump": TestKnownToBeMissing,
            "extension_configuration": TestKnownToBeMissing,
            "update": TestKnownToBeMissing,
        },
        "ExtensionConfigurationMapping": {
            "disable": TestKnownToBeMissing,
            "enable": TestKnownToBeMissing,
        },
        "LocaleConfiguration": {
            "__hash__": TestKnownToBeMissing,
            "dump": TestKnownToBeMissing,
            "hash": TestKnownToBeMissing,
            "update": TestKnownToBeMissing,
        },
        "LocaleConfigurationMapping": {
            "multilingual": TestKnownToBeMissing,
        },
        "Project": TestKnownToBeMissing,
        "ProjectConfiguration": {
            "assets_directory_path": TestKnownToBeMissing,
            "debug": TestKnownToBeMissing,
            "entity_types": TestKnownToBeMissing,
            "extensions": TestKnownToBeMissing,
            "lifetime_threshold": TestKnownToBeMissing,
            "locales": TestKnownToBeMissing,
            "localize_www_directory_path": TestKnownToBeMissing,
            "output_directory_path": TestKnownToBeMissing,
            "project_directory_path": TestKnownToBeMissing,
            "title": TestKnownToBeMissing,
            "update": TestKnownToBeMissing,
            "www_directory_path": TestKnownToBeMissing,
        },
    },
    "betty/render.py": TestKnownToBeMissing,
    "betty/requirement.py": {
        "Requirement": {
            "details": TestKnownToBeMissing,
            "is_met": TestKnownToBeMissing,
            "reduce": TestKnownToBeMissing,
            "summary": TestKnownToBeMissing,
        },
        "RequirementError": TestKnownToBeMissing,
    },
    "betty/serde/error.py": {
        "SerdeError": {
            "contexts": TestKnownToBeMissing,
            "raised": TestKnownToBeMissing,
        },
        "SerdeErrorCollection": {
            "__iter__": TestKnownToBeMissing,
            "__len__": TestKnownToBeMissing,
            "__reduce__": TestKnownToBeMissing,
            "append": TestKnownToBeMissing,
            "assert_valid": TestKnownToBeMissing,
            "invalid": TestKnownToBeMissing,
            "raised": TestKnownToBeMissing,
            "valid": TestKnownToBeMissing,
        },
    },
    "betty/serde/format.py": {
        # This is an interface.
        "Format": TestKnownToBeMissing,
        "FormatRepository": TestKnownToBeMissing,
        "FormatStr": TestKnownToBeMissing,
        "Json": {
            "extensions": TestKnownToBeMissing,
            "label": TestKnownToBeMissing,
        },
        "Yaml": {
            "extensions": TestKnownToBeMissing,
            "label": TestKnownToBeMissing,
        },
    },
    "betty/serde/load.py": {
        "Asserter": {
            "assert_assertions": TestKnownToBeMissing,
            "assert_entity_type": TestKnownToBeMissing,
            "assert_extension_type": TestKnownToBeMissing,
            "assert_locale": TestKnownToBeMissing,
            "assert_none": TestKnownToBeMissing,
            "assert_setattr": TestKnownToBeMissing,
        },
        # This is an empty class.
        "AssertionFailed": TestKnownToBeMissing,
        # This is a deprecated class.
        "Assertions": TestKnownToBeMissing,
        "Fields": TestKnownToBeMissing,
        # This is an empty class.
        "FormatError": TestKnownToBeMissing,
        # This is an empty class.
        "LoadError": TestKnownToBeMissing,
        "OptionalField": TestKnownToBeMissing,
        "RequiredField": TestKnownToBeMissing,
    },
    "betty/serve.py": {
        "AppServer": TestKnownToBeMissing,
        "BuiltinAppServer": TestKnownToBeMissing,
        "BuiltinServer": {
            "public_url": TestKnownToBeMissing,
            "start": TestKnownToBeMissing,
            "stop": TestKnownToBeMissing,
        },
        "NoPublicUrlBecauseServerNotStartedError": TestKnownToBeMissing,
        # This is an empty class.
        "OsError": TestKnownToBeMissing,
        # This is an interface.
        "Server": TestKnownToBeMissing,
        # This is an empty class.
        "ServerNotStartedError": TestKnownToBeMissing,
        # This is an interface.
        "ServerProvider": TestKnownToBeMissing,
    },
    "betty/serde/dump.py": TestKnownToBeMissing,
    "betty/sphinx/extension/replacements.py": TestKnownToBeMissing,
    "betty/url.py": {
        # This is an abstract base class.
        "LocalizedUrlGenerator": TestKnownToBeMissing,
        "StaticPathUrlGenerator": TestKnownToBeMissing,
        # This is an abstract base class.
        "StaticUrlGenerator": TestKnownToBeMissing,
    },
    "betty/warnings.py": TestKnownToBeMissing,
    "betty/wikipedia.py": {
        "Image": TestKnownToBeMissing,
        # This is an empty class.
        "NotAPageError": TestKnownToBeMissing,
        # This is an empty class.
        "RetrievalError": TestKnownToBeMissing,
        "Summary": {
            "name": TestKnownToBeMissing,
        },
        # This is an empty class.
        "WikipediaError": TestKnownToBeMissing,
    },
}


class TestCoverage:
    async def test(self) -> None:
        tester = CoverageTester()
        with pytest.warns(BettyDeprecationWarning):
            await tester.test()


def _module_path_to_name(module_path: Path) -> str:
    relative_module_path = module_path.relative_to(ROOT_DIRECTORY_PATH)
    module_name_parts = relative_module_path.parent.parts
    if relative_module_path.name != "__init__.py":
        module_name_parts = (*module_name_parts, relative_module_path.name[:-3])
    return ".".join(module_name_parts)


class CoverageTester:
    def __init__(self):
        self._ignore_src_module_paths = self._get_ignore_src_module_paths()

    async def test(self) -> None:
        errors: MutableMapping[Path, list[str]] = defaultdict(list)
        async for file_path in iterfiles(ROOT_DIRECTORY_PATH / "betty"):
            if file_path.suffix == ".py":
                async for file_error in self._test_python_file(file_path):
                    errors[file_path].append(file_error)
        if len(errors):
            message = "Missing test coverage:"
            total_error_count = 0
            for file_path in sorted(errors.keys()):
                file_error_count = len(errors[file_path])
                total_error_count += file_error_count
                if not file_error_count:
                    continue
                message += f"\n{file_path.relative_to(ROOT_DIRECTORY_PATH)}: {file_error_count} error(s)"
                for error in errors[file_path]:
                    message += f"\n  - {error}"
            message += f"\nTOTAL: {total_error_count} error(s)"

            raise AssertionError(message)

    def _get_coveragerc_ignore_modules(self) -> Iterable[Path]:
        coveragerc = ConfigParser()
        coveragerc.read(ROOT_DIRECTORY_PATH / ".coveragerc")
        omit = coveragerc.get("run", "omit").strip().split("\n")
        for omit_pattern in omit:
            for module_path in Path().glob(omit_pattern):
                if module_path.suffix != ".py":
                    continue
                if not module_path.is_file():
                    continue
                yield module_path.resolve()

    def _get_ignore_src_module_paths(
        self,
    ) -> Mapping[Path, _ModuleIgnore]:
        return {
            **{
                Path(module_file_path_str).resolve(): members
                for module_file_path_str, members in _BASELINE.items()
            },
            **{
                module_file_path: TestKnownToBeMissing
                for module_file_path in self._get_coveragerc_ignore_modules()
            },
        }

    async def _test_python_file(self, file_path: Path) -> AsyncIterable[str]:
        # Skip tests.
        if ROOT_DIRECTORY_PATH / "betty" / "tests" in file_path.parents:
            return

        src_module_path = file_path.resolve()
        expected_test_module_path = (
            ROOT_DIRECTORY_PATH
            / "betty"
            / "tests"
            / src_module_path.relative_to(ROOT_DIRECTORY_PATH / "betty").parent
            / f"test_{src_module_path.name}"
        )
        async for error in _ModuleCoverageTester(
            src_module_path,
            expected_test_module_path,
            self._ignore_src_module_paths.get(src_module_path, {}),
        ).test():
            yield error

    async def _test_python_file_contains_docstring_only(self, file_path: Path) -> bool:
        async with aiofiles.open(file_path) as f:
            f_content = await f.read()
        f_ast = parse(f_content)
        for child in iter_child_nodes(f_ast):
            if not isinstance(child, Expr):
                return False
            if not isinstance(child.value, Constant):
                return False
        return True


class _Importable(Protocol):
    __file__: str
    __name__: str


class _ModuleCoverageTester:
    def __init__(
        self, src_module_path: Path, test_module_path: Path, ignore: _ModuleIgnore
    ):
        self._src_module_path = src_module_path
        self._test_module_path = test_module_path
        self._ignore = ignore
        self._src_module_name, self._src_functions, self._src_classes = (
            self._get_module_data(self._src_module_path)
        )

    async def test(self) -> AsyncIterable[str]:
        # Skip private modules.
        if True in (x.startswith("_") for x in self._src_module_name.split(".")):
            return

        if self._test_module_path.exists():
            if self._ignore is TestKnownToBeMissing:
                yield f"{self._src_module_path} has a matching test file at {self._test_module_path}, which was unexpectedly declared as known to be missing."
                return
            else:
                assert self._ignore is not TestKnownToBeMissing
                test_module_name, _, test_classes = self._get_module_data(
                    self._test_module_path
                )
                for src_function in self._src_functions:
                    async for error in _ModuleFunctionCoverageTester(
                        src_function,
                        test_classes,
                        self._src_module_name,
                        test_module_name,
                        cast(
                            _ModuleFunctionIgnore,
                            self._ignore.get(src_function.__name__, None),  # type: ignore[union-attr]
                        ),
                    ).test():
                        yield error

                for src_class in self._src_classes:
                    async for error in _ModuleClassCoverageTester(
                        src_class,
                        test_classes,
                        self._src_module_name,
                        test_module_name,
                        cast(
                            _ModuleClassIgnore,
                            self._ignore.get(src_class.__name__, {}),  # type: ignore[union-attr]
                        ),
                    ).test():
                        yield error
            return

        if self._ignore is TestKnownToBeMissing:
            return

        if await self._test_python_file_contains_docstring_only(self._src_module_path):
            return

        yield f"{self._src_module_path} does not have a matching test file. Expected {self._test_module_path} to exist."

    async def _test_python_file_contains_docstring_only(self, file_path: Path) -> bool:
        async with aiofiles.open(file_path) as f:
            f_content = await f.read()
        f_ast = parse(f_content)
        for child in iter_child_nodes(f_ast):
            if not isinstance(child, Expr):
                return False
            if not isinstance(child.value, Constant):
                return False
        return True

    def _get_module_data(
        self, module_path: Path
    ) -> tuple[
        str,
        Sequence[_Importable & Callable[..., Any]],
        Sequence[_Importable & type],
    ]:
        module_name = _module_path_to_name(module_path)
        return (
            module_name,
            sorted(
                self._get_members(module_name, isfunction),  # type: ignore[arg-type]
                key=lambda member: member.__name__,
            ),
            sorted(
                self._get_members(module_name, isclass),  # type: ignore[arg-type]
                key=lambda member: member.__name__,
            ),
        )

    def _get_members(
        self, module_name: str, predicate: Callable[[object], bool]
    ) -> Iterable[_Importable]:
        module = import_module(module_name)
        for member_name, _ in getmembers(module, predicate):
            # Ignore private members.
            if member_name.startswith("_"):
                continue

            # Ignore members that are not defined by the module under test (they may have been from other modules).
            imported_member = getattr(module, member_name)
            if getattr(imported_member, "__module__", None) != module_name:
                continue

            yield imported_member


class _ModuleFunctionCoverageTester:
    def __init__(
        self,
        src_function: Callable[..., Any],
        test_classes: Sequence[type],
        src_module_name: str,
        test_module_name: str,
        ignore: _ModuleFunctionIgnore,
    ):
        self._src_function = src_function
        self._test_classes = {
            test_class.__name__: test_class for test_class in test_classes
        }
        self._src_module_name = src_module_name
        self._test_module_name = test_module_name
        self._ignore = ignore

    async def test(self) -> AsyncIterable[str]:
        expected_test_class_name = (
            f"Test{snake_case_to_upper_camel_case(self._src_function.__name__)}"
        )

        if expected_test_class_name in self._test_classes:
            if self._ignore is TestKnownToBeMissing:
                yield f"The source function {self._src_module_name}.{self._src_function.__name__} has a matching test class at {self._test_classes[expected_test_class_name].__module__}.{self._test_classes[expected_test_class_name].__name__}, which was unexpectedly declared as known to be missing."
            return

        if self._ignore is TestKnownToBeMissing:
            return

        yield f"Failed to find the test class {self._test_module_name}.{expected_test_class_name} for the source function {self._src_module_name}.{self._src_function.__name__}()."


class _ModuleClassCoverageTester:
    def __init__(
        self,
        src_class: type,
        test_classes: Sequence[type],
        src_module_name: str,
        test_module_name: str,
        ignore: _ModuleClassIgnore,
    ):
        self._src_class = src_class
        self._test_classes = {
            test_class.__name__: test_class for test_class in test_classes
        }
        self._src_module_name = src_module_name
        self._test_module_name = test_module_name
        self._ignore = ignore

    async def test(self) -> AsyncIterable[str]:
        expected_test_class_name = f"Test{self._src_class.__name__}"

        if expected_test_class_name in self._test_classes:
            if self._ignore is TestKnownToBeMissing:
                yield f"The source class {self._src_class.__module__}.{self._src_class.__name__} has a matching test class at {self._test_classes[expected_test_class_name].__module__}.{self._test_classes[expected_test_class_name].__name__}, which was unexpectedly declared as known to be missing."
                return
            assert self._ignore is not TestKnownToBeMissing
            for error in self._test_members(
                self._test_classes[expected_test_class_name],
                self._ignore,  # type: ignore[arg-type]
            ):
                yield error
            return

        if self._ignore is TestKnownToBeMissing:
            return

        yield f"Failed to find the test class {self._test_module_name}.{expected_test_class_name} for the source class {self._src_module_name}.{self._src_class.__name__}."

    _EXCLUDE_DUNDER_METHODS = (
        "__init__",
        "__new__",
        "__repr__",
        "__weakref__",
    )

    def _is_member(self, name: str, member: object) -> bool:
        if isfunction(member):
            # Include dunder methods such as __eq__.
            if (
                name.startswith("__")
                and name.endswith("__")
                and name not in self._EXCLUDE_DUNDER_METHODS
            ):
                return True
            # Skip private members.
            return not name.startswith("_")
        if isdatadescriptor(member):
            # Skip private members.
            return not name.startswith("_")
        return False

    def _test_members(
        self, test_class: type, ignore: _ModuleClassExistsIgnore
    ) -> Iterable[str]:
        src_base_members = [
            member
            for src_base_class in self._src_class.__bases__
            for name, member in getmembers(src_base_class)
            if self._is_member(name, member)
        ]
        for src_member_name, src_member in getmembers(self._src_class):
            if (
                self._is_member(src_member_name, src_member)
                and src_member not in src_base_members
            ):
                yield from self._test_member(
                    test_class,
                    src_member_name,
                    src_member,
                    ignore.get(src_member_name, None),
                )

    def _test_member(
        self,
        test_class: type,
        src_member_name: str,
        src_member: Callable[..., Any],
        ignore: _ModuleFunctionIgnore,
    ) -> Iterable[str]:
        expected_test_member_name = f"test_{src_member_name}"
        expected_test_member_name_prefix = f"{expected_test_member_name}_"
        test_members = [
            member
            for name, member in getmembers(test_class)
            if self._is_member(name, member)
            and name == expected_test_member_name
            or name.startswith(expected_test_member_name_prefix)
        ]
        if test_members:
            if ignore is TestKnownToBeMissing:
                formatted_test_members = ", ".join(
                    (f"{test_member.__name__}()" for test_member in test_members)
                )
                yield f"The source member {self._src_class.__module__}.{self._src_class.__name__}.{src_member_name}() has (a) matching test method(s) {formatted_test_members} in {test_class.__module__}.{test_class.__name__}, which was unexpectedly declared as known to be missing."
            return

        if ignore is TestKnownToBeMissing:
            return

        yield f"Failed to find a test method named {expected_test_member_name}() or any methods whose names start with `{expected_test_member_name_prefix}` in {self._test_module_name}.{test_class.__name__} for the source member {self._src_module_name}.{self._src_class.__name__}.{src_member_name}()."


class Test_ModuleCoverageTester:
    @pytest.mark.parametrize(
        ("errors_expected", "module", "ignore"),
        [
            (False, _module_private, TestKnownToBeMissing),
            (False, _module_private, {}),
            (True, module_with_test, TestKnownToBeMissing),
            (False, module_with_test, {}),
            (False, module_without_test, TestKnownToBeMissing),
            (True, module_without_test, {}),
        ],
    )
    async def test(
        self,
        errors_expected: bool,
        module: _Importable,
        ignore: _ModuleIgnore,
    ) -> None:
        src_module_path = Path(module.__file__)
        sut = _ModuleCoverageTester(
            src_module_path,
            src_module_path.parent / "test.py",
            ignore,
        )
        assert (len([error async for error in sut.test()]) > 0) is errors_expected


class Test_ModuleFunctionCoverageTester:
    @pytest.mark.parametrize(
        ("errors_expected", "module", "ignore"),
        [
            (True, module_function_with_test, TestKnownToBeMissing),
            (False, module_function_without_test, TestKnownToBeMissing),
            (False, module_function_with_test, {}),
            (True, module_function_without_test, {}),
        ],
    )
    async def test(
        self, errors_expected: bool, module: _Importable, ignore: _ModuleFunctionIgnore
    ) -> None:
        test_class = getattr(module, "TestSrc", None)
        sut = _ModuleFunctionCoverageTester(
            module.src,  # type: ignore[attr-defined]
            (test_class,) if test_class else (),
            module.__name__,
            module.__name__,
            ignore,
        )
        assert (len([error async for error in sut.test()]) > 0) is errors_expected


class Test_ModuleClassCoverageTester:
    @pytest.mark.parametrize(
        ("errors_expected", "module", "ignore"),
        [
            (True, module_class_with_test, TestKnownToBeMissing),
            (False, module_class_without_test, TestKnownToBeMissing),
            (False, module_class_with_test, {}),
            (True, module_class_without_test, {}),
            (
                True,
                module_class_function_with_test,
                {
                    "src": TestKnownToBeMissing,
                },
            ),
            (
                False,
                module_class_function_without_test,
                {
                    "src": TestKnownToBeMissing,
                },
            ),
            (False, module_class_function_with_test, {}),
            (True, module_class_function_without_test, {}),
        ],
    )
    async def test(
        self, errors_expected: bool, module: _Importable, ignore: _ModuleClassIgnore
    ) -> None:
        test_class = getattr(module, "TestSrc", None)
        sut = _ModuleClassCoverageTester(
            module.Src,  # type: ignore[attr-defined]
            (test_class,) if test_class else (),
            module.__name__,
            module.__name__,
            ignore,
        )
        assert (len([error async for error in sut.test()]) > 0) is errors_expected
