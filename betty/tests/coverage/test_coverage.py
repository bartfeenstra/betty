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
from glob import glob
from importlib import import_module
from inspect import getmembers, isfunction, isclass
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
            "discover_extension_types": TestKnownToBeMissing,
            "start": TestKnownToBeMissing,
            "stop": TestKnownToBeMissing,
        },
        "AppConfiguration": TestKnownToBeMissing,
    },
    "betty/app/extension/__init__.py": {
        "ConfigurableExtension": TestKnownToBeMissing,
        "CyclicDependencyError": TestKnownToBeMissing,
        "Dependencies": TestKnownToBeMissing,
        "Dependents": TestKnownToBeMissing,
        "Extension": {
            "disable_requirement": TestKnownToBeMissing,
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
    "betty/config.py": {
        "Configurable": TestKnownToBeMissing,
        "Configuration": TestKnownToBeMissing,
        "ConfigurationCollection": TestKnownToBeMissing,
        "ConfigurationMapping": {
            "replace": TestKnownToBeMissing,
        },
        "FileBasedConfiguration": {
            "read": TestKnownToBeMissing,
            "write": TestKnownToBeMissing,
        },
    },
    "betty/deriver.py": {
        # This is an enum.
        "Derivation": TestKnownToBeMissing
    },
    "betty/dispatch.py": TestKnownToBeMissing,
    "betty/error.py": TestKnownToBeMissing,
    "betty/extension/__init__.py": TestKnownToBeMissing,
    "betty/extension/cotton_candy/__init__.py": {
        "person_descendant_families": TestKnownToBeMissing,
        "person_timeline_events": TestKnownToBeMissing,
        "CottonCandy": TestKnownToBeMissing,
    },
    "betty/extension/gramps/config.py": {
        "FamilyTreeConfigurationSequence": TestKnownToBeMissing,
    },
    "betty/extension/nginx/docker.py": TestKnownToBeMissing,
    "betty/extension/privatizer/__init__.py": {
        "Privatizer": {
            "privatize": TestKnownToBeMissing,
        },
    },
    "betty/extension/webpack/__init__.py": {
        "Webpack": {
            "build_requirement": TestKnownToBeMissing,
        },
        # This is an interface.
        "WebpackEntrypointProvider": TestKnownToBeMissing,
    },
    "betty/extension/webpack/build.py": {
        "webpack_build_id": TestKnownToBeMissing,
    },
    "betty/extension/webpack/jinja2/__init__.py": TestKnownToBeMissing,
    "betty/extension/webpack/jinja2/filter.py": TestKnownToBeMissing,
    "betty/fs.py": {
        "FileSystem": {
            "clear": TestKnownToBeMissing,
            "prepend": TestKnownToBeMissing,
        },
    },
    "betty/functools.py": {
        "filter_suppress": TestKnownToBeMissing,
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
        "BettyPrimaryWindow": {
            "new_project": TestKnownToBeMissing,
            "open_application_configuration": TestKnownToBeMissing,
            "open_project": TestKnownToBeMissing,
            "report_bug": TestKnownToBeMissing,
            "request_feature": TestKnownToBeMissing,
        },
    },
    "betty/gui/error.py": TestKnownToBeMissing,
    "betty/gui/locale.py": TestKnownToBeMissing,
    "betty/gui/logging.py": TestKnownToBeMissing,
    "betty/gui/model.py": TestKnownToBeMissing,
    "betty/gui/window.py": TestKnownToBeMissing,
    "betty/importlib.py": {
        "fully_qualified_type_name": TestKnownToBeMissing,
    },
    "betty/html.py": TestKnownToBeMissing,
    "betty/jinja2/__init__.py": TestKnownToBeMissing,
    "betty/jinja2/filter.py": TestKnownToBeMissing,
    "betty/jinja2/test.py": TestKnownToBeMissing,
    "betty/json/linked_data.py": TestKnownToBeMissing,
    "betty/json/schema.py": {
        "add_property": TestKnownToBeMissing,
        "ref_json_schema": TestKnownToBeMissing,
        "ref_locale": TestKnownToBeMissing,
        "Schema": {
            "validate": TestKnownToBeMissing,
        },
    },
    "betty/load.py": TestKnownToBeMissing,
    "betty/locale.py": {
        "Date": {
            "datey_dump_linked_data": TestKnownToBeMissing,
        },
        "DateRange": {
            "datey_dump_linked_data": TestKnownToBeMissing,
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
            "coverage": TestKnownToBeMissing,
            "get": TestKnownToBeMissing,
            "get_negotiated": TestKnownToBeMissing,
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
    "betty/model/__init__.py": {
        "record_added": TestKnownToBeMissing,
        "unalias": TestKnownToBeMissing,
        "AliasedEntity": TestKnownToBeMissing,
        "BidirectionalEntityTypeAssociation": TestKnownToBeMissing,
        "BidirectionalToManyEntityTypeAssociation": TestKnownToBeMissing,
        "BidirectionalToOneEntityTypeAssociation": TestKnownToBeMissing,
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
        "HasLinksEntity": TestKnownToBeMissing,
        # This is static.
        "Organizer": TestKnownToBeMissing,
        "PresenceRole": TestKnownToBeMissing,
        "Privacy": TestKnownToBeMissing,
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
    "betty/media_type.py": {
        # This is an empty class.
        "InvalidMediaType": TestKnownToBeMissing,
    },
    "betty/path.py": TestKnownToBeMissing,
    "betty/privatizer.py": {
        "Privatizer": {
            "has_expired": TestKnownToBeMissing,
        },
    },
    "betty/project.py": {
        "ExtensionConfigurationMapping": {
            "disable": TestKnownToBeMissing,
            "enable": TestKnownToBeMissing,
        },
        "Project": TestKnownToBeMissing,
        "ProjectConfiguration": {
            "localize_www_directory_path": TestKnownToBeMissing,
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
            "raised": TestKnownToBeMissing,
        },
        "SerdeErrorCollection": {
            "append": TestKnownToBeMissing,
            "assert_valid": TestKnownToBeMissing,
        },
    },
    "betty/serde/format.py": {
        # This is an interface.
        "Format": TestKnownToBeMissing,
        "FormatRepository": TestKnownToBeMissing,
        "FormatStr": TestKnownToBeMissing,
    },
    "betty/serde/load.py": {
        "Asserter": {
            "assert_assertions": TestKnownToBeMissing,
            "assert_entity_type": TestKnownToBeMissing,
            "assert_extension_type": TestKnownToBeMissing,
            "assert_locale": TestKnownToBeMissing,
            "assert_none": TestKnownToBeMissing,
            "assert_or": TestKnownToBeMissing,
            "assert_setattr": TestKnownToBeMissing,
        },
        # This is an empty class.
        "AssertionFailed": TestKnownToBeMissing,
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
        omit = coveragerc.get("run", "omit").split("\n")
        for omit_pattern in omit:
            for module_path_str in glob(omit_pattern, recursive=True):
                if not module_path_str.endswith(".py"):
                    continue
                module_path = Path(module_path_str).resolve()
                if not module_path.is_file():
                    continue
                yield module_path

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
        if True in map(lambda x: x.startswith("_"), self._src_module_name.split(".")):
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
                            _ModuleClassIgnore, self._ignore.get(src_class.__name__, {})  # type: ignore[union-attr]
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

    def _get_module_data(self, module_path: Path) -> tuple[
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
            for error in self._test_functions(
                self._test_classes[expected_test_class_name],
                self._ignore,  # type: ignore[arg-type]
            ):
                yield error
            return

        if self._ignore is TestKnownToBeMissing:
            return

        yield f"Failed to find the test class {self._test_module_name}.{expected_test_class_name} for the source class {self._src_module_name}.{self._src_class.__name__}."

    def _test_functions(
        self, test_class: type, ignore: _ModuleClassExistsIgnore
    ) -> Iterable[str]:
        src_base_function_names = [
            name
            for src_base_class in self._src_class.__bases__
            for name, _ in getmembers(src_base_class, isfunction)
        ]
        src_functions = [
            function
            for name, function in getmembers(self._src_class, isfunction)
            if name not in src_base_function_names and not name.startswith("_")
        ]
        for src_function in src_functions:
            yield from self._test_function(
                test_class, src_function, ignore.get(src_function.__name__, None)
            )

    def _test_function(
        self,
        test_class: type,
        src_function: Callable[..., Any],
        ignore: _ModuleFunctionIgnore,
    ) -> Iterable[str]:
        expected_test_function_name = f"test_{src_function.__name__}"
        expected_test_function_name_prefix = f"{expected_test_function_name}_"
        test_functions = [
            function
            for name, function in getmembers(test_class, isfunction)
            if name == expected_test_function_name
            or name.startswith(expected_test_function_name_prefix)
        ]
        if test_functions:
            if ignore is TestKnownToBeMissing:
                formatted_test_functions = ", ".join(
                    map(
                        lambda test_function: f"{test_function.__name__}()",
                        test_functions,
                    )
                )
                yield f"The source function {self._src_class.__module__}.{self._src_class.__name__}.{src_function.__name__}() has (a) matching test method(s) {formatted_test_functions} in {test_class.__module__}.{test_class.__name__}, which was unexpectedly declared as known to be missing."
            return

        if ignore is TestKnownToBeMissing:
            return

        yield f"Failed to find a test method named {expected_test_function_name}() or any methods whose names start with `{expected_test_function_name_prefix}` in {self._test_module_name}.{test_class.__name__} for the source function {self._src_module_name}.{self._src_class.__name__}.{src_function.__name__}()."


class Test_ModuleCoverageTester:
    @pytest.mark.parametrize(
        "errors_expected, module, ignore",
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
        "errors_expected, module, ignore",
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
        "errors_expected, module, ignore",
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
