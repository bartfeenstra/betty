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
from enum import Enum
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


class MissingReason(Enum):
    """
    Reasons why test coverage is missing.
    """

    ABSTRACT = "This testable is abstract"
    INTERNAL = "This testable is internal to Betty itself"
    SHOULD_BE_COVERED = "This testable should be covered by a test but isn't yet"
    STATIC_CONTENT_ONLY = "This testable has no testable components"
    COVERED_ELSEWHERE = "This testable is covered by another test"
    DATACLASS = "This testable is inherited from @dataclass"
    ENUM = "This testable is inherited from Enum"
    TYPED_DICT = "This testable is inherited from TypedDict"
    PROTOCOL = "This testable is a Protocol"


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
    "betty/app/factory.py": MissingReason.ABSTRACT,
    "betty/assertion/__init__.py": {
        "Field": MissingReason.INTERNAL,
        "OptionalField": MissingReason.DATACLASS,
        "RequiredField": MissingReason.DATACLASS,
    },
    "betty/assertion/error.py": {
        "AssertionContext": MissingReason.ABSTRACT,
        "AssertionFailed": {
            "contexts": MissingReason.COVERED_ELSEWHERE,
        },
        "AssertionFailedGroup": {
            "invalid": MissingReason.COVERED_ELSEWHERE,
        },
    },
    "betty/cache/__init__.py": {
        "Cache": MissingReason.ABSTRACT,
        "CacheItem": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/cache/_base.py": MissingReason.COVERED_ELSEWHERE,
    "betty/cli/__init__.py": {
        "ContextAppObject": MissingReason.SHOULD_BE_COVERED,
        "ctx_app_object": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/cli/error.py": {
        "user_facing_error_to_bad_parameter": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/cli/commands/__init__.py": {
        "command": MissingReason.SHOULD_BE_COVERED,
        "Command": MissingReason.SHOULD_BE_COVERED,
        "CommandRepository": MissingReason.SHOULD_BE_COVERED,
        "parameter_callback": MissingReason.SHOULD_BE_COVERED,
        "project_option": MissingReason.SHOULD_BE_COVERED,
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
        "Ledger": MissingReason.SHOULD_BE_COVERED,
        "RateLimiter": {
            "__aenter__": MissingReason.SHOULD_BE_COVERED,
            "__aexit__": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/config/__init__.py": {
        "DefaultConfigurable": MissingReason.ABSTRACT,
    },
    "betty/config/collections/__init__.py": MissingReason.ABSTRACT,
    "betty/contextlib.py": {
        "SynchronizedContextManager": {
            "__enter__": MissingReason.SHOULD_BE_COVERED,
            "__exit__": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/core.py": {
        "Shutdownable": MissingReason.ABSTRACT,
        "ShutdownCallbackKwargs": MissingReason.TYPED_DICT,
        "ShutdownStack": {
            "append": MissingReason.COVERED_ELSEWHERE,
        },
    },
    "betty/date.py": {
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
    "betty/error.py": MissingReason.SHOULD_BE_COVERED,
    "betty/event_dispatcher.py": {
        "Event": MissingReason.ABSTRACT,
        "EventHandlerRegistry": {
            "handlers": MissingReason.COVERED_ELSEWHERE,
        },
    },
    "betty/factory.py": {
        "Factory": MissingReason.PROTOCOL,
        "IndependentFactory": MissingReason.ABSTRACT,
        "TargetFactory": MissingReason.ABSTRACT,
    },
    "betty/fetch/__init__.py": {
        "Fetcher": MissingReason.ABSTRACT,
        "FetchResponse": {
            "__eq__": MissingReason.DATACLASS,
            "__delattr__": MissingReason.DATACLASS,
            "__hash__": MissingReason.DATACLASS,
            "__replace__": MissingReason.DATACLASS,
            "__setattr__": MissingReason.DATACLASS,
        },
    },
    "betty/fetch/static.py": MissingReason.SHOULD_BE_COVERED,
    "betty/gramps/error.py": MissingReason.SHOULD_BE_COVERED,
    "betty/gramps/loader.py": {
        "GrampsEntityReference": MissingReason.SHOULD_BE_COVERED,
        "GrampsEntityType": MissingReason.ENUM,
        "GrampsFileNotFound": MissingReason.STATIC_CONTENT_ONLY,
        "LoaderUsedAlready": MissingReason.STATIC_CONTENT_ONLY,
        "XPathError": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/html.py": {
        "CssProvider": MissingReason.ABSTRACT,
        "JsProvider": MissingReason.ABSTRACT,
    },
    "betty/jinja2/__init__.py": {
        "context_job_context": MissingReason.SHOULD_BE_COVERED,
        "context_localizer": MissingReason.SHOULD_BE_COVERED,
        "context_project": MissingReason.SHOULD_BE_COVERED,
        "Environment": {},
    },
    "betty/jinja2/filter.py": {
        "filters": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/jinja2/test.py": {
        "tests": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/json/linked_data.py": MissingReason.SHOULD_BE_COVERED,
    "betty/locale/__init__.py": {
        "get_data": MissingReason.SHOULD_BE_COVERED,
        "get_display_name": MissingReason.SHOULD_BE_COVERED,
        "LocaleNotFoundError": MissingReason.SHOULD_BE_COVERED,
        "to_babel_identifier": MissingReason.SHOULD_BE_COVERED,
        "to_locale": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/locale/error.py": {
        "InvalidLocale": MissingReason.SHOULD_BE_COVERED,
        "LocaleError": MissingReason.STATIC_CONTENT_ONLY,
        "LocaleNotFound": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/locale/babel.py": {
        "run_babel": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/locale/translation.py": {
        "find_source_files": MissingReason.SHOULD_BE_COVERED,
        "new_dev_translation": MissingReason.SHOULD_BE_COVERED,
        "new_project_translation": MissingReason.SHOULD_BE_COVERED,
        "new_extension_translation": MissingReason.SHOULD_BE_COVERED,
        "update_dev_translations": MissingReason.SHOULD_BE_COVERED,
        "update_project_translations": MissingReason.SHOULD_BE_COVERED,
        "update_extension_translations": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/locale/localizable/__init__.py": {
        "call": MissingReason.SHOULD_BE_COVERED,
        "format": MissingReason.SHOULD_BE_COVERED,
        "gettext": MissingReason.SHOULD_BE_COVERED,
        "Localizable": MissingReason.ABSTRACT,
        "ngettext": MissingReason.SHOULD_BE_COVERED,
        "npgettext": MissingReason.SHOULD_BE_COVERED,
        "pgettext": MissingReason.SHOULD_BE_COVERED,
        "StaticTranslationsLocalizableAttr": MissingReason.INTERNAL,
    },
    "betty/media_type/__init__.py": {
        "InvalidMediaType": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/media_type/media_types.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/model/__init__.py": {
        "Entity": MissingReason.SHOULD_BE_COVERED,
        "NonPersistentId": MissingReason.SHOULD_BE_COVERED,
        "UserFacingEntity": MissingReason.ABSTRACT,
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
        "EntityCollection": MissingReason.SHOULD_BE_COVERED,
        "MultipleTypesEntityCollection": {
            "__iter__": MissingReason.SHOULD_BE_COVERED,
            "__len__": MissingReason.SHOULD_BE_COVERED,
            "clear": MissingReason.SHOULD_BE_COVERED,
        },
        "SingleTypeEntityCollection": {
            "__iter__": MissingReason.SHOULD_BE_COVERED,
            "__len__": MissingReason.SHOULD_BE_COVERED,
        },
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
    "betty/ancestry/event_type/__init__.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/ancestry/event_type/event_types.py": {
        "CreatableDerivableEventType": MissingReason.ABSTRACT,
        "CreatableEventType": MissingReason.ABSTRACT,
        "DerivableEventType": MissingReason.ABSTRACT,
        "DuringLifeEventType": MissingReason.ABSTRACT,
        "EndOfLifeEventType": MissingReason.ABSTRACT,
        "FinalDispositionEventType": MissingReason.ABSTRACT,
        "PostDeathEventType": MissingReason.ABSTRACT,
        "PreBirthEventType": MissingReason.ABSTRACT,
        "StartOfLifeEventType": MissingReason.ABSTRACT,
    },
    "betty/ancestry/gender/__init__.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/ancestry/place_type/__init__.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/ancestry/presence_role/__init__.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/copyright_notice/__init__.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/license/__init__.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/path.py": MissingReason.SHOULD_BE_COVERED,
    "betty/multiprocessing.py": MissingReason.STATIC_CONTENT_ONLY,
    "betty/plugin/__init__.py": {
        "DependentPlugin": MissingReason.ABSTRACT,
        "OrderedPlugin": MissingReason.ABSTRACT,
        "Plugin": {
            "plugin_id": MissingReason.ABSTRACT,
            "plugin_label": MissingReason.ABSTRACT,
        },
        "PluginError": MissingReason.ABSTRACT,
        "PluginRepository": {
            "__aiter__": MissingReason.ABSTRACT,
            "get": MissingReason.ABSTRACT,
        },
        "ShorthandPluginBase": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/plugin/assertion.py": {
        "assert_plugin": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/plugin/config.py": {
        # This is tested as part of PluginConfigurationPluginConfigurationMapping.
        "PluginConfigurationMapping": MissingReason.COVERED_ELSEWHERE,
    },
    "betty/plugin/lazy.py": MissingReason.SHOULD_BE_COVERED,
    "betty/privacy/__init__.py": {
        "Privacy": MissingReason.ENUM,
    },
    "betty/privacy/privatizer.py": {
        "Privatizer": {
            "has_expired": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/project/extension/__init__.py": {
        "ConfigurableExtension": MissingReason.SHOULD_BE_COVERED,
        "Dependencies": MissingReason.SHOULD_BE_COVERED,
        "ExtensionError": MissingReason.STATIC_CONTENT_ONLY,
        "ExtensionTypeError": MissingReason.STATIC_CONTENT_ONLY,
        "ExtensionTypeInvalidError": MissingReason.SHOULD_BE_COVERED,
        "Theme": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/project/extension/cotton_candy/__init__.py": {
        "person_descendant_families": MissingReason.SHOULD_BE_COVERED,
        "person_timeline_events": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/project/extension/cotton_candy/config.py": {
        "CottonCandyConfiguration": {
            "featured_entities": MissingReason.SHOULD_BE_COVERED,
            "link_active_color": MissingReason.SHOULD_BE_COVERED,
            "link_inactive_color": MissingReason.SHOULD_BE_COVERED,
            "primary_active_color": MissingReason.SHOULD_BE_COVERED,
            "primary_inactive_color": MissingReason.SHOULD_BE_COVERED,
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
        "FamilyTreeConfiguration": {
            "file_path": MissingReason.SHOULD_BE_COVERED,
        },
        "GrampsConfiguration": {
            "family_trees": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/project/extension/privatizer/__init__.py": {
        "Privatizer": {
            "privatize": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/project/extension/webpack/__init__.py": {
        "PrebuiltAssetsRequirement": {
            "summary": MissingReason.SHOULD_BE_COVERED,
        },
        "Webpack": {
            "new_context_vars": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/project/extension/webpack/build.py": {
        "EntryPointProvider": MissingReason.ABSTRACT,
        "webpack_build_id": MissingReason.SHOULD_BE_COVERED,
    },
    "betty/project/extension/webpack/jinja2/__init__.py": MissingReason.SHOULD_BE_COVERED,
    "betty/project/extension/webpack/jinja2/filter.py": MissingReason.SHOULD_BE_COVERED,
    "betty/project/extension/wikipedia/config.py": {
        "WikipediaConfiguration": {
            "populate_images": MissingReason.SHOULD_BE_COVERED,
        },
    },
    "betty/project/factory.py": MissingReason.ABSTRACT,
    "betty/project/load.py": {
        "LoadAncestryEvent": MissingReason.STATIC_CONTENT_ONLY,
        "PostLoadAncestryEvent": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/render.py": {
        "Renderer": MissingReason.ABSTRACT,
    },
    "betty/repr.py": MissingReason.SHOULD_BE_COVERED,
    "betty/requirement.py": {
        "Requirement": {
            "details": MissingReason.ABSTRACT,
            "is_met": MissingReason.ABSTRACT,
            "reduce": MissingReason.ABSTRACT,
            "summary": MissingReason.ABSTRACT,
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
            "start": MissingReason.COVERED_ELSEWHERE,
            "stop": MissingReason.COVERED_ELSEWHERE,
        },
        "BuiltinServer": MissingReason.SHOULD_BE_COVERED,
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
        "LocalizedUrlGenerator": MissingReason.ABSTRACT,
        "StaticUrlGenerator": MissingReason.ABSTRACT,
        "UnsupportedResource": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/warnings.py": {
        "BettyDeprecationWarning": MissingReason.STATIC_CONTENT_ONLY,
    },
    "betty/wikipedia/__init__.py": {
        "Image": MissingReason.DATACLASS,
        "NotAPageError": MissingReason.STATIC_CONTENT_ONLY,
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
                module_file_path: MissingReason.SHOULD_BE_COVERED
                for module_file_path in self._get_coveragerc_ignore_modules()
            },
        }

    async def _test_python_file(self, file_path: Path) -> AsyncIterable[str]:
        # Skip tests.
        if ROOT_DIRECTORY_PATH / "betty" / "tests" in file_path.parents:
            return
        if ROOT_DIRECTORY_PATH / "betty" / "tests_playwright" in file_path.parents:
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
                            _ModuleClassIgnore, self._ignore.get(src_class.__name__, {})
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
            if isinstance(self._ignore, MissingReason):
                yield f"The source function {self._src_module_name}.{self._src_function.__name__} has a matching test class at {self._test_classes[expected_test_class_name].__module__}.{self._test_classes[expected_test_class_name].__name__}, which was unexpectedly declared as known to be missing."
            return

        if isinstance(self._ignore, MissingReason):
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
            if isinstance(ignore, MissingReason):
                formatted_test_members = ", ".join(
                    (f"{test_member.__name__}()" for test_member in test_members)
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
        test_class = getattr(module, "TestSrc", None)
        sut = _ModuleClassCoverageTester(
            module.Src,  # type: ignore[attr-defined]
            (test_class,) if test_class else (),
            module.__name__,
            module.__name__,
            ignore,
        )
        assert (len([error async for error in sut.test()]) > 0) is errors_expected
