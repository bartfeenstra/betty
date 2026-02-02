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
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, cast

import aiofiles
import pytest

from betty.dirs import ROOT_DIRECTORY_PATH
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
    from ty_extensions import Intersection


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


_ModuleFunctionExistsIgnore: TypeAlias = None
_ModuleFunctionIgnore = _ModuleFunctionExistsIgnore | MissingReason
_ModuleClassExistsIgnore = Mapping[str, _ModuleFunctionIgnore]
_ModuleClassIgnore = _ModuleClassExistsIgnore | MissingReason
_ModuleMemberIgnore = _ModuleFunctionIgnore | _ModuleClassIgnore
_ModuleExistsIgnore = Mapping[str, _ModuleMemberIgnore]
_ModuleIgnore = _ModuleExistsIgnore | MissingReason

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
        "AssetError": MissingReason.ABSTRACT,
        "AssetRepository": MissingReason.ABSTRACT,
    },
    "betty/assertion.py": {
        "Field": MissingReason.INTERNAL,
        "OptionalField": MissingReason.DATACLASS,
        "RequiredField": MissingReason.DATACLASS,
    },
    "betty/cache/__init__.py": {
        "Cache": MissingReason.ABSTRACT,
        "CacheItem": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/cache/_base.py": MissingReason.COVERED_ELSEWHERE,
    "betty/console/__init__.py": {
        "SystemExitCode": MissingReason.ENUM,
    },
    "betty/console/command/__init__.py": {
        "Command": MissingReason.SHOULD_BE_COVERED,
        "CommandDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/console/command/commands/about.py": {
        "About": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/command/commands/clear_caches.py": {
        "ClearCaches": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/command/commands/config.py": {
        "Config": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/command/commands/demo.py": {
        "Demo": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/command/commands/dev_profile_demo.py": MissingReason.DEVELOPMENT,
    "betty/console/command/commands/dev_update_translations.py": {
        "DevUpdateTranslations": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/command/commands/docs.py": {
        "Docs": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/command/commands/extension_new_translation.py": {
        "ExtensionNewTranslation": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/command/commands/extension_update_translations.py": {
        "ExtensionUpdateTranslations": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/command/commands/generate.py": {
        "Generate": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/command/commands/new.py": {
        "New": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/command/commands/new_translation.py": {
        "NewTranslation": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/command/commands/serve.py": {
        "Serve": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/command/commands/update_translations.py": {
        "UpdateTranslations": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/console/project.py": {
        "ConfigurationFileNotFound": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/concurrent.py": {
        "AsynchronizedLock": {
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
    "betty/content_provider/__init__.py": {
        "ContentProvider": MissingReason.ABSTRACT,
        "ContentProviderDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/content_provider/content_providers.py": {
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
        "Notes": {
            "plugin": MissingReason.INHERITED,
        },
        "Render": {
            "plugin": MissingReason.INHERITED,
        },
        "RenderConfiguration": {
            "media_type": MissingReason.INHERITED,
        },
        "Template": {
            "provide_template": MissingReason.ABSTRACT,
        },
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
    "betty/service/bootstrap.py": {
        "BootstrappedError": MissingReason.ABSTRACT,
        "NotBootstrappedError": MissingReason.ABSTRACT,
        "Shutdownable": MissingReason.ABSTRACT,
        "ShutdownCallbackKwargs": MissingReason.TYPED_DICT,
        "ShutdownStack": {
            "append": MissingReason.COVERED_ELSEWHERE,
        },
    },
    "betty/service/container.py": {
        "ServiceContainer": {
            "new_target": MissingReason.ABSTRACT,
        },
        "ServiceInitializedError": MissingReason.ABSTRACT,
    },
    "betty/service/hydrate.py": {
        "Hydratable": MissingReason.ABSTRACT,
        "Hydrator": MissingReason.ABSTRACT,
    },
    "betty/service/level.py": {
        "Manufacturable": MissingReason.ABSTRACT,
    },
    "betty/service/requirement/__init__.py": {
        "ServiceLevelKwargs": MissingReason.TYPED_DICT,
        "UnmetRequirement": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/service/requirement/app.py": {
        "RequireAppKwargs": MissingReason.TYPED_DICT,
    },
    "betty/service/requirement/extension.py": {
        "RequireExtensionKwargs": MissingReason.TYPED_DICT,
    },
    "betty/service/requirement/project.py": {
        "RequireProjectKwargs": MissingReason.TYPED_DICT,
    },
    "betty/data/__init__.py": {
        "Data": MissingReason.ABSTRACT,
    },
    "betty/data/aggregate/__init__.py": {
        "AggregateDefinition": {
            "elements": MissingReason.ABSTRACT,
        },
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
    "betty/data/aggregate/record/object/property.py": {
        "PropertyNotInitialized": MissingReason.STATIC_CONTENT_ONLY,
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
    "betty/html/__init__.py": {
        "CssProvider": MissingReason.ABSTRACT,
        "JsProvider": MissingReason.ABSTRACT,
    },
    "betty/html/attributes.py": {
        "Attributes": {
            attr_name: MissingReason.STATIC_CONTENT_ONLY
            for attr_name, _ in getmembers(Attributes)
            if attr_name.startswith("html_")
        },
    },
    "betty/http_client/rate_limit.py": {
        "RateLimit": MissingReason.ABSTRACT,
        "RateLimitDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/http_client/rate_limits.py": {
        "WikipediaActionApi": {
            "plugin": MissingReason.INHERITED,
        },
        "WikipediaRestApi": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/jinja2/__init__.py": {
        "context_job_context": MissingReason.SHOULD_BE_COVERED,
        "context_localizer": MissingReason.SHOULD_BE_COVERED,
        "context_project": MissingReason.SHOULD_BE_COVERED,
        "context_document": MissingReason.SHOULD_BE_COVERED,
        "Environment": {},
    },
    "betty/jinja2/filter.py": {
        "filters": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/jinja2/test.py": {
        "tests": MissingReason.STATIC_CONTENT_ONLY,
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
    "betty/link.py": MissingReason.ABSTRACT,
    "betty/locale/babel.py": {
        "run_babel": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/locale/error.py": {
        "LocaleError": MissingReason.ABSTRACT,
    },
    "betty/locale/translation/__init__.py": {
        "find_source_files": MissingReason.SHOULD_BE_COVERED,
        "new_dev_translation": MissingReason.SHOULD_BE_COVERED,
        "AssetTranslationRepository": {
            "bootstrap": MissingReason.COVERED_ELSEWHERE,
        },
        "TranslationRepository": MissingReason.ABSTRACT,
        "update_dev_translations": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/locale/translation/project/__init__.py": {
        "new_project_translation": MissingReason.SHOULD_BE_COVERED,
        "update_project_translations": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/locale/translation/project/extension.py": {
        "new_extension_translation": MissingReason.SHOULD_BE_COVERED,
        "update_extension_translations": MissingReason.SHOULD_BE_COVERED,
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
    "betty/media_type/__init__.py": {
        "MediaType": {
            "data": MissingReason.INHERITED,
        },
        "InvalidMediaType": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/media_type/media_types.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/model/__init__.py": {
        "Entity": MissingReason.SHOULD_BE_COVERED,
        "EntityDefinition": {
            "type": MissingReason.INHERITED,
        },
        "EntityReferenceCollectionSchema": MissingReason.STATIC_CONTENT_ONLY,
        "EntityReferenceSchema": MissingReason.STATIC_CONTENT_ONLY,
        "NonPersistentId": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/model/association.py": {
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
    "betty/model/collections.py": {
        "EntityCollection": MissingReason.ABSTRACT,
        "record_added": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/ancestry/citation.py": {
        "Citation": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/ancestry/date.py": {
        "HasDate": {
            "dated_linked_data_contexts": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/ancestry/enclosure.py": {
        "Enclosure": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/ancestry/event.py": {
        "Event": {
            "dated_linked_data_contexts": MissingReason.STATIC_CONTENT_ONLY,
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/ancestry/file.py": {
        "File": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/ancestry/file_reference.py": {
        "FileReference": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/ancestry/link.py": {
        "Link": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/ancestry/note.py": {
        "Note": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/ancestry/person.py": {
        "Person": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/ancestry/person_name.py": {
        "PersonName": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/ancestry/place.py": {
        "Place": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/ancestry/presence.py": {
        "Presence": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/ancestry/source.py": {
        "Source": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/collections.py": {
        "KeyedCollection": MissingReason.ABSTRACT,
        "MutableCollection": MissingReason.ABSTRACT,
        "MutableKeyedCollection": MissingReason.ABSTRACT,
        "MutableResolvedMapping": MissingReason.ABSTRACT,
        "MutableResolvedSequence": MissingReason.ABSTRACT,
        "ResolvedMapping": MissingReason.ABSTRACT,
    },
    "betty/config.py": {
        "Configurable": MissingReason.ABSTRACT,
    },
    "betty/copyright_notice/__init__.py": {
        "CopyrightNotice": MissingReason.STATIC_CONTENT_ONLY,
        "CopyrightNoticeDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/copyright_notice/config.py": {
        "CopyrightNoticeDefinitionConfiguration": {
            "data": MissingReason.INHERITED,
        },
    },
    "betty/copyright_notice/copyright_notices.py": {
        "ProjectAuthor": {
            "plugin": MissingReason.INHERITED,
        },
        "PublicDomain": {
            "plugin": MissingReason.INHERITED,
        },
        "Streetmix": {
            "plugin": MissingReason.INHERITED,
        },
        "WikipediaContributors": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/event_type/__init__.py": {
        "EventType": MissingReason.STATIC_CONTENT_ONLY,
        "EventTypeDefinition": {
            "type": MissingReason.INHERITED,
        },
        "ShouldExistEventType": MissingReason.ABSTRACT,
    },
    "betty/event_type/config.py": {
        "EventTypeDefinitionConfiguration": {
            "data": MissingReason.INHERITED,
        },
    },
    "betty/event_type/event_types.py": {
        "Adoption": MissingReason.STATIC_CONTENT_ONLY,
        "Baptism": MissingReason.STATIC_CONTENT_ONLY,
        "BatMitzvah": MissingReason.STATIC_CONTENT_ONLY,
        "BarMitzvah": MissingReason.STATIC_CONTENT_ONLY,
        "Birth": MissingReason.STATIC_CONTENT_ONLY,
        "Burial": MissingReason.STATIC_CONTENT_ONLY,
        "Conference": MissingReason.STATIC_CONTENT_ONLY,
        "Confirmation": MissingReason.STATIC_CONTENT_ONLY,
        "Correspondence": MissingReason.STATIC_CONTENT_ONLY,
        "Cremation": MissingReason.STATIC_CONTENT_ONLY,
        "Death": {
            "plugin": MissingReason.INHERITED,
        },
        "Divorce": MissingReason.STATIC_CONTENT_ONLY,
        "DivorceAnnouncement": MissingReason.STATIC_CONTENT_ONLY,
        "Emigration": MissingReason.STATIC_CONTENT_ONLY,
        "Engagement": MissingReason.STATIC_CONTENT_ONLY,
        "Funeral": MissingReason.STATIC_CONTENT_ONLY,
        "Immigration": MissingReason.STATIC_CONTENT_ONLY,
        "Marriage": MissingReason.STATIC_CONTENT_ONLY,
        "MarriageAnnouncement": MissingReason.STATIC_CONTENT_ONLY,
        "Missing": MissingReason.STATIC_CONTENT_ONLY,
        "Occupation": MissingReason.STATIC_CONTENT_ONLY,
        "Residence": MissingReason.STATIC_CONTENT_ONLY,
        "Retirement": MissingReason.STATIC_CONTENT_ONLY,
        "Unknown": MissingReason.STATIC_CONTENT_ONLY,
        "Will": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/license/__init__.py": {
        "License": MissingReason.STATIC_CONTENT_ONLY,
        "LicenseDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/license/config.py": {
        "LicenseDefinitionConfiguration": {
            "data": MissingReason.INHERITED,
        },
    },
    "betty/license/licenses.py": {
        "AllRightsReserved": {
            "plugin": MissingReason.INHERITED,
        },
        "PublicDomain": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/gender/__init__.py": {
        "Gender": MissingReason.STATIC_CONTENT_ONLY,
        "GenderDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/gender/config.py": {
        "GenderDefinitionConfiguration": {
            "data": MissingReason.INHERITED,
        },
    },
    "betty/gender/genders.py": {
        "Man": MissingReason.STATIC_CONTENT_ONLY,
        "NonBinary": MissingReason.STATIC_CONTENT_ONLY,
        "Unknown": MissingReason.STATIC_CONTENT_ONLY,
        "Woman": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/npm.py": {
        "is_available": MissingReason.SHOULD_BE_COVERED,
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
    },
    "betty/place_type/config.py": {
        "PlaceTypeDefinitionConfiguration": {
            "data": MissingReason.INHERITED,
        },
    },
    "betty/place_type/place_types.py": {
        "Borough": MissingReason.STATIC_CONTENT_ONLY,
        "Building": MissingReason.STATIC_CONTENT_ONLY,
        "Cemetery": MissingReason.STATIC_CONTENT_ONLY,
        "City": MissingReason.STATIC_CONTENT_ONLY,
        "Country": MissingReason.STATIC_CONTENT_ONLY,
        "County": MissingReason.STATIC_CONTENT_ONLY,
        "Department": MissingReason.STATIC_CONTENT_ONLY,
        "District": MissingReason.STATIC_CONTENT_ONLY,
        "Farm": MissingReason.STATIC_CONTENT_ONLY,
        "Hamlet": MissingReason.STATIC_CONTENT_ONLY,
        "Locality": MissingReason.STATIC_CONTENT_ONLY,
        "Municipality": MissingReason.STATIC_CONTENT_ONLY,
        "Neighborhood": MissingReason.STATIC_CONTENT_ONLY,
        "Number": MissingReason.STATIC_CONTENT_ONLY,
        "Parish": MissingReason.STATIC_CONTENT_ONLY,
        "Province": MissingReason.STATIC_CONTENT_ONLY,
        "Region": MissingReason.STATIC_CONTENT_ONLY,
        "State": MissingReason.STATIC_CONTENT_ONLY,
        "Street": MissingReason.STATIC_CONTENT_ONLY,
        "Town": MissingReason.STATIC_CONTENT_ONLY,
        "Unknown": MissingReason.STATIC_CONTENT_ONLY,
        "Village": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/plugin/__init__.py": {
        "Plugin": MissingReason.ABSTRACT,
    },
    "betty/plugin/config/__init__.py": {
        "PluginDefinitionConfiguration": {"new_plugin": MissingReason.ABSTRACT},
    },
    "betty/plugin/error.py": {
        "PluginError": MissingReason.ABSTRACT,
        "PluginUnavailable": MissingReason.ABSTRACT,
    },
    "betty/plugin/repository/__init__.py": {
        "PluginRepository": {
            "__iter__": MissingReason.ABSTRACT,
            "get": MissingReason.ABSTRACT,
        },
    },
    "betty/plugin/manager/__init__.py": {
        "PluginManager": MissingReason.ABSTRACT,
    },
    "betty/plugin/discovery/__init__.py": {
        "PluginDiscovery": MissingReason.ABSTRACT,
    },
    "betty/plugin/assertion.py": {
        "assert_plugin": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/portable/__init__.py": {
        "Portable": MissingReason.ABSTRACT,
        "Porter": MissingReason.ABSTRACT,
    },
    "betty/portable/error.py": {
        "NotPortable": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/presence_role/__init__.py": {
        "PresenceRole": MissingReason.STATIC_CONTENT_ONLY,
        "PresenceRoleDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/presence_role/config.py": {
        "PresenceRoleDefinitionConfiguration": {
            "data": MissingReason.INHERITED,
        },
    },
    "betty/presence_role/presence_roles.py": {
        "Attendee": MissingReason.STATIC_CONTENT_ONLY,
        "Beneficiary": MissingReason.STATIC_CONTENT_ONLY,
        "Celebrant": MissingReason.STATIC_CONTENT_ONLY,
        "Informant": MissingReason.STATIC_CONTENT_ONLY,
        "Organizer": MissingReason.STATIC_CONTENT_ONLY,
        "Speaker": MissingReason.STATIC_CONTENT_ONLY,
        "Subject": MissingReason.STATIC_CONTENT_ONLY,
        "Unknown": MissingReason.STATIC_CONTENT_ONLY,
        "Witness": MissingReason.STATIC_CONTENT_ONLY,
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
    "betty/project/config.py": {
        "ProjectConfiguration": {
            "copyright_notice": MissingReason.INHERITED,
            "license": MissingReason.INHERITED,
        },
    },
    "betty/extension/__init__.py": {
        "Extension": MissingReason.SHOULD_BE_COVERED,
        "ExtensionDefinition": {
            "type": MissingReason.INHERITED,
        },
        "ExtensionError": MissingReason.STATIC_CONTENT_ONLY,
        "ExtensionTypeError": MissingReason.STATIC_CONTENT_ONLY,
        "ExtensionTypeInvalidError": MissingReason.SHOULD_BE_COVERED,
        "Theme": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/extension/demo/__init__.py": {
        "Demo": {
            "secondary_navigation_links": MissingReason.STATIC_CONTENT_ONLY,
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/extension/deriver/__init__.py": {
        "Deriver": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/extension/demo/serve.py": {
        "DemoServer": {
            "public_url": MissingReason.SHOULD_BE_COVERED,
            "start": MissingReason.SHOULD_BE_COVERED,
            "stop": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/extension/gramps/__init__.py": {
        "Gramps": {
            "plugin": MissingReason.INHERITED,
        }
    },
    "betty/extension/gramps/config.py": {
        "FamilyTreeConfiguration": {
            "event_types": MissingReason.INHERITED,
            "file": MissingReason.INHERITED,
            "name": MissingReason.INHERITED,
            "place_types": MissingReason.INHERITED,
            "presence_roles": MissingReason.INHERITED,
        },
    },
    "betty/extension/http_api_doc/__init__.py": {
        "HttpApiDoc": {
            "plugin": MissingReason.INHERITED,
            "webpack_entry_point_cache_keys": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/extension/maps/__init__.py": {
        "Maps": {
            "plugin": MissingReason.INHERITED,
            "webpack_entry_point_cache_keys": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/extension/maps/content_provider.py": {
        "Map": {
            "plugin": MissingReason.INHERITED,
        },
        "Attribution": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/extension/privatizer/__init__.py": {
        "Privatizer": {
            "post_load": MissingReason.SHOULD_BE_COVERED,
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/extension/raspberry_mint/__init__.py": {
        "Breakpoint": MissingReason.ENUM,
        "ColorStyle": MissingReason.ENUM,
        "JustifyContent": MissingReason.ENUM,
        "RaspberryMint": {
            "plugin": MissingReason.INHERITED,
            "webpack_entry_point_cache_keys": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/extension/raspberry_mint/content_provider.py": {
        "Citations": {
            "plugin": MissingReason.INHERITED,
        },
        "ColorStyle": {
            "plugin": MissingReason.INHERITED,
        },
        "Columns": {
            "plugin": MissingReason.INHERITED,
        },
        "Enclosees": {
            "plugin": MissingReason.INHERITED,
        },
        "EntityCard": {
            "plugin": MissingReason.INHERITED,
        },
        "ExternalLinks": {
            "plugin": MissingReason.INHERITED,
        },
        "Facts": {
            "plugin": MissingReason.INHERITED,
        },
        "Families": {
            "plugin": MissingReason.INHERITED,
        },
        "FileReferees": {
            "plugin": MissingReason.INHERITED,
        },
        "Media": {
            "plugin": MissingReason.INHERITED,
        },
        "MediaGallery": {
            "plugin": MissingReason.INHERITED,
        },
        "Presences": {
            "plugin": MissingReason.INHERITED,
        },
        "Section": {
            "plugin": MissingReason.INHERITED,
        },
        "Timeline": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/extension/trees/__init__.py": {
        "Trees": {
            "plugin": MissingReason.INHERITED,
            "webpack_entry_point_cache_keys": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/extension/spdx/__init__.py": {
        "Spdx": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/extension/trees/content_provider.py": {
        "Tree": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/extension/webpack/__init__.py": {
        "Webpack": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/extension/webpack/build.py": {
        "EntryPointProvider": MissingReason.ABSTRACT,
        "webpack_build_id": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/extension/webpack/jinja2/__init__.py": MissingReason.SHOULD_BE_COVERED,
    "betty/extension/webpack/jinja2/filter.py": MissingReason.SHOULD_BE_COVERED,
    "betty/extension/wiki/__init__.py": {
        "Wiki": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/extension/wiki/config.py": {
        "WikiConfiguration": {
            "populate_images": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/extension/wiki/content_provider.py": {
        "WikipediaSummary": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/project/generate/__init__.py": {
        "Generator": MissingReason.ABSTRACT,
    },
    "betty/project/load/__init__.py": {
        "load": MissingReason.SHOULD_BE_COVERED,
        "Loader": MissingReason.ABSTRACT,
        "PostLoader": MissingReason.ABSTRACT,
    },
    "betty/project/url.py": {
        "LocalizedUrlGenerator": {
            "__init_subclass__": MissingReason.INHERITED,
        },
        "StaticUrlGenerator": {
            "__init_subclass__": MissingReason.INHERITED,
        },
    },
    "betty/render/__init__.py": {
        "Renderer": MissingReason.ABSTRACT,
        "RendererDefinition": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/render/html.py": {
        "Html": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/render/plain_text.py": {
        "PlainText": {
            "plugin": MissingReason.INHERITED,
        },
    },
    "betty/requirement.py": {
        "HasRequirement": MissingReason.STATIC_CONTENT_ONLY,
        "Requirement": {
            "details": MissingReason.ABSTRACT,
            "is_met": MissingReason.ABSTRACT,
            "reduce": MissingReason.ABSTRACT,
            "summary": MissingReason.ABSTRACT,
        },
    },
    "betty/document.py": {
        "DocumentProvider": MissingReason.STATIC_CONTENT_ONLY,
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
    "betty/serde/__init__.py": {
        "Serializer": MissingReason.ABSTRACT,
        "SerializerDefinition": MissingReason.STATIC_CONTENT_ONLY,
        "SerializationError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/serde/serializers.py": {
        "Json": {
            "plugin": MissingReason.INHERITED,
        },
        "Yaml": {
            "plugin": MissingReason.INHERITED,
        },
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
        "Void": MissingReason.SHOULD_BE_COVERED,
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
    relative_module_path = module_path.relative_to(ROOT_DIRECTORY_PATH)
    module_name_parts = relative_module_path.parent.parts
    if relative_module_path.name != "__init__.py":
        module_name_parts = (*module_name_parts, relative_module_path.name[:-3])
    return ".".join(module_name_parts)


class CoverageTester:
    def __init__(self):
        self._ignore_src_module_paths = self._get_ignore_src_module_paths()

    async def test(self) -> Mapping[Path, Sequence[str]]:
        errors: MutableMapping[Path, MutableSequence[str]] = defaultdict(list)

        for directory_path, _, file_names in walk(str(ROOT_DIRECTORY_PATH / "betty")):
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
        Sequence[Intersection[_Importable, Callable[..., Any]]],
        Sequence[Intersection[_Importable, type]],
    ]:
        module_name = _module_path_to_name(module_path)
        return (
            module_name,
            sorted(
                self._get_members(module_name, isfunction),
                key=lambda member: member.__name__,
            ),
            sorted(
                self._get_members(module_name, isclass),
                key=lambda member: member.__name__,
            ),
        )  # ty:ignore[invalid-return-type]

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
