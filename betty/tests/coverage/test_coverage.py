from __future__ import annotations

from _ast import Constant, Expr
from ast import iter_child_nodes, parse
from collections.abc import Callable, Iterable, Mapping, Sequence
from enum import Enum
from importlib import import_module
from inspect import getmembers, isclass, isdatadescriptor, isfunction
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Protocol, cast

import pytest

from betty.data import Data
from betty.dirs import root_directory
from betty.html.attributes import Attributes
from betty.plugin import PluginDefinition
from betty.plugin.cls import Plugin
from betty.tests.coverage.fixtures import (
    _module_private,
    module_class_function_with_test,
    module_class_function_without_test,
    module_class_with_test,
    module_class_without_test,
    module_function_with_test,
    module_function_without_test,
    module_with_test,
    module_without_test,
)

if TYPE_CHECKING:
    from betty.typing import Intersection


class MissingReason(Enum):
    """
    Reasons why test coverage is missing.
    """

    DEVELOPMENT = "This testable is for Betty development purposes only"
    ABSTRACT = "This testable is abstract"
    INTERNAL = "This testable is internal to Betty itself"
    SHOULD_BE_COVERED = "This testable should be covered by a test but isn't yet"
    STATIC_CONTENT_ONLY = "This testable has no testable components"
    COVERED_ELSEWHERE = "This testable is covered by another test"
    DATACLASS = "This testable is inherited from @dataclass"
    ENUM = "This testable is inherited from Enum"
    TYPED_DICT = "This testable is inherited from TypedDict"
    PROTOCOL = "This testable is a Protocol"
    INHERITED = "This testable is inherited"


type _ModuleFunctionExistsIgnore = None
type _ModuleFunctionIgnore = _ModuleFunctionExistsIgnore | MissingReason
type _ModuleClassExistsIgnore = Mapping[str, _ModuleFunctionIgnore]
type _ModuleClassIgnore = _ModuleClassExistsIgnore | MissingReason
type _ModuleMemberIgnore = _ModuleFunctionIgnore | _ModuleClassIgnore
type _ModuleExistsIgnore = Mapping[str, _ModuleMemberIgnore]
type _ModuleIgnore = _ModuleExistsIgnore | MissingReason

# Keys are paths to module files with ignore rules. These paths area relative to the project root directory.
# This baseline MUST NOT be extended. It SHOULD decrease in size as more coverage is added to Betty over time.
_BASELINE: Mapping[str, _ModuleIgnore] = {
    "betty/__init__.py": MissingReason.SHOULD_BE_COVERED,
    "betty/app/__init__.py": {
        "App": {
            "shutdown": MissingReason.COVERED_ELSEWHERE,
        }
    },
    "betty/assertions/plugin.py": {
        "assert_plugin": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/assertions/record.py": {
        "Field": MissingReason.DATACLASS,
    },
    "betty/asset.py": {
        "AssetError": MissingReason.ABSTRACT,
        "AssetRepository": MissingReason.ABSTRACT,
    },
    "betty/asset_directories/builtin.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/asset_directories/http_api_doc.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/asset_directories/maps.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/asset_directories/raspberry_mint.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/asset_directories/trees.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/asset_directories/project.py": MissingReason.COVERED_ELSEWHERE,
    "betty/asset_directories/webpack.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/asset_directories/wiki.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/asyncio.py": {
        "ReAwaitable": MissingReason.ABSTRACT,
    },
    "betty/attr.py": {
        "Attr": {},
    },
    "betty/attrs/common.py": {
        "CommonAttr": MissingReason.ABSTRACT,
    },
    "betty/attrs/date.py": {
        "HasAnyDate": {
            "has_any_date_linked_data_contexts": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/attrs/privacy.py": {
        "PrivacyAttr": {
            "linked_data_schema_for": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/cache.py": {
        "Cache": MissingReason.ABSTRACT,
        "CacheItem": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/cache/_base.py": MissingReason.COVERED_ELSEWHERE,
    "betty/commands/dev_profile_demo.py": MissingReason.DEVELOPMENT,
    "betty/console/__init__.py": {
        "SystemExitCode": MissingReason.ENUM,
    },
    "betty/console/command.py": {
        "Command": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/console/project.py": {
        "ConfigurationFileNotFound": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/concurrent.py": {
        "ThreadSafeLock": {
            "release": MissingReason.SHOULD_BE_COVERED,
        },
        "Lock": {
            "__aexit__": MissingReason.COVERED_ELSEWHERE,
            "acquire": MissingReason.ABSTRACT,
            "release": MissingReason.ABSTRACT,
        },
        "RateLimiter": {
            "__aenter__": MissingReason.SHOULD_BE_COVERED,
            "__aexit__": MissingReason.SHOULD_BE_COVERED,
        },
        "Semaphore": {
            "__aexit__": MissingReason.COVERED_ELSEWHERE,
            "acquire": MissingReason.ABSTRACT,
            "release": MissingReason.ABSTRACT,
        },
    },
    "betty/content_builder.py": {
        "ContentBuilder": MissingReason.ABSTRACT,
        "ContentBuilderDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "ContentBuilderManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/content_builders/box.py": {
        "BoxData": {
            "min_height": MissingReason.INHERITED,
            "max_height": MissingReason.INHERITED,
            "height": MissingReason.INHERITED,
            "min_width": MissingReason.INHERITED,
            "max_width": MissingReason.INHERITED,
            "width": MissingReason.INHERITED,
        },
    },
    "betty/content_builders/render.py": {
        "RenderData": {
            "media_type": MissingReason.INHERITED,
        },
    },
    "betty/content_builders/template.py": {
        "Template": {
            "build_template": MissingReason.ABSTRACT,
        },
    },
    "betty/contextlib.py": {
        "SynchronizedContextManager": {
            "__enter__": MissingReason.SHOULD_BE_COVERED,
            "__exit__": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/css_resources/webpack.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/service.py": {
        "Service": MissingReason.DATACLASS,
        "ServiceAlreadyInitialized": MissingReason.STATIC_CONTENT_ONLY,
        "ServiceError": MissingReason.ABSTRACT,
        "ServiceNotYetInitialized": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/services/plugin/__init__.py": {
        "PluginServiceManager": {
            "new_service": MissingReason.ABSTRACT,
        },
    },
    "betty/services/plugin/collection/__init__.py": {
        "CollectionPluginServiceManager": {
            "new_service_item": MissingReason.ABSTRACT,
        },
    },
    "betty/data.py": {
        "Data": MissingReason.ABSTRACT,
    },
    "betty/datas/aggregate/__init__.py": {
        "AggregateDefinition": MissingReason.ABSTRACT,
    },
    "betty/datas/aggregate/collection/__init__.py": {
        "CollectionDefinition": MissingReason.ABSTRACT,
    },
    "betty/datas/aggregate/record/__init__.py": {
        "PortableRecord": MissingReason.ABSTRACT,
        "RecordPorter": MissingReason.ABSTRACT,
    },
    "betty/datas/date.py": {
        "AnyDateDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/datas/plugin_definition.py": {
        "PluginDefinitionData": {
            "new_plugin": MissingReason.ABSTRACT,
        },
    },
    "betty/datas/plugin_manufacturer_sequence.py": {
        "PluginManufacturerSequenceDefinition": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/date.py": {
        "DateRange": {
            "end": MissingReason.INHERITED,
            "end_is_boundary": MissingReason.INHERITED,
            "start": MissingReason.INHERITED,
            "start_is_boundary": MissingReason.INHERITED,
        },
        "IncompleteDateError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/deriver.py": {"Derivation": MissingReason.ENUM},
    "betty/dirs.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/error.py": {
        "FileNotFound": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/exception.py": {
        "HumanFacingException": {
            "indicators": MissingReason.COVERED_ELSEWHERE,
        },
    },
    "betty/factory.py": {
        "DataManufacturable": MissingReason.ABSTRACT,
        "FactoryError": MissingReason.ABSTRACT,
        "Manufacturable": MissingReason.ABSTRACT,
        "UnsupportedTarget": MissingReason.ABSTRACT,
    },
    "betty/functools.py": {
        "Result": {
            "result": MissingReason.COVERED_ELSEWHERE,
        }
    },
    "betty/genders/man.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/genders/non_binary.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/genders/unknown.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/genders/woman.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/gramps.py": {
        "GrampsEntityReference": MissingReason.SHOULD_BE_COVERED,
        "GrampsEntityType": MissingReason.ENUM,
        "GrampsError": MissingReason.STATIC_CONTENT_ONLY,
        "GrampsFileNotFound": MissingReason.STATIC_CONTENT_ONLY,
        "LoaderUsedAlready": MissingReason.STATIC_CONTENT_ONLY,
        "XPathError": MissingReason.STATIC_CONTENT_ONLY,
        "UserFacingGrampsError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/html/attributes.py": {
        "Attributes": {
            attr_name: MissingReason.STATIC_CONTENT_ONLY
            for attr_name, _ in getmembers(Attributes)
            if attr_name.startswith("html_")
        },
    },
    "betty/http_client/rate_limit.py": {
        "RateLimitDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/indicator/__init__.py": {
        "Indicator": MissingReason.ABSTRACT,
    },
    "betty/indicator/selector.py": {
        "Indicator": MissingReason.ABSTRACT,
        "Selector": MissingReason.ABSTRACT,
    },
    "betty/jinja/__init__.py": {
        "context_document": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/jinja/filter.py": {
        "JinjaFilter": MissingReason.STATIC_CONTENT_ONLY,
        "JinjaFilterDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "JinjaFilterManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/jinja/test.py": {
        "JinjaTest": MissingReason.STATIC_CONTENT_ONLY,
        "JinjaTestDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "JinjaTestManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/job/__init__.py": {
        "Job": {
            "do": MissingReason.ABSTRACT,
        },
    },
    "betty/job/executor/__init__.py": {
        "Executor": MissingReason.ABSTRACT,
    },
    "betty/job/scheduler/__init__.py": {
        "Cancelled": MissingReason.STATIC_CONTENT_ONLY,
        "Closed": MissingReason.STATIC_CONTENT_ONLY,
        "Completed": MissingReason.STATIC_CONTENT_ONLY,
        "Released": MissingReason.STATIC_CONTENT_ONLY,
        "Scheduler": MissingReason.ABSTRACT,
    },
    "betty/jobs/generate_logo.py": {
        "GenerateLogo": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/jobs/no_op.py": {
        "NoOpJob": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/jobs/raise_exception.py": {
        "RaiseException": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/jobs/sleep.py": {
        "Sleep": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/js_resources/webpack_entry_point_loader.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/json_schema.py": {
        "Schema": {
            "validate": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/json_schemas/json_ld.py": MissingReason.SHOULD_BE_COVERED,
    "betty/life_cycle/__init__.py": {
        "AlreadyBootstrapped": MissingReason.STATIC_CONTENT_ONLY,
        "AlreadyShutDown": MissingReason.STATIC_CONTENT_ONLY,
        "LifeCycleError": MissingReason.STATIC_CONTENT_ONLY,
        "NotYetBootstrapped": MissingReason.STATIC_CONTENT_ONLY,
        "ShutdownerKwargs": MissingReason.TYPED_DICT,
    },
    "betty/link.py": {
        "Link": MissingReason.ABSTRACT,
    },
    "betty/links/betty_documentation.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/links/betty_github.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/links/http_api_doc.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/linked_data.py": {
        "dump_context": MissingReason.SHOULD_BE_COVERED,
        "dump_link": MissingReason.SHOULD_BE_COVERED,
        "dump_schema": MissingReason.SHOULD_BE_COVERED,
        "JsonLdObject": MissingReason.SHOULD_BE_COVERED,
        "LinkedDataDumpable": MissingReason.ABSTRACT,
        "LinkedDataDumpableWithSchema": MissingReason.ABSTRACT,
        "LinkedDataDumpableWithSchemaJsonLdObject": MissingReason.SHOULD_BE_COVERED,
        "LinkedDataDumper": MissingReason.ABSTRACT,
    },
    "betty/load.py": {
        "load": MissingReason.SHOULD_BE_COVERED,
        "Loader": MissingReason.ABSTRACT,
        "LoaderDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "LoaderManufacturer": MissingReason.STATIC_CONTENT_ONLY,
        "Enricher": MissingReason.ABSTRACT,
        "EnricherDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "EnricherManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/loaders/gramps.py": {
        "FamilyTree": {
            "event_types": MissingReason.INHERITED,
            "file": MissingReason.INHERITED,
            "name": MissingReason.INHERITED,
            "place_types": MissingReason.INHERITED,
            "roles": MissingReason.INHERITED,
        },
    },
    "betty/locale/__init__.py": {
        "Localized": MissingReason.ABSTRACT,
    },
    "betty/locale/babel.py": {
        "run_babel": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/locale/error.py": {
        "LocaleError": MissingReason.ABSTRACT,
    },
    "betty/locale/translation.py": {
        "AssetTranslationRepository": {
            "bootstrap": MissingReason.COVERED_ELSEWHERE,
        },
        "TranslationRepository": MissingReason.ABSTRACT,
        "new_translation": MissingReason.SHOULD_BE_COVERED,
        "update_translations": MissingReason.SHOULD_BE_COVERED,
        "update_app_translations": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/locale/localizable/__init__.py": {
        "CountableLocalizable": {
            "count": MissingReason.ABSTRACT,
        },
        "format": MissingReason.SHOULD_BE_COVERED,
        "Localizable": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/locale/localizable/error.py": {
        "InvalidPluralTag": MissingReason.STATIC_CONTENT_ONLY,
        "MissingPluralPlaceholder": MissingReason.STATIC_CONTENT_ONLY,
        "MissingPluralTag": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/locale/localizable/gettext.py": {
        "gettext": MissingReason.SHOULD_BE_COVERED,
        "ngettext": MissingReason.SHOULD_BE_COVERED,
        "npgettext": MissingReason.SHOULD_BE_COVERED,
        "pgettext": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/locale/localizable/markup.py": {
        "LocalizableSequence": MissingReason.ABSTRACT,
    },
    "betty/machine_name.py": {
        "MachineName": {
            "persistent": MissingReason.COVERED_ELSEWHERE,
        },
    },
    "betty/media_type.py": {
        "InvalidMediaType": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/media_types/html.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/media_types/jinja.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/media_types/json.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/media_types/json_ld.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/media_types/pdf.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/media_types/plain_text.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/media_types/svg.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/media_types/yaml.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/collection/__init__.py": {
        "MutableCollection": MissingReason.ABSTRACT,
    },
    "betty/collection/keyed/__init__.py": {
        "KeyedCollection": MissingReason.ABSTRACT,
        "MutableKeyedCollection": MissingReason.ABSTRACT,
    },
    "betty/collection/mapping/__init__.py": {
        "MutableResolvedMapping": MissingReason.ABSTRACT,
        "ResolvedMapping": MissingReason.ABSTRACT,
    },
    "betty/collection/sequence/__init__.py": {
        "MutableResolvedSequence": MissingReason.ABSTRACT,
    },
    "betty/copyright_notice.py": {
        "CopyrightNotice": MissingReason.STATIC_CONTENT_ONLY,
        "CopyrightNoticeDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "CopyrightNoticeManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/enrichers/privatizer.py": {
        "Privatizer": {
            "enrich": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/enrichers/wiki.py": {
        "WikiData": {
            "populate_images": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/entities/event.py": {
        "Event": {
            "has_any_date_linked_data_contexts": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/entity/__init__.py": {
        "Entity": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/entity/association.py": {
        "BidirectionalToOne": {
            "__set__": MissingReason.COVERED_ELSEWHERE,
        },
        "BidirectionalToZeroOrOne": {
            "__set__": MissingReason.COVERED_ELSEWHERE,
        },
        "resolve": MissingReason.SHOULD_BE_COVERED,
        "ToManyResolver": MissingReason.ABSTRACT,
        "ToOneResolver": MissingReason.ABSTRACT,
        "ToZeroOrOneResolver": MissingReason.ABSTRACT,
    },
    "betty/entity/collection/__init__.py": {
        "EntityCollection": MissingReason.ABSTRACT,
    },
    "betty/event_type.py": {
        "EventType": MissingReason.STATIC_CONTENT_ONLY,
        "EventTypeManufacturer": MissingReason.INHERITED,
        "ShouldExistEventType": MissingReason.ABSTRACT,
    },
    "betty/license.py": {
        "License": MissingReason.STATIC_CONTENT_ONLY,
        "LicenseDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "LicenseManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/gender.py": {
        "Gender": MissingReason.STATIC_CONTENT_ONLY,
        "GenderDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "GenderManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/npm.py": {
        "npm": MissingReason.SHOULD_BE_COVERED,
        "NpmUnavailable": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/path.py": MissingReason.SHOULD_BE_COVERED,
    "betty/multiprocessing.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_type.py": {
        "PlaceType": MissingReason.STATIC_CONTENT_ONLY,
        "PlaceTypeDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "PlaceTypeManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/place_types/borough.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/building.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/cemetery.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/city.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/country.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/county.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/department.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/district.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/farm.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/hamlet.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/locality.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/municipality.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/neighborhood.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/number.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/parish.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/province.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/region.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/state.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/street.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/town.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/unknown.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/place_types/village.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugin/cls.py": {
        "Plugin": MissingReason.ABSTRACT,
    },
    "betty/plugin/error.py": {
        "PluginError": MissingReason.ABSTRACT,
    },
    "betty/plugin/factory.py": {
        "PluginManufacturerDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "PluginManufacturerError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/plugin/discovery.py": {
        "PluginDiscovererCollection": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/plugin/ordered.py": {
        "OrderedPluginClsDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/portable/__init__.py": {
        "Portable": MissingReason.ABSTRACT,
        "Porter": MissingReason.ABSTRACT,
    },
    "betty/portable/error.py": {
        "NotPortable": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/role.py": {
        "Role": MissingReason.STATIC_CONTENT_ONLY,
        "RoleDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "RoleManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/roles/attendee.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/roles/beneficiary.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/roles/celebrant.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/roles/informant.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/roles/organizer.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/roles/speaker.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/roles/subject.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/roles/unknown.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/roles/witness.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/privacy/__init__.py": {
        "Privacy": MissingReason.ENUM,
    },
    "betty/privacy/privatizer.py": {
        "Privatizer": {
            "has_expired": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/progress.py": {
        "Progress": MissingReason.ABSTRACT,
    },
    "betty/event_types/adoption.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/baptism.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/bar_mitzvah.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/bat_mitzvah.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/birth.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/burial.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/conference.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/confirmation.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/correspondence.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/cremation.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/divorce.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/divorce_announcement.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/emigration.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/engagement.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/funeral.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/immigration.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/marriage.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/marriage_announcement.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/missing.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/occupation.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/residence.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/retirement.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/unknown.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/event_types/will.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/extension.py": {
        "Extension": MissingReason.SHOULD_BE_COVERED,
        "ExtensionDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "ExtensionManufacturer": MissingReason.INHERITED,
        "ExtensionError": MissingReason.STATIC_CONTENT_ONLY,
        "ExtensionTypeError": MissingReason.STATIC_CONTENT_ONLY,
        "ExtensionTypeInvalidError": MissingReason.SHOULD_BE_COVERED,
        "Theme": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/extensions/http_api_doc.py": {
        "HttpApiDoc": {
            "webpack_entry_point_cache_keys": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/extensions/maps.py": {
        "Maps": {
            "webpack_entry_point_cache_keys": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/extensions/raspberry_mint/__init__.py": {
        "Breakpoint": MissingReason.ENUM,
        "ColorStyle": MissingReason.ENUM,
        "JustifyContent": MissingReason.ENUM,
        "RaspberryMint": {
            "webpack_entry_point_cache_keys": MissingReason.STATIC_CONTENT_ONLY,
        },
        "Region": {
            "name": MissingReason.INHERITED,
            "value": MissingReason.INHERITED,
        },
    },
    "betty/extensions/trees.py": {
        "Trees": {
            "webpack_entry_point_cache_keys": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/extensions/spdx.py": {
        "Spdx": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/extensions/webpack/build.py": {
        "EntryPointProvider": MissingReason.ABSTRACT,
        "webpack_build_id": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/project/__init__.py": {
        "ProjectData": {
            "copyright_notice": MissingReason.INHERITED,
            "license": MissingReason.INHERITED,
        },
    },
    "betty/project/generate.py": {
        "Generator": MissingReason.ABSTRACT,
    },
    "betty/prop.py": {
        "Prop": {
            "__set_name__": MissingReason.COVERED_ELSEWHERE,
            "get": MissingReason.ABSTRACT,
        },
        "PropDefinition": MissingReason.DATACLASS,
    },
    "betty/render.py": {
        "Renderer": MissingReason.ABSTRACT,
        "RendererDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/requirement.py": {
        "UnmetRequirement": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/document.py": {
        "DocumentProvider": MissingReason.STATIC_CONTENT_ONLY,
        "DocumentProviderDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "DocumentProviderManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/sample.py": {
        "Samplable": MissingReason.ABSTRACT,
        "SampleNotFound": MissingReason.STATIC_CONTENT_ONLY,
        "Size": MissingReason.ENUM,
    },
    "betty/serialize.py": {
        "Serializer": MissingReason.ABSTRACT,
        "SerializerDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "SerializationError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/server.py": {
        "Server": MissingReason.ABSTRACT,
        "ServerDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "ServerNotStarted": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/servers/builtin.py": {
        "BuiltinServer": {
            "public_url": MissingReason.COVERED_ELSEWHERE,
            "stop": MissingReason.COVERED_ELSEWHERE,
        },
    },
    "betty/servers/demo.py": {
        "DemoServer": {
            "public_url": MissingReason.SHOULD_BE_COVERED,
            "start": MissingReason.SHOULD_BE_COVERED,
            "stop": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/servers/documentation.py": {
        "DocumentationServer": {
            "public_url": MissingReason.SHOULD_BE_COVERED,
            "start": MissingReason.SHOULD_BE_COVERED,
            "stop": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/servers/project_builtin.py": {
        "ProjectBuiltinServer": {
            "public_url": MissingReason.COVERED_ELSEWHERE,
            "start": MissingReason.COVERED_ELSEWHERE,
            "stop": MissingReason.COVERED_ELSEWHERE,
        },
    },
    "betty/sphinx/extension/betty.py": MissingReason.COVERED_ELSEWHERE,
    "betty/subprocess.py": {
        "FileNotFound": MissingReason.STATIC_CONTENT_ONLY,
        "SubprocessError": MissingReason.STATIC_CONTENT_ONLY,
    },
    # We do not test our test utilities.
    **{
        str(path): MissingReason.INTERNAL
        for path in (Path("betty") / "test_utils").rglob("**/*.py")
    },
    "betty/typing.py": {
        "Intersection": MissingReason.STATIC_CONTENT_ONLY,
        "Void": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/url/__init__.py": {
        "GenerationError": MissingReason.ABSTRACT,
        "LocalizedUrlGenerator": MissingReason.ABSTRACT,
        "StaticUrlGenerator": MissingReason.ABSTRACT,
        "UnsupportedMediaType": MissingReason.SHOULD_BE_COVERED,
        "UnsupportedResource": MissingReason.STATIC_CONTENT_ONLY,
        "UrlGenerator": MissingReason.ABSTRACT,
    },
    "betty/user/__init__.py": {
        "User": MissingReason.ABSTRACT,
        "UserError": MissingReason.ABSTRACT,
        "UserFacing": MissingReason.STATIC_CONTENT_ONLY,
        "UserTimeoutError": MissingReason.STATIC_CONTENT_ONLY,
        "Verbosity": MissingReason.ENUM,
    },
    "betty/user/logging.py": {
        "UserHandler": {
            "start": MissingReason.COVERED_ELSEWHERE,
            "stop": MissingReason.COVERED_ELSEWHERE,
        },
    },
    "betty/warnings.py": {
        "BettyDeprecationWarning": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/wiki/__init__.py": {
        "NotAPageError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/wiki/client.py": {
        "ClientError": MissingReason.STATIC_CONTENT_ONLY,
        "Image": MissingReason.DATACLASS,
        "Summary": {
            "__eq__": MissingReason.DATACLASS,
            "__delattr__": MissingReason.DATACLASS,
            "__hash__": MissingReason.DATACLASS,
            "__replace__": MissingReason.DATACLASS,
            "__setattr__": MissingReason.DATACLASS,
        },
    },
}


class TestCoverage:
    async def test(self, subtests: pytest.Subtests) -> None:
        errors = await CoverageTester().test()
        for file in sorted(errors):
            for error in sorted(errors[file]):
                with subtests.test():
                    raise AssertionError(error)


def _module_path_to_name(module: Path) -> str:
    relative_module_path = module.relative_to(root_directory)
    module_name_parts = relative_module_path.parent.parts
    if relative_module_path.name != "__init__.py":
        module_name_parts = (*module_name_parts, relative_module_path.name[:-3])
    return ".".join(module_name_parts)


class CoverageTester:
    def __init__(self):
        self._ignore_src_module_paths = {
            Path(module_file).resolve(): members
            for module_file, members in _BASELINE.items()
        }

    async def test(self) -> Mapping[Path, Iterable[str]]:
        return {
            file: self._test_python_file(file)
            for directory, _, file_names in (root_directory / "betty").resolve().walk()
            for file_name in file_names
            if file_name.endswith(".py")
            if (file := directory / file_name)
        }

    def _test_python_file(self, file: Path, /) -> Iterable[str]:
        if root_directory / "betty" / "tests" in file.parents:
            if file.name.startswith("test_"):
                return self._test_python_test_file(file)
            return ()
        return self._test_python_src_file(file)

    def _test_python_src_file(self, file: Path, /) -> Iterable[str]:
        if file.name == "__init__.py":
            expected_test_module_path = (
                root_directory
                / "betty"
                / "tests"
                / file.relative_to(root_directory / "betty").parent.parent
                / f"test_{file.parent.name}.py"
            )
        else:
            expected_test_module_path = (
                root_directory
                / "betty"
                / "tests"
                / file.relative_to(root_directory / "betty").parent
                / f"test_{file.name}"
            )
        return _ModuleCoverageTester(
            file,
            expected_test_module_path,
            self._ignore_src_module_paths.get(file, {}),
        ).test()

    def _test_python_test_file(self, file: Path, /) -> Iterable[str]:
        expected_src_module_path = (
            root_directory
            / "betty"
            / file.relative_to(root_directory / "betty" / "tests").parent
            / file.name[5:]
        )
        if expected_src_module_path in self._ignore_src_module_paths and isinstance(
            self._ignore_src_module_paths[expected_src_module_path], MissingReason
        ):
            yield f"{expected_src_module_path} has a matching test file at {file}, which was unexpectedly declared as known to be missing."


class _Importable(Protocol):
    __file__: str
    __name__: str


class _ModuleCoverageTester:
    def __init__(self, src_module: Path, test_module: Path, ignore: _ModuleIgnore, /):
        self._src_module = src_module
        self._test_module = test_module
        self._ignore = ignore
        self._src_module_name, self._src_functions, self._src_classes = (
            self._get_module_data(self._src_module)
        )

    def test(self) -> Iterable[str]:
        # Skip private modules.
        if True in (x.startswith("_") for x in self._src_module_name.split(".")):
            return

        if self._test_module.exists() and not isinstance(self._ignore, MissingReason):
            test_module_name, test_functions, test_classes = self._get_module_data(
                self._test_module
            )
            for src_function in self._src_functions:
                yield from _ModuleFunctionCoverageTester(
                    src_function,
                    test_functions,
                    self._src_module_name,
                    test_module_name,
                    cast(
                        "_ModuleFunctionIgnore",
                        self._ignore.get(src_function.__name__, None),
                    ),
                ).test()

            for src_class in self._src_classes:
                yield from _ModuleClassCoverageTester(
                    src_class,
                    test_classes,
                    self._src_module_name,
                    test_module_name,
                    cast(
                        "_ModuleClassIgnore",
                        self._ignore.get(src_class.__name__, {}),
                    ),
                ).test()
            return

        if isinstance(self._ignore, MissingReason):
            return

        if self._test_python_file_contains_docstring_only(self._src_module):
            return

        yield f"{self._src_module} does not have a matching test file. Expected {self._test_module} to exist."

    def _test_python_file_contains_docstring_only(self, file: Path, /) -> bool:
        with open(file, encoding="utf-8") as f:
            python = f.read()
        for child in iter_child_nodes(parse(python, file)):
            if not isinstance(child, Expr):
                return False
            if not isinstance(child.value, Constant):
                return False
        return True

    def _get_module_data(
        self, module: Path, /
    ) -> tuple[
        str,
        Sequence[Intersection[_Importable, Callable[..., Any]]],
        Sequence[Intersection[_Importable, type]],
    ]:
        module_name = _module_path_to_name(module)
        return (
            module_name,
            sorted(
                self._get_members(module_name, isfunction),
                key=lambda member: member.__name__,
            ),  # ty:ignore[no-matching-overload]
            sorted(
                self._get_members(module_name, isclass),
                key=lambda member: member.__name__,
            ),  # ty:ignore[no-matching-overload]
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
            imported_member = cast(_Importable, getattr(module, member_name))
            if getattr(imported_member, "__module__", None) != module_name:
                continue

            yield imported_member


class _ModuleFunctionCoverageTester:
    def __init__(
        self,
        src_function: Intersection[_Importable, Callable[..., Any]],
        test_functions: Sequence[Intersection[_Importable, Callable[..., Any]]],
        src_module_name: str,
        test_module_name: str,
        ignore: _ModuleFunctionIgnore,
    ):
        self._src_function = src_function
        self._test_functions = {
            test_function.__name__: test_function for test_function in test_functions
        }
        self._src_module_name = src_module_name
        self._test_module_name = test_module_name
        self._ignore = ignore

    def test(self) -> Iterable[str]:
        expected_test_member_name = f"test_{self._src_function.__name__}"
        expected_test_member_name_prefix = f"{expected_test_member_name}__"
        test_functions = [
            test_function
            for test_function_name, test_function in self._test_functions.items()
            if self._is_member(test_function_name)
            and test_function_name == expected_test_member_name
            or test_function_name.startswith(expected_test_member_name_prefix)
        ]
        if test_functions:
            if isinstance(self._ignore, MissingReason):
                formatted_test_members = ", ".join(
                    f"{test_function.__name__}()" for test_function in test_functions
                )
                yield f"The source function {self._src_function.__module__}.{self._src_function.__name__}() has (a) matching test function(s) {formatted_test_members} in {self._test_module_name}, which was unexpectedly declared as known to be missing."
            return

        if isinstance(self._ignore, MissingReason):
            return

        yield f"Failed to find a test function named {expected_test_member_name}() or any methods whose names start with `{expected_test_member_name_prefix}` in {self._test_module_name} for the source function {self._src_module_name}.{self._src_function.__name__}()."

    def _is_member(self, name: str) -> bool:
        # Skip private members.
        return not name.startswith("_")


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

    def test(self) -> Iterable[str]:
        expected_test_class_name = (
            f"Test{self._src_class.__name__[0].upper()}{self._src_class.__name__[1:]}"
        )

        if expected_test_class_name in self._test_classes:
            if isinstance(self._ignore, MissingReason):
                yield f"The source class {self._src_class.__module__}.{self._src_class.__name__} has a matching test class at {self._test_classes[expected_test_class_name].__module__}.{self._test_classes[expected_test_class_name].__name__}, which was unexpectedly declared as known to be missing."
                return
            assert not isinstance(self._ignore, MissingReason)
            yield from self._test_members(
                self._test_classes[expected_test_class_name], self._ignore
            )
            return

        if isinstance(self._ignore, MissingReason):
            return

        yield f"Failed to find the test class {self._test_module_name}.{expected_test_class_name} for the source class {self._src_module_name}.{self._src_class.__name__}."

    _exclude_dunder_methods: Final[Sequence[str]] = (
        "__annotate_func__",
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
                and name not in self._exclude_dunder_methods
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
        expected_test_member_name_prefix = f"{expected_test_member_name}__"
        test_members = [
            member
            for name, member in getmembers(test_class)
            if self._is_member(name, member)
            and name == expected_test_member_name
            or name.startswith(expected_test_member_name_prefix)
        ]
        if test_members:
            if isinstance(ignore, MissingReason):
                formatted_test_members = ", ".join(
                    f"{test_member.__name__}()" for test_member in test_members
                )
                yield f"The source member {self._src_class.__module__}.{self._src_class.__name__}.{src_member_name}() has (a) matching test method(s) {formatted_test_members} in {test_class.__module__}.{test_class.__name__}, which was unexpectedly declared as known to be missing."
            return

        for ignored_class, ignored_member_name in (
            (Data, "data"),
            (Plugin, "plugin"),
            (PluginDefinition, "type"),
        ):
            assert hasattr(ignored_class, ignored_member_name)
            if (
                issubclass(self._src_class, ignored_class)
                and src_member_name == ignored_member_name
            ):
                if ignore is not None:
                    yield f"The source member {self._src_class.__module__}.{self._src_class.__name__}.{src_member_name}() is ignored automatically, but was also unexpectedly declared as known to be missing."
                return

        if isinstance(ignore, MissingReason):
            return

        yield f"Failed to find a test method named {expected_test_member_name}() or any methods whose names start with `{expected_test_member_name_prefix}` in {self._test_module_name}.{test_class.__name__} for the source member {self._src_module_name}.{self._src_class.__name__}.{src_member_name}()."


class Test_ModuleCoverageTester:
    @pytest.mark.parametrize(
        ("errors_expected", "module", "ignore"),
        [
            (False, _module_private, MissingReason.SHOULD_BE_COVERED),
            (False, _module_private, {}),
            (False, module_with_test, {}),
            (False, module_without_test, MissingReason.SHOULD_BE_COVERED),
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
        assert (len(list(sut.test())) > 0) is errors_expected


class Test_ModuleFunctionCoverageTester:
    @pytest.mark.parametrize(
        ("errors_expected", "module", "ignore"),
        [
            (True, module_function_with_test, MissingReason.SHOULD_BE_COVERED),
            (False, module_function_without_test, MissingReason.SHOULD_BE_COVERED),
            (False, module_function_with_test, {}),
            (True, module_function_without_test, {}),
        ],
    )
    async def test(
        self, errors_expected: bool, module: _Importable, ignore: _ModuleFunctionIgnore
    ) -> None:
        test_function = cast(
            "Intersection[_Importable, Callable[..., Any]] | None",
            getattr(module, "test_src", None),
        )
        sut = _ModuleFunctionCoverageTester(
            module.src,  # ty:ignore[unresolved-attribute]
            () if test_function is None else (test_function,),
            module.__name__,
            module.__name__,
            ignore,
        )
        assert (len(list(sut.test())) > 0) is errors_expected


class Test_ModuleClassCoverageTester:
    @pytest.mark.parametrize(
        ("errors_expected", "module", "ignore"),
        [
            (True, module_class_with_test, MissingReason.SHOULD_BE_COVERED),
            (False, module_class_without_test, MissingReason.SHOULD_BE_COVERED),
            (False, module_class_with_test, {}),
            (True, module_class_without_test, {}),
            (
                True,
                module_class_function_with_test,
                {
                    "src": MissingReason.SHOULD_BE_COVERED,
                },
            ),
            (
                False,
                module_class_function_without_test,
                {
                    "src": MissingReason.SHOULD_BE_COVERED,
                },
            ),
            (False, module_class_function_with_test, {}),
            (True, module_class_function_without_test, {}),
        ],
    )
    async def test(
        self, errors_expected: bool, module: _Importable, ignore: _ModuleClassIgnore
    ) -> None:
        test_class = cast(type | None, getattr(module, "TestSrc", None))
        sut = _ModuleClassCoverageTester(
            module.Src,  # ty:ignore[unresolved-attribute]
            () if test_class is None else (test_class,),
            module.__name__,
            module.__name__,
            ignore,
        )
        assert (len(list(sut.test())) > 0) is errors_expected
