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
    MutableSequence,
)
from configparser import ConfigParser
from importlib import import_module
from inspect import getmembers, isfunction, isclass, isdatadescriptor
from os import walk
from pathlib import Path
from typing import Protocol, Any, cast, TypeAlias

import aiofiles
import pytest

from betty.fs import ROOT_DIRECTORY_PATH
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
    "betty/assets.py": {
        "AssetRepository": {
            "__len__": TestKnownToBeMissing,
            "clear": TestKnownToBeMissing,
            "paths": TestKnownToBeMissing,
            "prepend": TestKnownToBeMissing,
        },
    },
    "betty/app/config.py": {
        "AppConfiguration": TestKnownToBeMissing,
    },
    # This contains a single abstract class.
    "betty/app/factory.py": TestKnownToBeMissing,
    "betty/assertion/__init__.py": {
        "assert_assertions": TestKnownToBeMissing,
        "assert_entity_type": TestKnownToBeMissing,
        "assert_locale": TestKnownToBeMissing,
        "assert_none": TestKnownToBeMissing,
        "assert_setattr": TestKnownToBeMissing,
        "Fields": TestKnownToBeMissing,
        "OptionalField": TestKnownToBeMissing,
        "RequiredField": TestKnownToBeMissing,
    },
    "betty/assertion/error.py": {
        # This is an abstract class.
        "AssertionContext": TestKnownToBeMissing,
        "AssertionFailed": {
            "contexts": TestKnownToBeMissing,
            "raised": TestKnownToBeMissing,
        },
        "AssertionFailedGroup": {
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
    "betty/cache/__init__.py": {
        # This is an interface.
        "Cache": TestKnownToBeMissing,
        "CacheItem": TestKnownToBeMissing,
    },
    "betty/cache/_base.py": TestKnownToBeMissing,
    "betty/cli/__init__.py": {
        "ContextAppObject": TestKnownToBeMissing,
        "ctx_app_object": TestKnownToBeMissing,
    },
    "betty/cli/error.py": {
        "user_facing_error_to_bad_parameter": TestKnownToBeMissing,
    },
    "betty/cli/commands/__init__.py": {
        "command": TestKnownToBeMissing,
        "Command": TestKnownToBeMissing,
        "CommandRepository": TestKnownToBeMissing,
        "discover_commands": TestKnownToBeMissing,
        "parameter_callback": TestKnownToBeMissing,
        "project_option": TestKnownToBeMissing,
    },
    "betty/concurrent.py": {
        "AsynchronizedLock": {
            "release": TestKnownToBeMissing,
        },
        "Lock": {
            # This is covered by another test method.
            "__aexit__": TestKnownToBeMissing,
            # This is an abstract method.
            "acquire": TestKnownToBeMissing,
            # This is an abstract method.
            "release": TestKnownToBeMissing,
        },
        "Ledger": TestKnownToBeMissing,
        "RateLimiter": {
            "__aenter__": TestKnownToBeMissing,
            "__aexit__": TestKnownToBeMissing,
        },
    },
    "betty/config/__init__.py": {
        "assert_configuration_file": TestKnownToBeMissing,
        "Configurable": TestKnownToBeMissing,
        # This is an abstract class.
        "Configuration": TestKnownToBeMissing,
        "write_configuration_file": TestKnownToBeMissing,
    },
    "betty/config/collections/__init__.py": TestKnownToBeMissing,
    "betty/config/collections/sequence.py": {
        "ConfigurationSequence": {
            "dump": TestKnownToBeMissing,
            "to_index": TestKnownToBeMissing,
            "to_key": TestKnownToBeMissing,
            "update": TestKnownToBeMissing,
        },
    },
    "betty/contextlib.py": {
        "SynchronizedContextManager": {
            "__enter__": TestKnownToBeMissing,
            "__exit__": TestKnownToBeMissing,
        },
    },
    "betty/date.py": {
        "Date": {
            "__contains__": TestKnownToBeMissing,
            "__ge__": TestKnownToBeMissing,
            "__le__": TestKnownToBeMissing,
        },
        "DateRange": {
            "__contains__": TestKnownToBeMissing,
            "__ge__": TestKnownToBeMissing,
            "__le__": TestKnownToBeMissing,
            "comparable": TestKnownToBeMissing,
        },
        # This is an empty class.
        "IncompleteDateError": TestKnownToBeMissing,
    },
    "betty/deriver.py": {
        # This is an enum.
        "Derivation": TestKnownToBeMissing
    },
    "betty/documentation.py": {
        "DocumentationServer": {
            "public_url": TestKnownToBeMissing,
            "start": TestKnownToBeMissing,
            "stop": TestKnownToBeMissing,
        },
    },
    "betty/error.py": TestKnownToBeMissing,
    "betty/event_dispatcher.py": {
        # This is an interface.
        "Event": TestKnownToBeMissing,
        "EventHandlerRegistry": {
            # This is covered by another test.
            "handlers": TestKnownToBeMissing,
        },
    },
    "betty/factory.py": {
        # This is an abstract class.
        "IndependentFactory": TestKnownToBeMissing,
        # This is an abstract class.
        "TargetFactory": TestKnownToBeMissing,
    },
    "betty/fetch/__init__.py": {
        # This is an interface.
        "Fetcher": TestKnownToBeMissing,
        "FetchResponse": {
            # This is inherited from @dataclass.
            "__eq__": TestKnownToBeMissing,
            # This is inherited from @dataclass.
            "__delattr__": TestKnownToBeMissing,
            # This is inherited from @dataclass.
            "__hash__": TestKnownToBeMissing,
            # This is inherited from @dataclass.
            "__replace__": TestKnownToBeMissing,
            # This is inherited from @dataclass.
            "__setattr__": TestKnownToBeMissing,
        },
    },
    "betty/fetch/static.py": TestKnownToBeMissing,
    "betty/gramps/error.py": TestKnownToBeMissing,
    "betty/gramps/loader.py": {
        # This is checked statically.
        "GrampsEntityReference": TestKnownToBeMissing,
        # This is an enum.
        "GrampsEntityType": TestKnownToBeMissing,
        # This is an empty class.
        "GrampsFileNotFound": TestKnownToBeMissing,
        # This is an empty class.
        "GrampsLoaderError": TestKnownToBeMissing,
        # This is an empty class.
        "LoaderUsedAlready": TestKnownToBeMissing,
        # This is an empty class.
        "XPathError": TestKnownToBeMissing,
    },
    "betty/html.py": TestKnownToBeMissing,
    "betty/jinja2/__init__.py": {
        "context_job_context": TestKnownToBeMissing,
        "context_localizer": TestKnownToBeMissing,
        "context_project": TestKnownToBeMissing,
        "Environment": TestKnownToBeMissing,
    },
    "betty/jinja2/filter.py": {
        "filter_hashid": TestKnownToBeMissing,
        "filter_json": TestKnownToBeMissing,
        "filter_localize": TestKnownToBeMissing,
        "filter_localized_url": TestKnownToBeMissing,
        "filter_negotiate_dateds": TestKnownToBeMissing,
        "filter_negotiate_localizeds": TestKnownToBeMissing,
        "filter_public_css": TestKnownToBeMissing,
        "filter_public_js": TestKnownToBeMissing,
        "filter_static_url": TestKnownToBeMissing,
        # This is covered statically.
        "filters": TestKnownToBeMissing,
    },
    "betty/jinja2/test.py": {
        "test_date_range": TestKnownToBeMissing,
        "test_end_of_life_event": TestKnownToBeMissing,
        "test_has_file_references": TestKnownToBeMissing,
        "test_has_links": TestKnownToBeMissing,
        "test_linked_data_dumpable": TestKnownToBeMissing,
        "test_start_of_life_event": TestKnownToBeMissing,
        "test_user_facing_entity": TestKnownToBeMissing,
        # This is covered statically.
        "tests": TestKnownToBeMissing,
    },
    "betty/json/linked_data.py": TestKnownToBeMissing,
    "betty/locale/__init__.py": {
        "get_data": TestKnownToBeMissing,
        "get_display_name": TestKnownToBeMissing,
        "LocaleNotFoundError": TestKnownToBeMissing,
        "to_babel_identifier": TestKnownToBeMissing,
        "to_locale": TestKnownToBeMissing,
    },
    "betty/locale/error.py": {
        "InvalidLocale": TestKnownToBeMissing,
        # This is an interface.
        "LocaleError": TestKnownToBeMissing,
        "LocaleNotFound": TestKnownToBeMissing,
    },
    "betty/locale/babel.py": {
        "run_babel": TestKnownToBeMissing,
    },
    "betty/locale/translation.py": {
        "find_source_files": TestKnownToBeMissing,
        "new_dev_translation": TestKnownToBeMissing,
        "new_project_translation": TestKnownToBeMissing,
        "new_extension_translation": TestKnownToBeMissing,
        "update_dev_translations": TestKnownToBeMissing,
        "update_project_translations": TestKnownToBeMissing,
        "update_extension_translations": TestKnownToBeMissing,
    },
    "betty/locale/localizable/__init__.py": {
        "call": TestKnownToBeMissing,
        "format": TestKnownToBeMissing,
        "gettext": TestKnownToBeMissing,
        # This is an interface.
        "Localizable": TestKnownToBeMissing,
        "ngettext": TestKnownToBeMissing,
        "npgettext": TestKnownToBeMissing,
        "pgettext": TestKnownToBeMissing,
        # This is an internal base class.
        "StaticTranslationsLocalizableAttr": TestKnownToBeMissing,
    },
    "betty/media_type/__init__.py": {
        # This is an empty class.
        "InvalidMediaType": TestKnownToBeMissing,
    },
    # This contains static definitions only.
    "betty/media_type/media_types.py": TestKnownToBeMissing,
    "betty/model/__init__.py": {
        "unalias": TestKnownToBeMissing,
        "Entity": TestKnownToBeMissing,
        "GeneratedEntityId": TestKnownToBeMissing,
        # This is an interface.
        "UserFacingEntity": TestKnownToBeMissing,
    },
    "betty/model/association.py": {
        "BidirectionalToOne": {
            # This is covered by a different test method.
            "__set__": TestKnownToBeMissing,
        },
        "BidirectionalToZeroOrOne": {
            # This is covered by a different test method.
            "__set__": TestKnownToBeMissing,
        },
        "resolve": TestKnownToBeMissing,
        # This is an abstract class.
        "ToManyResolver": TestKnownToBeMissing,
        # This is an abstract class.
        "ToOneResolver": TestKnownToBeMissing,
        # This is an abstract class.
        "ToZeroOrOneResolver": TestKnownToBeMissing,
    },
    "betty/model/collections.py": {
        "EntityCollection": TestKnownToBeMissing,
        "MultipleTypesEntityCollection": {
            "__iter__": TestKnownToBeMissing,
            "__len__": TestKnownToBeMissing,
            "clear": TestKnownToBeMissing,
        },
        "SingleTypeEntityCollection": {
            "__iter__": TestKnownToBeMissing,
            "__len__": TestKnownToBeMissing,
        },
        "record_added": TestKnownToBeMissing,
    },
    "betty/model/graph.py": {
        "EntityGraphBuilder": {
            "add_association": TestKnownToBeMissing,
            "add_entity": TestKnownToBeMissing,
        },
    },
    "betty/ancestry/__init__.py": {
        "Place": {
            "associated_files": TestKnownToBeMissing,
        },
    },
    "betty/ancestry/date.py": {
        "HasDate": {
            # This is static.
            "dated_linked_data_contexts": TestKnownToBeMissing,
        },
    },
    "betty/ancestry/event.py": {
        "Event": {
            # This is static.
            "dated_linked_data_contexts": TestKnownToBeMissing,
        },
    },
    # This contains static items only.
    "betty/ancestry/event_type/__init__.py": TestKnownToBeMissing,
    "betty/ancestry/event_type/event_types.py": {
        # This is an abstract class.
        "CreatableDerivableEventType": TestKnownToBeMissing,
        # This is an abstract class.
        "CreatableEventType": TestKnownToBeMissing,
        # This is an abstract class.
        "DerivableEventType": TestKnownToBeMissing,
        # This is an abstract class.
        "DuringLifeEventType": TestKnownToBeMissing,
        # This is an abstract class.
        "EndOfLifeEventType": TestKnownToBeMissing,
        # This is an abstract class.
        "FinalDispositionEventType": TestKnownToBeMissing,
        # This is an abstract class.
        "PostDeathEventType": TestKnownToBeMissing,
        # This is an abstract class.
        "PreBirthEventType": TestKnownToBeMissing,
        # This is an abstract class.
        "StartOfLifeEventType": TestKnownToBeMissing,
    },
    # This contains an abstract class and a static value only.
    "betty/ancestry/gender/__init__.py": TestKnownToBeMissing,
    # This contains an abstract class and a static value only.
    "betty/ancestry/place_type/__init__.py": TestKnownToBeMissing,
    # This contains an abstract class and a static value only.
    "betty/ancestry/presence_role/__init__.py": TestKnownToBeMissing,
    # This contains an abstract class and a static value only.
    "betty/copyright_notice/__init__.py": TestKnownToBeMissing,
    # This contains an abstract class and a static value only.
    "betty/license/__init__.py": TestKnownToBeMissing,
    "betty/path.py": TestKnownToBeMissing,
    "betty/plugin/__init__.py": {
        "Plugin": {
            # This is an interface method.
            "plugin_id": TestKnownToBeMissing,
            # This is an interface method.
            "plugin_label": TestKnownToBeMissing,
        },
        "ShorthandPluginBase": TestKnownToBeMissing,
        # This is a base/sentinel class.
        "PluginError": TestKnownToBeMissing,
        "PluginRepository": {
            # This is an interface method.
            "__aiter__": TestKnownToBeMissing,
            # This is an interface method.
            "get": TestKnownToBeMissing,
        },
    },
    "betty/plugin/assertion.py": {
        "assert_plugin": TestKnownToBeMissing,
    },
    "betty/plugin/config.py": {
        # This is tested as part of PluginConfigurationPluginConfigurationMapping.
        "PluginConfigurationMapping": TestKnownToBeMissing,
    },
    "betty/plugin/lazy.py": TestKnownToBeMissing,
    "betty/privacy/__init__.py": {
        # This is an enum.
        "Privacy": TestKnownToBeMissing,
    },
    "betty/privacy/privatizer.py": {
        "Privatizer": {
            "has_expired": TestKnownToBeMissing,
        },
    },
    "betty/project/extension/__init__.py": {
        "ConfigurableExtension": TestKnownToBeMissing,
        "CyclicDependencyError": TestKnownToBeMissing,
        "Dependencies": TestKnownToBeMissing,
        # This is an empty class.
        "ExtensionError": TestKnownToBeMissing,
        # This is an interface.
        "Extensions": TestKnownToBeMissing,
        # This is an empty class.
        "ExtensionTypeError": TestKnownToBeMissing,
        "ExtensionTypeInvalidError": TestKnownToBeMissing,
        # This is an empty class.
        "Theme": TestKnownToBeMissing,
    },
    "betty/project/extension/cotton_candy/__init__.py": {
        "person_descendant_families": TestKnownToBeMissing,
        "person_timeline_events": TestKnownToBeMissing,
    },
    "betty/project/extension/cotton_candy/config.py": {
        "CottonCandyConfiguration": {
            "update": TestKnownToBeMissing,
            "featured_entities": TestKnownToBeMissing,
            "link_active_color": TestKnownToBeMissing,
            "link_inactive_color": TestKnownToBeMissing,
            "primary_active_color": TestKnownToBeMissing,
            "primary_inactive_color": TestKnownToBeMissing,
        },
    },
    "betty/project/extension/demo/__init__.py": {
        "DemoServer": {
            "public_url": TestKnownToBeMissing,
            "start": TestKnownToBeMissing,
            "stop": TestKnownToBeMissing,
        },
    },
    "betty/project/extension/gramps/config.py": {
        "FamilyTreeConfiguration": {
            "file_path": TestKnownToBeMissing,
        },
        "GrampsConfiguration": {
            "family_trees": TestKnownToBeMissing,
        },
    },
    "betty/project/extension/privatizer/__init__.py": {
        "Privatizer": {
            "privatize": TestKnownToBeMissing,
        },
    },
    "betty/project/extension/webpack/__init__.py": {
        "PrebuiltAssetsRequirement": {
            "summary": TestKnownToBeMissing,
        },
        "Webpack": {
            "new_context_vars": TestKnownToBeMissing,
        },
        # This is an interface.
        "WebpackEntryPointProvider": TestKnownToBeMissing,
    },
    "betty/project/extension/webpack/build.py": {
        "webpack_build_id": TestKnownToBeMissing,
    },
    "betty/project/extension/webpack/jinja2/__init__.py": TestKnownToBeMissing,
    "betty/project/extension/webpack/jinja2/filter.py": TestKnownToBeMissing,
    "betty/project/extension/wikipedia/config.py": {
        "WikipediaConfiguration": {
            "populate_images": TestKnownToBeMissing,
        },
    },
    # This contains a single abstract class.
    "betty/project/factory.py": TestKnownToBeMissing,
    "betty/project/load.py": {
        # This is an empty class.
        "LoadAncestryEvent": TestKnownToBeMissing,
        # This is an empty class.
        "PostLoadAncestryEvent": TestKnownToBeMissing,
    },
    "betty/render.py": TestKnownToBeMissing,
    "betty/repr.py": TestKnownToBeMissing,
    "betty/requirement.py": {
        "Requirement": {
            # This is an abstract method.
            "details": TestKnownToBeMissing,
            # This is an abstract method.
            "is_met": TestKnownToBeMissing,
            # This is an abstract method.
            "reduce": TestKnownToBeMissing,
            # This is an abstract method.
            "summary": TestKnownToBeMissing,
        },
    },
    "betty/serde/__init__.py": {
        # This is an interface.
        "Format": TestKnownToBeMissing,
        "FormatError": TestKnownToBeMissing,
        "FormatStr": TestKnownToBeMissing,
    },
    "betty/serde/dump.py": TestKnownToBeMissing,
    "betty/serde/format/__init__.py": {
        # This is an abstract class.
        "Format": TestKnownToBeMissing,
        # This is an empty class.
        "FormatError": TestKnownToBeMissing,
    },
    # This contains abstract classes only.
    "betty/serde/load.py": TestKnownToBeMissing,
    "betty/serve.py": {
        "ProjectServer": TestKnownToBeMissing,
        "BuiltinProjectServer": {
            # This method is covered by another test method.
            "public_url": TestKnownToBeMissing,
            # This method is covered by another test method.
            "start": TestKnownToBeMissing,
            # This method is covered by another test method.
            "stop": TestKnownToBeMissing,
        },
        "BuiltinServer": TestKnownToBeMissing,
        "NoPublicUrlBecauseServerNotStartedError": TestKnownToBeMissing,
        # This is an empty class.
        "OsError": TestKnownToBeMissing,
        # This is an interface.
        "Server": TestKnownToBeMissing,
        # This is an empty class.
        "ServerNotStartedError": TestKnownToBeMissing,
    },
    # We do not test our test utilities.
    **{
        str(path): TestKnownToBeMissing
        for path in (Path("betty") / "test_utils").rglob("**/*.py")
    },
    "betty/typing.py": {
        "Void": TestKnownToBeMissing,
    },
    "betty/url/__init__.py": {
        # This is an abstract base class.
        "LocalizedUrlGenerator": TestKnownToBeMissing,
        # This is an abstract base class.
        "StaticUrlGenerator": TestKnownToBeMissing,
        # This is an empty class.
        "UnsupportedResource": TestKnownToBeMissing,
    },
    "betty/warnings.py": {
        # This is an empty class.
        "BettyDeprecationWarning": TestKnownToBeMissing,
    },
    "betty/wikipedia/__init__.py": {
        # This is a dataclass.
        "Image": TestKnownToBeMissing,
        # This is an empty class.
        "NotAPageError": TestKnownToBeMissing,
        "Summary": {
            # This is inherited from @dataclass.
            "__eq__": TestKnownToBeMissing,
            # This is inherited from @dataclass.
            "__delattr__": TestKnownToBeMissing,
            # This is inherited from @dataclass.
            "__hash__": TestKnownToBeMissing,
            # This is inherited from @dataclass.
            "__replace__": TestKnownToBeMissing,
            # This is inherited from @dataclass.
            "__setattr__": TestKnownToBeMissing,
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

        for directory_path, _, file_names in walk(str((ROOT_DIRECTORY_PATH / "betty"))):
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
        src_function: Callable[..., Any] & _Importable,
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
        expected_test_class_name = (
            f"Test{self._src_class.__name__[0].upper()}{self._src_class.__name__[1:]}"
        )

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
