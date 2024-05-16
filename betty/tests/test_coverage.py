from _ast import Expr, Constant
from ast import parse, iter_child_nodes
from collections import defaultdict
from collections.abc import (
    Sequence,
    Iterator,
    Callable,
    Mapping,
    AsyncIterator,
    MutableMapping,
)
from configparser import ConfigParser
from glob import glob
from importlib import import_module
from inspect import getmembers, isfunction, isclass
from pathlib import Path

import aiofiles

from betty.fs import iterfiles, ROOT_DIRECTORY_PATH
from betty.string import snake_case_to_upper_camel_case


class TestModuleKnownToBeMissing:
    pass  # pragma: no cover


# Keys are paths to module files with ignore rules. These paths area relative to the project root directory.
# Values are either the type :py:class:`TestModuleKnownToBeMissing` as a value, or a set containing the names
# of the module's top-level functions and classes to ignore.
# This baseline MUST NOT be extended. It SHOULD decrease in size as more coverage is added to Betty over time.
_BASELINE: Mapping[str, set[str] | type[TestModuleKnownToBeMissing]] = {
    "betty/__init__.py": TestModuleKnownToBeMissing,
    "betty/_patch.py": TestModuleKnownToBeMissing,
    "betty/about.py": {
        "is_development",
        "is_stable",
        "report",
    },
    "betty/app/__init__.py": {
        "AppConfiguration",
    },
    "betty/app/extension/__init__.py": {
        "ConfigurableExtension",
        "CyclicDependencyError",
        "Dependencies",
        "Dependents",
        # This is an empty class.
        "ExtensionError",
        # This is an interface.
        "Extensions",
        # This is an empty class.
        "ExtensionTypeError",
        "ExtensionTypeImportError",
        "ExtensionTypeInvalidError",
        "discover_extension_types",
        "format_extension_type",
        "get_extension_type",
        "get_extension_type_by_extension",
        "get_extension_type_by_name",
        "get_extension_type_by_type",
        "ListExtensions",
        # This is an empty class.
        "Theme",
        # This is an interface.
        "UserFacingExtension",
    },
    # This is deprecated.
    "betty/app/extension/requirement.py": TestModuleKnownToBeMissing,
    "betty/asyncio.py": {
        "gather",
    },
    "betty/cache/__init__.py": {
        # This is an interface.
        "Cache",
        "CacheItem",
        # This is deprecated.
        "FileCache",
    },
    "betty/cache/_base.py": TestModuleKnownToBeMissing,
    "betty/classtools.py": TestModuleKnownToBeMissing,
    "betty/cli.py": {
        "app_command",
        # This is an interface.
        "CommandProvider",
        "global_command",
    },
    "betty/config.py": {
        "Configurable",
        "Configuration",
        "ConfigurationCollection",
    },
    "betty/deriver.py": {
        # This is an enum.
        "Derivation"
    },
    "betty/dispatch.py": TestModuleKnownToBeMissing,
    "betty/error.py": TestModuleKnownToBeMissing,
    "betty/extension/__init__.py": TestModuleKnownToBeMissing,
    "betty/extension/cotton_candy/__init__.py": {
        "person_descendant_families",
        "person_timeline_events",
        "CottonCandy",
    },
    "betty/extension/gramps/config.py": {
        "FamilyTreeConfigurationSequence",
    },
    "betty/extension/nginx/docker.py": TestModuleKnownToBeMissing,
    "betty/extension/webpack/__init__.py": {
        # This is an interface.
        "WebpackEntrypointProvider",
    },
    "betty/extension/webpack/build.py": {
        "webpack_build_id",
    },
    "betty/extension/webpack/jinja2/__init__.py": TestModuleKnownToBeMissing,
    "betty/extension/webpack/jinja2/filter.py": TestModuleKnownToBeMissing,
    "betty/functools.py": {
        "filter_suppress",
    },
    "betty/gramps/error.py": TestModuleKnownToBeMissing,
    "betty/gramps/loader.py": {
        "GrampsEntityReference",
        "GrampsEntityType",
        # This is an empty class.
        "GrampsFileNotFoundError",
        # This is an empty class.
        "GrampsLoadFileError",
        # This is an empty class.
        "XPathError",
    },
    "betty/generate.py": {
        "create_file",
        "create_html_resource",
        "create_json_resource",
        "GenerationContext",
        # This is an interface.
        "Generator",
        # This is deprecated.
        "getLogger",
    },
    "betty/gui/__init__.py": TestModuleKnownToBeMissing,
    "betty/gui/error.py": TestModuleKnownToBeMissing,
    "betty/gui/locale.py": TestModuleKnownToBeMissing,
    "betty/gui/logging.py": TestModuleKnownToBeMissing,
    "betty/gui/model.py": TestModuleKnownToBeMissing,
    "betty/gui/serve.py": TestModuleKnownToBeMissing,
    "betty/gui/text.py": TestModuleKnownToBeMissing,
    "betty/gui/window.py": TestModuleKnownToBeMissing,
    "betty/importlib.py": {
        "fully_qualified_type_name",
    },
    "betty/html.py": TestModuleKnownToBeMissing,
    "betty/jinja2/__init__.py": TestModuleKnownToBeMissing,
    "betty/jinja2/filter.py": TestModuleKnownToBeMissing,
    "betty/jinja2/test.py": TestModuleKnownToBeMissing,
    "betty/json/linked_data.py": TestModuleKnownToBeMissing,
    "betty/json/schema.py": {
        "add_property",
        "ref_json_schema",
        "ref_locale",
    },
    "betty/load.py": TestModuleKnownToBeMissing,
    "betty/locale.py": {
        "get_data",
        "get_display_name",
        # This is an empty class.
        "IncompleteDateError",
        "init_translation",
        "LocaleNotFoundError",
        # This is an interface.
        "Localizable",
        "Localized",
        "Localizer",
        "ref_date",
        "ref_date_range",
        "ref_datey",
        "Str",
        "run_babel",
        "to_babel_identifier",
        "to_locale",
        "update_translations",
    },
    "betty/model/__init__.py": {
        "record_added",
        "unalias",
        "AliasedEntity",
        "BidirectionalEntityTypeAssociation",
        "BidirectionalToManyEntityTypeAssociation",
        "BidirectionalToOneEntityTypeAssociation",
        "EntityCollection",
        # This is an empty class.
        "EntityTypeError",
        "EntityTypeImportError",
        "EntityTypeInvalidError",
        # This is an interface.
        "EntityTypeProvider",
        "GeneratedEntityId",
        "ToManyEntityTypeAssociation",
        "ToOneEntityTypeAssociation",
        # This is an interface.
        "UserFacingEntity",
    },
    "betty/model/ancestry.py": {
        "ref_link",
        "ref_link_collection",
        "ref_media_type",
        "ref_role",
        "resolve_privacy",
        # This is deprecated.
        "AnonymousCitation",
        # This is deprecated.
        "AnonymousSource",
        # This is static.
        "Attendee",
        # This is static.
        "Beneficiary",
        "Celebrant",
        "HasLinksEntity",
        # This is static.
        "Organizer",
        "PresenceRole",
        "Privacy",
        # This is static.
        "Speaker",
        # This is static.
        "Subject",
        # This is static.
        "Witness",
    },
    "betty/model/event_type.py": {
        "Adoption",
        "Baptism",
        "Birth",
        "Burial",
        "Conference",
        "Confirmation",
        "Correspondence",
        "CreatableDerivableEventType",
        "CreatableEventType",
        "Cremation",
        "DerivableEventType",
        "Divorce",
        "DivorceAnnouncement",
        "DuringLifeEventType",
        "Emigration",
        "EndOfLifeEventType",
        "Engagement",
        "EventTypeProvider",
        "FinalDispositionEventType",
        "Funeral",
        "Immigration",
        "Marriage",
        "MarriageAnnouncement",
        "Missing",
        "Occupation",
        "PostDeathEventType",
        "PreBirthEventType",
        "Residence",
        "Retirement",
        "StartOfLifeEventType",
        "UnknownEventType",
        "Will",
    },
    "betty/media_type.py": {
        # This is an empty class.
        "InvalidMediaType",
    },
    "betty/path.py": TestModuleKnownToBeMissing,
    "betty/project.py": {
        "Project",
    },
    "betty/render.py": TestModuleKnownToBeMissing,
    "betty/requirement.py": {
        "RequirementError",
    },
    "betty/serde/format.py": {
        # This is an interface.
        "Format",
        "FormatRepository",
        "FormatStr",
    },
    "betty/serde/load.py": {
        # This is an empty class.
        "AssertionFailed",
        "Assertions",
        "Fields",
        # This is an empty class.
        "FormatError",
        # This is an empty class.
        "LoadError",
        "OptionalField",
        "RequiredField",
    },
    "betty/serve.py": {
        "AppServer",
        "BuiltinAppServer",
        "NoPublicUrlBecauseServerNotStartedError",
        # This is an empty class.
        "OsError",
        # This is an interface.
        "Server",
        # This is an empty class.
        "ServerNotStartedError",
        # This is an interface.
        "ServerProvider",
    },
    "betty/serde/dump.py": TestModuleKnownToBeMissing,
    "betty/sphinx/extension/replacements.py": TestModuleKnownToBeMissing,
    "betty/url.py": {
        # This is an abstract base class.
        "LocalizedUrlGenerator",
        "StaticPathUrlGenerator",
        # This is an abstract base class.
        "StaticUrlGenerator",
    },
    "betty/warnings.py": TestModuleKnownToBeMissing,
    "betty/wikipedia.py": {
        "Image",
        # This is an empty class.
        "NotAPageError",
        # This is an empty class.
        "RetrievalError",
        # This is an empty class.
        "WikipediaError",
    },
}


class TestCoverage:
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

    def _module_path_to_name(self, relative_module_path: Path) -> str:
        module_name_parts = relative_module_path.parent.parts
        if relative_module_path.name != "__init__.py":
            module_name_parts = (*module_name_parts, relative_module_path.name[:-3])
        return ".".join(module_name_parts)

    def _get_coveragerc_ignore_modules(self) -> Iterator[Path]:
        coveragerc = ConfigParser()
        coveragerc.read(ROOT_DIRECTORY_PATH / ".coveragerc")
        omit = coveragerc.get("run", "omit").split("\n")
        for omit_pattern in omit:
            for module_path_str in glob(omit_pattern, recursive=True):
                if not module_path_str.endswith(".py"):
                    continue
                module_path = Path(module_path_str)
                if not module_path.is_file():
                    continue
                yield module_path

    async def _get_ignore_src_module_paths(
        self,
    ) -> Mapping[Path, set[str] | type[TestModuleKnownToBeMissing]]:
        return {
            **{
                Path(module_file_path_str): members
                for module_file_path_str, members in _BASELINE.items()
            },
            **{
                module_file_path: TestModuleKnownToBeMissing
                for module_file_path in self._get_coveragerc_ignore_modules()
            },
        }

    async def _test_python_file(self, file_path: Path) -> AsyncIterator[str]:
        # Skip tests.
        if ROOT_DIRECTORY_PATH / "betty" / "tests" in file_path.parents:
            return

        src_module_path = file_path.relative_to(ROOT_DIRECTORY_PATH)

        ignore_src_module_paths = await self._get_ignore_src_module_paths()

        expected_test_file_path = (
            ROOT_DIRECTORY_PATH
            / "betty"
            / "tests"
            / file_path.relative_to(ROOT_DIRECTORY_PATH / "betty").parent
            / f"test_{file_path.name}"
        )
        if expected_test_file_path.exists():
            if (
                src_module_path in ignore_src_module_paths
                and ignore_src_module_paths[src_module_path]
                == TestModuleKnownToBeMissing
            ):
                yield f"{src_module_path} has a matching test file at {src_module_path}, which was unexpectedly declared as known to be missing."
            async for error in self._test_python_module(
                src_module_path,
                expected_test_file_path.relative_to(ROOT_DIRECTORY_PATH),
            ):
                yield error
            return

        if src_module_path in ignore_src_module_paths:
            return

        if await self._test_python_file_contains_docstring_only(file_path):
            return

        yield f"{src_module_path} does not have a matching test file. Expected {expected_test_file_path} to exist."

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

    async def _test_python_module(
        self, src_module_path: Path, test_module_path: Path
    ) -> AsyncIterator[str]:
        src_module_name, src_function_names, src_class_names = self._get_module_data(
            src_module_path
        )

        # Skip private modules.
        if True in map(lambda x: x.startswith("_"), src_module_name.split(".")):
            return

        test_module_name, _, test_class_names = self._get_module_data(test_module_path)

        ignore_src_module_paths = await self._get_ignore_src_module_paths()

        for src_function_name in src_function_names:
            expected_test_class_name = (
                f"Test{snake_case_to_upper_camel_case(src_function_name)}"
            )
            ignore_src_members = ignore_src_module_paths.get(src_module_path, set())
            assert isinstance(ignore_src_members, set)
            if (
                expected_test_class_name not in test_class_names
                and src_function_name not in ignore_src_members
            ):
                yield f"Failed to find the test class {test_module_name}.{expected_test_class_name} for the source function {src_module_name}.{src_function_name}()."

        for src_class_name in src_class_names:
            expected_test_class_name = f"Test{src_class_name}"
            ignore_src_members = ignore_src_module_paths.get(src_module_path, set())
            assert isinstance(ignore_src_members, set)
            if (
                expected_test_class_name not in test_class_names
                and src_class_name not in ignore_src_members
            ):
                yield f"Failed to find the test class {test_module_name}.{expected_test_class_name} for the source class {src_module_name}.{src_class_name}."

    def _get_module_data(
        self, module_path: Path
    ) -> tuple[str, Sequence[str], Sequence[str]]:
        module_name = self._module_path_to_name(module_path)
        return (
            module_name,
            sorted(self._get_members(module_name, isfunction)),
            sorted(self._get_members(module_name, isclass)),
        )

    def _get_members(
        self, module_name: str, predicate: Callable[[object], bool]
    ) -> Iterator[str]:
        module = import_module(module_name)
        for member_name, _ in getmembers(module, predicate):
            # Ignore private members.
            if member_name.startswith("_"):
                continue

            # Ignore members that are not defined by the module under test (they may have been from other modules).
            imported_member = getattr(module, member_name)
            if getattr(imported_member, "__module__", None) != module_name:
                continue

            yield imported_member.__name__
