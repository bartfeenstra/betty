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
from configparser import ConfigParser
from enum import Enum
from importlib import import_module
from inspect import getmembers, isclass, isdatadescriptor, isfunction
from os import walk
from pathlib import Path
from typing import Any, Protocol, TypeAlias, cast

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
    "betty/app/factory.py": {
        "AppDependentFactory": MissingReason.ABSTRACT,
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
    "betty/attr.py": {
        "AttrNotInitialized": MissingReason.STATIC_CONTENT_ONLY,
        "OptionalAttr": MissingReason.SHOULD_BE_COVERED,
        "RequiredAttr": MissingReason.SHOULD_BE_COVERED,
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
    },
    "betty/console/command/commands/dev_profile_demo.py": MissingReason.DEVELOPMENT,
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
    "betty/config/__init__.py": {
        "Configuration": {
            "validator": MissingReason.STATIC_CONTENT_ONLY,
        }
    },
    "betty/config/collections/__init__.py": MissingReason.ABSTRACT,
    "betty/config/factory.py": {
        "ConfigurationDependentSelfFactory": MissingReason.ABSTRACT,
    },
    "betty/content_provider/__init__.py": {
        "ContentProvider": MissingReason.ABSTRACT,
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
    "betty/service/level/__init__.py": MissingReason.ABSTRACT,
    "betty/service/level/factory.py": MissingReason.ABSTRACT,
    "betty/data.py": {
        "Context": MissingReason.ABSTRACT,
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
            "contexts": MissingReason.COVERED_ELSEWHERE,
        },
        "HumanFacingExceptionGroup": {
            "invalid": MissingReason.COVERED_ELSEWHERE,
        },
    },
    "betty/factory.py": {
        "Factory": MissingReason.PROTOCOL,
        "SelfFactory": MissingReason.ABSTRACT,
    },
    "betty/fetch/__init__.py": {
        "Fetcher": MissingReason.ABSTRACT,
        "FetchResponse": {
            "__annotate_func__": MissingReason.DATACLASS,
            "__eq__": MissingReason.DATACLASS,
            "__delattr__": MissingReason.DATACLASS,
            "__hash__": MissingReason.DATACLASS,
            "__replace__": MissingReason.DATACLASS,
            "__setattr__": MissingReason.DATACLASS,
        },
    },
    "betty/fetch/static.py": MissingReason.SHOULD_BE_COVERED,
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
    "betty/json/linked_data.py": MissingReason.SHOULD_BE_COVERED,
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
        "InvalidMediaType": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/media_type/media_types.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/model/__init__.py": {
        "Entity": MissingReason.SHOULD_BE_COVERED,
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
    "betty/ancestry/date.py": {
        "HasDate": {
            "dated_linked_data_contexts": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/ancestry/event.py": {
        "Event": {
            "dated_linked_data_contexts": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/ancestry/event_type/__init__.py": {
        "EventType": MissingReason.STATIC_CONTENT_ONLY,
        "ShouldExistEventType": MissingReason.ABSTRACT,
    },
    "betty/ancestry/gender/__init__.py": {
        "Gender": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/ancestry/place_type/__init__.py": {
        "PlaceType": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/ancestry/presence_role/__init__.py": {
        "PresenceRole": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/copyright_notice/__init__.py": {
        "CopyrightNotice": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/license/__init__.py": {
        "License": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/path.py": MissingReason.SHOULD_BE_COVERED,
    "betty/multiprocessing.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/mutability.py": {
        "MutabilityError": MissingReason.STATIC_CONTENT_ONLY,
        "MutableError": MissingReason.STATIC_CONTENT_ONLY,
        "ImmutableError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/openapi.py": {
        "SpecificationSchema": {"__annotate_func__": MissingReason.DATACLASS},
    },
    "betty/plugin/__init__.py": {
        "Plugin": MissingReason.ABSTRACT,
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
    "betty/plugin/repository/provider/__init__.py": {
        "PluginRepositoryProvider": MissingReason.ABSTRACT,
    },
    "betty/plugin/discovery/__init__.py": {
        "PluginDiscovery": MissingReason.ABSTRACT,
    },
    "betty/plugin/assertion.py": {
        "assert_plugin": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/plugin/config/__init__.py": {
        "PluginDefinitionConfigurationMapping": MissingReason.SHOULD_BE_COVERED,
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
        "EventTypePluginConfiguration": MissingReason.STATIC_CONTENT_ONLY,
        "GenderPluginConfiguration": MissingReason.STATIC_CONTENT_ONLY,
        "PlaceTypePluginConfiguration": MissingReason.STATIC_CONTENT_ONLY,
        "PresenceRolePluginConfiguration": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/project/extension/__init__.py": {
        "ExtensionError": MissingReason.STATIC_CONTENT_ONLY,
        "ExtensionTypeError": MissingReason.STATIC_CONTENT_ONLY,
        "ExtensionTypeInvalidError": MissingReason.SHOULD_BE_COVERED,
        "Theme": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/project/extension/demo/__init__.py": {
        "Demo": {
            "secondary_navigation_links": MissingReason.STATIC_CONTENT_ONLY,
        },
    },
    "betty/project/extension/demo/serve.py": {
        "DemoServer": {
            "public_url": MissingReason.SHOULD_BE_COVERED,
            "start": MissingReason.SHOULD_BE_COVERED,
            "stop": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/project/extension/gramps/config.py": {
        "EventTypeMapping": MissingReason.STATIC_CONTENT_ONLY,
        "PlaceTypeMapping": MissingReason.STATIC_CONTENT_ONLY,
        "PresenceRoleMapping": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/project/extension/privatizer/__init__.py": {
        "Privatizer": {
            "post_load": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/project/extension/raspberry_mint/__init__.py": {
        "Breakpoint": MissingReason.ENUM,
        "ColorStyle": MissingReason.ENUM,
        "JustifyContent": MissingReason.ENUM,
    },
    "betty/project/extension/webpack/build.py": {
        "EntryPointProvider": MissingReason.ABSTRACT,
        "webpack_build_id": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/project/extension/webpack/jinja2/__init__.py": MissingReason.SHOULD_BE_COVERED,
    "betty/project/extension/webpack/jinja2/filter.py": MissingReason.SHOULD_BE_COVERED,
    "betty/project/extension/wiki/config.py": {
        "WikiConfiguration": {
            "populate_images": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/project/factory.py": {
        "ProjectDependentFactory": MissingReason.ABSTRACT,
    },
    "betty/project/generate/__init__.py": {
        "Generator": MissingReason.ABSTRACT,
    },
    "betty/project/load/__init__.py": {
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
    },
    "betty/repr.py": MissingReason.SHOULD_BE_COVERED,
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
    "betty/serde/dump.py": MissingReason.SHOULD_BE_COVERED,
    "betty/serde/format/__init__.py": {
        "Format": MissingReason.ABSTRACT,
        "FormatError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/serde/load.py": MissingReason.ABSTRACT,
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
        "InvalidMediaType": MissingReason.STATIC_CONTENT_ONLY,
        "LocalizedUrlGenerator": MissingReason.ABSTRACT,
        "StaticUrlGenerator": MissingReason.ABSTRACT,
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
    async def test(self) -> None:
        tester = CoverageTester()
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
        errors: MutableMapping[Path, MutableSequence[str]] = defaultdict(list)

        for directory_path, _, file_names in walk(str(ROOT_DIRECTORY_PATH / "betty")):
            for file_name in file_names:
                file_path = Path(directory_path) / file_name
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
            **dict.fromkeys(
                self._get_coveragerc_ignore_modules(), MissingReason.SHOULD_BE_COVERED
            ),
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
            imported_member = cast(_Importable, getattr(module, member_name))
            if getattr(imported_member, "__module__", None) != module_name:
                continue

            yield imported_member


class _ModuleFunctionCoverageTester:
    def __init__(
        self,
        src_function: _Importable & Callable[..., Any],
        test_functions: Sequence[_Importable & Callable[..., Any]],
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
            "_Importable & Callable[..., Any] | None", getattr(module, "test_src", None)
        )
        sut = _ModuleFunctionCoverageTester(
            module.src,  # type: ignore[attr-defined]
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
            module.Src,  # type: ignore[attr-defined]
            () if test_class is None else (test_class,),
            module.__name__,
            module.__name__,
            ignore,
        )
        assert (len([error async for error in sut.test()]) > 0) is errors_expected
