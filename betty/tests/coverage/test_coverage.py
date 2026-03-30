from __future__ import annotations

from _ast import Constant, Expr
from ast import iter_child_nodes, parse
from collections import defaultdict
from collections.abc import (
    AsyncIterable,
    Callable,
    Iterable,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)
from enum import Enum
from importlib import import_module
from inspect import getmembers, isclass, isdatadescriptor, isfunction
from os import walk
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast

import pytest

from betty.dirs import ROOT_DIRECTORY
from betty.html.attributes import Attributes
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
    "betty/asset.py": {
        "Asset": MissingReason.STATIC_CONTENT_ONLY,
        "AssetDefinition": {
            "type": MissingReason.INHERITED,
        },
        "AssetError": MissingReason.ABSTRACT,
        "AssetManufacturer": MissingReason.STATIC_CONTENT_ONLY,
        "AssetRepository": MissingReason.ABSTRACT,
    },
    "betty/assertion.py": {
        "Field": MissingReason.INTERNAL,
        "OptionalField": MissingReason.DATACLASS,
        "RequiredField": MissingReason.DATACLASS,
    },
    "betty/asyncio.py": {
        "ReAwaitable": MissingReason.ABSTRACT,
    },
    "betty/cache/__init__.py": {
        "Cache": MissingReason.ABSTRACT,
        "CacheItem": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/cache/_base.py": MissingReason.COVERED_ELSEWHERE,
    "betty/console/__init__.py": {
        "SystemExitCode": MissingReason.ENUM,
    },
    "betty/console/command.py": {
        "Command": MissingReason.SHOULD_BE_COVERED,
        "CommandDefinition": {
            "type": MissingReason.INHERITED,
        },
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
    "betty/content.py": {
        "Content": MissingReason.ABSTRACT,
        "ContentDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "ContentManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/contextlib.py": {
        "SynchronizedContextManager": {
            "__enter__": MissingReason.SHOULD_BE_COVERED,
            "__exit__": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/service/__init__.py": {
        "ServiceError": MissingReason.ABSTRACT,
    },
    "betty/service/provider.py": {
        "Service": MissingReason.DATACLASS,
        "ServiceAlreadyInitialized": MissingReason.STATIC_CONTENT_ONLY,
        "ServiceNotYetInitialized": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/service/factory.py": {
        "DataManufacturable": MissingReason.ABSTRACT,
        "Manufacturable": MissingReason.ABSTRACT,
    },
    "betty/service/plugin/service/__init__.py": {
        "PluginServiceManager": {
            "new_service": MissingReason.ABSTRACT,
        },
    },
    "betty/service/plugin/service/collection/__init__.py": {
        "CollectionPluginServiceManager": {
            "new_service_item": MissingReason.ABSTRACT,
        },
    },
    "betty/service/requirement/__init__.py": {
        "CallableRequirement": {
            "__get__": MissingReason.COVERED_ELSEWHERE,
        },
        "UnmetRequirement": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/data/__init__.py": {
        "Data": MissingReason.ABSTRACT,
    },
    "betty/data/aggregate/__init__.py": {
        "AggregateDefinition": MissingReason.ABSTRACT,
    },
    "betty/data/aggregate/collection/__init__.py": {
        "CollectionDefinition": MissingReason.ABSTRACT,
    },
    "betty/data/aggregate/record/__init__.py": {
        "PortableRecord": MissingReason.ABSTRACT,
        "RecordPorter": MissingReason.ABSTRACT,
    },
    "betty/data/aggregate/record/object/__init__.py": {
        "Attr": MissingReason.ABSTRACT,
    },
    "betty/data/indicator/__init__.py": {
        "Indicator": MissingReason.ABSTRACT,
    },
    "betty/data/indicator/selector.py": {
        "Indicator": MissingReason.ABSTRACT,
        "Selector": MissingReason.ABSTRACT,
    },
    "betty/date/__init__.py": {
        "IncompleteDateError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/demo/serve.py": {
        "DemoServer": {
            "public_url": MissingReason.SHOULD_BE_COVERED,
            "start": MissingReason.SHOULD_BE_COVERED,
            "stop": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/deriver.py": {"Derivation": MissingReason.ENUM},
    "betty/documentation.py": {
        "DocumentationServer": {
            "public_url": MissingReason.SHOULD_BE_COVERED,
            "start": MissingReason.SHOULD_BE_COVERED,
            "stop": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/dirs.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/error.py": {
        "FileNotFound": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/exception.py": {
        "HumanFacingException": {
            "indicators": MissingReason.COVERED_ELSEWHERE,
        },
    },
    "betty/functools.py": {
        "Result": {
            "result": MissingReason.COVERED_ELSEWHERE,
        }
    },
    "betty/gramps/error.py": MissingReason.SHOULD_BE_COVERED,
    "betty/gramps/loader.py": {
        "GrampsEntityReference": MissingReason.SHOULD_BE_COVERED,
        "GrampsEntityType": MissingReason.ENUM,
        "GrampsFileNotFound": MissingReason.STATIC_CONTENT_ONLY,
        "LoaderUsedAlready": MissingReason.STATIC_CONTENT_ONLY,
        "XPathError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/html/attributes.py": {
        "Attributes": {
            attr_name: MissingReason.STATIC_CONTENT_ONLY
            for attr_name, _ in getmembers(Attributes)
            if attr_name.startswith("html_")
        },
    },
    "betty/html/css.py": {
        "CssResourceDefinition": {
            "type": MissingReason.INHERITED,
        },
    },
    "betty/html/js.py": {
        "JsResourceDefinition": {
            "type": MissingReason.INHERITED,
        },
    },
    "betty/http_client/rate_limit.py": {
        "RateLimit": MissingReason.ABSTRACT,
        "RateLimitDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "RateLimitManufacturer": MissingReason.STATIC_CONTENT_ONLY,
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
    "betty/json/linked_data.py": {
        "dump_context": MissingReason.SHOULD_BE_COVERED,
        "dump_link": MissingReason.SHOULD_BE_COVERED,
        "dump_schema": MissingReason.SHOULD_BE_COVERED,
        "JsonLdObject": MissingReason.SHOULD_BE_COVERED,
        "JsonLdSchema": MissingReason.SHOULD_BE_COVERED,
        "LinkedDataDumpable": MissingReason.ABSTRACT,
        "LinkedDataDumpableWithSchema": MissingReason.ABSTRACT,
        "LinkedDataDumpableWithSchemaJsonLdObject": MissingReason.SHOULD_BE_COVERED,
        "LinkedDataDumper": MissingReason.ABSTRACT,
    },
    "betty/json/schema.py": {
        "FileBasedSchema": {
            "__init_subclass__": MissingReason.INHERITED,
        },
        "Schema": {
            "validate": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/life_cycle/__init__.py": {
        "AlreadyBootstrapped": MissingReason.STATIC_CONTENT_ONLY,
        "AlreadyShutDown": MissingReason.STATIC_CONTENT_ONLY,
        "LifeCycleError": MissingReason.STATIC_CONTENT_ONLY,
        "NotYetBootstrapped": MissingReason.STATIC_CONTENT_ONLY,
        "ShutdownerKwargs": MissingReason.TYPED_DICT,
    },
    "betty/link.py": {
        "Link": MissingReason.STATIC_CONTENT_ONLY,
        "LinkDefinition": {
            "type": MissingReason.INHERITED,
        },
        "LinkManufacturer": MissingReason.STATIC_CONTENT_ONLY,
        "LinkType": MissingReason.ABSTRACT,
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
        "update_universe_translations": MissingReason.SHOULD_BE_COVERED,
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
            "data": MissingReason.INHERITED,
        },
    },
    "betty/media_type/__init__.py": {
        "MediaType": {
            "data": MissingReason.INHERITED,
        },
        "InvalidMediaType": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/media_type/media_types.py": MissingReason.STATIC_CONTENT_ONLY,
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
    "betty/copyright_notice/__init__.py": {
        "CopyrightNotice": MissingReason.STATIC_CONTENT_ONLY,
        "CopyrightNoticeDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "CopyrightNoticeManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/copyright_notice/data.py": {
        "CopyrightNoticeDefinitionConfiguration": {
            "data": MissingReason.INHERITED,
        },
    },
    "betty/entity/__init__.py": {
        "Entity": MissingReason.SHOULD_BE_COVERED,
        "EntityDefinition": {
            "type": MissingReason.INHERITED,
        },
        "EntityReferenceCollectionSchema": MissingReason.STATIC_CONTENT_ONLY,
        "EntityReferenceSchema": MissingReason.STATIC_CONTENT_ONLY,
        "NonPersistentId": MissingReason.SHOULD_BE_COVERED,
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
    "betty/entity/has_date.py": {
        "HasDate": {
            "dated_linked_data_contexts": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/event_type/__init__.py": {
        "EventType": MissingReason.STATIC_CONTENT_ONLY,
        "EventTypeDefinition": {
            "type": MissingReason.INHERITED,
        },
        "EventTypeManufacturer": MissingReason.INHERITED,
        "ShouldExistEventType": MissingReason.ABSTRACT,
    },
    "betty/event_type/data.py": {
        "EventTypeDefinitionConfiguration": {
            "data": MissingReason.INHERITED,
        },
    },
    "betty/license/__init__.py": {
        "License": MissingReason.STATIC_CONTENT_ONLY,
        "LicenseDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "LicenseManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/license/data.py": {
        "LicenseDefinitionConfiguration": {
            "data": MissingReason.INHERITED,
        },
    },
    "betty/gender/__init__.py": {
        "Gender": MissingReason.STATIC_CONTENT_ONLY,
        "GenderDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "GenderManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/gender/data.py": {
        "GenderDefinitionConfiguration": {
            "data": MissingReason.INHERITED,
        },
    },
    "betty/npm.py": {
        "npm": MissingReason.SHOULD_BE_COVERED,
        "NpmUnavailable": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/path.py": MissingReason.SHOULD_BE_COVERED,
    "betty/multiprocessing.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/openapi.py": {
        "SpecificationSchema": {"__annotate_func__": MissingReason.DATACLASS},
    },
    "betty/place_type/__init__.py": {
        "PlaceType": MissingReason.STATIC_CONTENT_ONLY,
        "PlaceTypeDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "PlaceTypeManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/place_type/data.py": {
        "PlaceTypeDefinitionConfiguration": {
            "data": MissingReason.INHERITED,
        },
    },
    "betty/plugin/assertion.py": {
        "assert_plugin": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/plugin/cls.py": {
        "Plugin": MissingReason.ABSTRACT,
        "PluginClsDefinition": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/plugin/data/__init__.py": {
        "PluginDefinitionConfiguration": {"new_plugin": MissingReason.ABSTRACT},
    },
    "betty/plugin/error.py": {
        "PluginError": MissingReason.ABSTRACT,
    },
    "betty/plugin/discovery/__init__.py": {
        "PluginDiscovery": MissingReason.ABSTRACT,
    },
    "betty/plugin/ordered.py": {
        "OrderedPluginClsDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/plugins/asset/http_api_doc.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/asset/maps.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/asset/raspberry_mint.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/asset/trees.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/asset/project.py": MissingReason.COVERED_ELSEWHERE,
    "betty/plugins/asset/universe.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/asset/webpack.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/asset/wiki.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/command/about.py": {
        "About": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/command/clear_caches.py": {
        "ClearCaches": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/command/config.py": {
        "Config": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/command/demo.py": {
        "Demo": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/command/dev_profile_demo.py": MissingReason.DEVELOPMENT,
    "betty/plugins/command/dev_update_translations.py": {
        "DevUpdateTranslations": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/command/docs.py": {
        "Docs": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/command/asset_new_translation.py": {
        "AssetNewTranslation": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/command/asset_update_translations.py": {
        "AssetUpdateTranslations": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/command/generate.py": {
        "Generate": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/command/new.py": {
        "New": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/command/new_translation.py": {
        "NewTranslation": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/command/serve.py": {
        "Serve": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/command/update_translations.py": {
        "UpdateTranslations": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/content/box.py": {
        "Box": {
            "plugin": MissingReason.INHERITED,
        },
        "BoxConfiguration": {
            "min_height": MissingReason.INHERITED,
            "max_height": MissingReason.INHERITED,
            "height": MissingReason.INHERITED,
            "min_width": MissingReason.INHERITED,
            "max_width": MissingReason.INHERITED,
            "width": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/map.py": {
        "Map": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/map_attribution.py": {
        "MapAttribution": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/notes.py": {
        "Notes": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_citations.py": {
        "Citations": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_color_style.py": {
        "ColorStyle": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_columns.py": {
        "Columns": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_enclosees.py": {
        "Enclosees": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_entity_card.py": {
        "EntityCard": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_external_links.py": {
        "ExternalLinks": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_facts.py": {
        "Facts": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_families.py": {
        "Families": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_file_referees.py": {
        "FileReferees": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_incomplete_translation_warning.py": {
        "IncompleteTranslationWarning": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_media.py": {
        "Media": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_media_gallery.py": {
        "MediaGallery": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_presences.py": {
        "Presences": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_section.py": {
        "Section": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/raspberry_mint_timeline.py": {
        "Timeline": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/render.py": {
        "Render": {
            "plugin": MissingReason.INHERITED,
        },
        "RenderConfiguration": {
            "media_type": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/static.py": {
        "Static": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/template.py": {
        "Template": {
            "build_template": MissingReason.ABSTRACT,
        },
    },
    "betty/plugins/content/tree.py": {
        "Tree": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/content/wikipedia_summary.py": {
        "WikipediaSummary": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/copyright_notice/project_author.py": {
        "ProjectAuthor": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/copyright_notice/public_domain.py": {
        "PublicDomain": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/copyright_notice/streetmix.py": {
        "Streetmix": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/copyright_notice/wikipedia_contributors.py": {
        "WikipediaContributors": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/css_resource/webpack.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/document_provider/webpack/__init__.py": {
        "Webpack": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/enricher/deriver/__init__.py": {
        "Deriver": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/enricher/populate_links/__init__.py": {
        "PopulateLinks": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/enricher/privatizer/__init__.py": {
        "Privatizer": {
            "enrich": MissingReason.SHOULD_BE_COVERED,
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/enricher/wiki/__init__.py": {
        "Wiki": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/enricher/wiki/data.py": {
        "WikiConfiguration": {
            "populate_images": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/plugins/entity/citation.py": {
        "Citation": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/entity/enclosure.py": {
        "Enclosure": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/entity/event.py": {
        "Event": {
            "dated_linked_data_contexts": MissingReason.STATIC_CONTENT_ONLY,
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/entity/file.py": {
        "File": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/entity/file_reference.py": {
        "FileReference": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/entity/link.py": {
        "Link": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/entity/note.py": {
        "Note": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/entity/person.py": {
        "Person": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/entity/person_name.py": {
        "PersonName": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/entity/place.py": {
        "Place": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/entity/place_name.py": {
        "PlaceName": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/entity/presence.py": {
        "Presence": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/entity/source.py": {
        "Source": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/event_type/adoption.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/baptism.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/bar_mitzvah.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/bat_mitzvah.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/birth.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/burial.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/conference.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/confirmation.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/correspondence.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/cremation.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/death.py": {
        "Death": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/event_type/divorce.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/divorce_announcement.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/emigration.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/engagement.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/funeral.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/immigration.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/marriage.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/marriage_announcement.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/missing.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/occupation.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/residence.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/retirement.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/unknown.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/event_type/will.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/extension/demo/__init__.py": {
        "Demo": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/extension/http_api_doc/__init__.py": {
        "HttpApiDoc": {
            "plugin": MissingReason.INHERITED,
            "webpack_entry_point_cache_keys": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/plugins/extension/maps/__init__.py": {
        "Maps": {
            "plugin": MissingReason.INHERITED,
            "webpack_entry_point_cache_keys": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/plugins/extension/raspberry_mint/__init__.py": {
        "Breakpoint": MissingReason.ENUM,
        "ColorStyle": MissingReason.ENUM,
        "JustifyContent": MissingReason.ENUM,
        "RaspberryMint": {
            "plugin": MissingReason.INHERITED,
            "webpack_entry_point_cache_keys": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/plugins/extension/raspberry_mint/region.py": {
        "Region": {
            "name": MissingReason.INHERITED,
            "value": MissingReason.INHERITED,
        }
    },
    "betty/plugins/extension/trees/__init__.py": {
        "Trees": {
            "plugin": MissingReason.INHERITED,
            "webpack_entry_point_cache_keys": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/plugins/extension/spdx/__init__.py": {
        "Spdx": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/plugins/extension/webpack/__init__.py": {
        "Webpack": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/extension/webpack/build.py": {
        "EntryPointProvider": MissingReason.ABSTRACT,
        "webpack_build_id": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/plugins/extension/wiki/__init__.py": {
        "Wiki": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/gender/man.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/gender/non_binary.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/gender/unknown.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/gender/woman.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/jinja_filter/build_content.py": {
        "BuildContent": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/file.py": {
        "File": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/format_datetime_datetime.py": {
        "FormatDatetimeDatetime": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/format_degrees.py": {
        "FormatDegrees": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/html_lang.py": {
        "HtmlLang": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/image_resize_cover.py": {
        "ImageResizeCover": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/json_dump.py": {
        "JsonDump": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/json_load.py": {
        "JsonLoad": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/localize.py": {
        "Localize": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/negotiate_has_dates.py": {
        "NegotiateHasDates": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/select_has_dates.py": {
        "SelectHasDates": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/to_language_tag.py": {
        "ToLanguageTag": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/unique.py": {
        "Unique": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/url.py": {
        "Url": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_filter/webpack_entry_point_js.py": {
        "WebpackEntryPointJs": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_test/has_file_references.py": {
        "HasFileReferences": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_test/image_media_type_supported.py": {
        "ImageMediaTypeSupported": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_test/linked_data_dumpable.py": {
        "LinkedDataDumpable": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_test/persistent_entity_id.py": {
        "PersistentEntityId": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/jinja_test/public.py": {
        "Public": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/js_resource/webpack_entry_point_loader.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/license/all_rights_reserved.py": {
        "AllRightsReserved": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/license/public_domain.py": {
        "PublicDomain": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/link/betty_documentation.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/link/betty_github.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/link/http_api_doc.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/loader/demo/__init__.py": {
        "Demo": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/loader/gramps/__init__.py": {
        "Gramps": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/plugins/loader/gramps/data.py": {
        "FamilyTree": {
            "event_types": MissingReason.INHERITED,
            "file": MissingReason.INHERITED,
            "name": MissingReason.INHERITED,
            "place_types": MissingReason.INHERITED,
            "roles": MissingReason.INHERITED,
        },
    },
    "betty/plugins/place_type/borough.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/building.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/cemetery.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/city.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/country.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/county.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/department.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/district.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/farm.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/hamlet.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/locality.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/municipality.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/neighborhood.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/number.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/parish.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/province.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/region.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/state.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/street.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/town.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/unknown.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/place_type/village.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/rate_limit/wikipedia_action_api.py": {
        "WikipediaActionApi": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/rate_limit/wikipedia_rest_api.py": {
        "WikipediaRestApi": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/renderer/html.py": {
        "Html": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/renderer/plain_text.py": {
        "PlainText": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/role/attendee.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/role/beneficiary.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/role/celebrant.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/role/informant.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/role/organizer.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/role/speaker.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/role/subject.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/role/unknown.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/role/witness.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugins/serializer/json.py": {
        "Json": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/plugins/serializer/yaml.py": {
        "Yaml": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/portable/__init__.py": {
        "Portable": MissingReason.ABSTRACT,
        "Porter": MissingReason.ABSTRACT,
    },
    "betty/portable/error.py": {
        "NotPortable": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/property/__init__.py": {
        "PropertyNotInitialized": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/role/__init__.py": {
        "Role": MissingReason.STATIC_CONTENT_ONLY,
        "RoleDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "RoleManufacturer": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/role/data.py": {
        "RoleDefinitionConfiguration": {
            "data": MissingReason.INHERITED,
        },
    },
    "betty/privacy/__init__.py": {
        "Privacy": MissingReason.ENUM,
    },
    "betty/privacy/privatizer.py": {
        "Privatizer": {
            "has_expired": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/progress/__init__.py": {
        "Progress": MissingReason.ABSTRACT,
    },
    "betty/project/data.py": {
        "ProjectConfiguration": {
            "copyright_notice": MissingReason.INHERITED,
            "license": MissingReason.INHERITED,
        },
    },
    "betty/extension/__init__.py": {
        "Extension": MissingReason.SHOULD_BE_COVERED,
        "ExtensionDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "ExtensionManufacturer": MissingReason.INHERITED,
        "ExtensionError": MissingReason.STATIC_CONTENT_ONLY,
        "ExtensionTypeError": MissingReason.STATIC_CONTENT_ONLY,
        "ExtensionTypeInvalidError": MissingReason.SHOULD_BE_COVERED,
        "Theme": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/project/generate/__init__.py": {
        "Generator": MissingReason.ABSTRACT,
    },
    "betty/project/url.py": {
        "LocalizedUrlGenerator": {
            "__init_subclass__": MissingReason.INHERITED,
        },
        "StaticUrlGenerator": {
            "__init_subclass__": MissingReason.INHERITED,
        },
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
    "betty/rich/user.py": {
        "RichUser": {
            "disconnect": MissingReason.COVERED_ELSEWHERE,
        },
    },
    "betty/sample.py": {
        "Samplable": MissingReason.ABSTRACT,
        "SampleNotFound": MissingReason.STATIC_CONTENT_ONLY,
        "Size": MissingReason.ENUM,
    },
    "betty/serde.py": {
        "Serializer": MissingReason.ABSTRACT,
        "SerializerDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "SerializationError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/serve.py": {
        "ProjectServer": MissingReason.SHOULD_BE_COVERED,
        "BuiltinProjectServer": {
            "public_url": MissingReason.COVERED_ELSEWHERE,
            "stop": MissingReason.COVERED_ELSEWHERE,
        },
        "BuiltinServer": {
            "public_url": MissingReason.COVERED_ELSEWHERE,
            "stop": MissingReason.COVERED_ELSEWHERE,
        },
        "NoPublicUrlBecauseServerNotStartedError": MissingReason.SHOULD_BE_COVERED,
        "OsError": MissingReason.STATIC_CONTENT_ONLY,
        "Server": MissingReason.ABSTRACT,
        "ServerNotStartedError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/sphinx/extension/betty.py": MissingReason.COVERED_ELSEWHERE,
    "betty/subprocess.py": {
        "CalledSubprocessError": MissingReason.STATIC_CONTENT_ONLY,
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
    "betty/url/proxy.py": {
        "ProxyLocalizedUrlGenerator": {
            "__init_subclass__": MissingReason.INHERITED,
        },
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
        for file_path in sorted(errors):
            for error in errors[file_path]:
                with subtests.test():
                    raise AssertionError(error)


def _module_path_to_name(module_path: Path) -> str:
    relative_module_path = module_path.relative_to(ROOT_DIRECTORY)
    module_name_parts = relative_module_path.parent.parts
    if relative_module_path.name != "__init__.py":
        module_name_parts = (*module_name_parts, relative_module_path.name[:-3])
    return ".".join(module_name_parts)


class CoverageTester:
    def __init__(self):
        self._ignore_src_module_paths = self._get_ignore_src_module_paths()

    async def test(self) -> Mapping[Path, Sequence[str]]:
        errors: MutableMapping[Path, MutableSequence[str]] = defaultdict(list)

        for directory_path, _, file_names in walk(str(ROOT_DIRECTORY / "betty")):
            for file_name in file_names:
                file_path = Path(directory_path) / file_name
                if file_path.suffix == ".py":
                    async for file_error in self._test_python_file(file_path):
                        errors[file_path].append(file_error)
        return errors

    def _get_ignore_src_module_paths(
        self,
    ) -> Mapping[Path, _ModuleIgnore]:
        return {
            Path(module_file_path_str).resolve(): members
            for module_file_path_str, members in _BASELINE.items()
        }

    async def _test_python_file(self, file_path: Path) -> AsyncIterable[str]:
        # Skip tests.
        if ROOT_DIRECTORY / "betty" / "tests" in file_path.parents:
            return

        src_module_path = file_path.resolve()
        expected_test_module_path = (
            ROOT_DIRECTORY
            / "betty"
            / "tests"
            / src_module_path.relative_to(ROOT_DIRECTORY / "betty").parent
            / f"test_{src_module_path.name}"
        )
        async for error in _ModuleCoverageTester(
            src_module_path,
            expected_test_module_path,
            self._ignore_src_module_paths.get(src_module_path, {}),
        ).test():
            yield error

    async def _test_python_file_contains_docstring_only(self, file_path: Path) -> bool:
        with open(file_path, encoding="utf-8") as f:
            f_content = f.read()
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
            if isinstance(self._ignore, MissingReason):
                yield f"{self._src_module_path} has a matching test file at {self._test_module_path}, which was unexpectedly declared as known to be missing."
                return
            else:
                assert not isinstance(self._ignore, MissingReason)
                test_module_name, test_functions, test_classes = self._get_module_data(
                    self._test_module_path
                )
                for src_function in self._src_functions:
                    async for error in _ModuleFunctionCoverageTester(
                        src_function,
                        test_functions,
                        self._src_module_name,
                        test_module_name,
                        cast(
                            "_ModuleFunctionIgnore",
                            self._ignore.get(src_function.__name__, None),
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
                            "_ModuleClassIgnore",
                            self._ignore.get(src_class.__name__, {}),
                        ),
                    ).test():
                        yield error
            return

        if isinstance(self._ignore, MissingReason):
            return

        if await self._test_python_file_contains_docstring_only(self._src_module_path):
            return

        yield f"{self._src_module_path} does not have a matching test file. Expected {self._test_module_path} to exist."

    async def _test_python_file_contains_docstring_only(self, file_path: Path) -> bool:
        with open(file_path, encoding="utf-8") as f:
            f_content = f.read()
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
        Sequence[Intersection[_Importable, Callable[..., Any]]],
        Sequence[Intersection[_Importable, type]],
    ]:
        module_name = _module_path_to_name(module_path)
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

    async def test(self) -> AsyncIterable[str]:
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

    async def test(self) -> AsyncIterable[str]:
        expected_test_class_name = (
            f"Test{self._src_class.__name__[0].upper()}{self._src_class.__name__[1:]}"
        )

        if expected_test_class_name in self._test_classes:
            if isinstance(self._ignore, MissingReason):
                yield f"The source class {self._src_class.__module__}.{self._src_class.__name__} has a matching test class at {self._test_classes[expected_test_class_name].__module__}.{self._test_classes[expected_test_class_name].__name__}, which was unexpectedly declared as known to be missing."
                return
            assert not isinstance(self._ignore, MissingReason)
            for error in self._test_members(
                self._test_classes[expected_test_class_name], self._ignore
            ):
                yield error
            return

        if isinstance(self._ignore, MissingReason):
            return

        yield f"Failed to find the test class {self._test_module_name}.{expected_test_class_name} for the source class {self._src_module_name}.{self._src_class.__name__}."

    _EXCLUDE_DUNDER_METHODS = (
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

        if isinstance(ignore, MissingReason):
            return

        yield f"Failed to find a test method named {expected_test_member_name}() or any methods whose names start with `{expected_test_member_name_prefix}` in {self._test_module_name}.{test_class.__name__} for the source member {self._src_module_name}.{self._src_class.__name__}.{src_member_name}()."


class Test_ModuleCoverageTester:
    @pytest.mark.parametrize(
        ("errors_expected", "module", "ignore"),
        [
            (False, _module_private, MissingReason.SHOULD_BE_COVERED),
            (False, _module_private, {}),
            (True, module_with_test, MissingReason.SHOULD_BE_COVERED),
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
        assert (len([error async for error in sut.test()]) > 0) is errors_expected


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
        assert (len([error async for error in sut.test()]) > 0) is errors_expected


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
        assert (len([error async for error in sut.test()]) > 0) is errors_expected
