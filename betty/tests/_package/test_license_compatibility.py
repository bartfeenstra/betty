import io
import json
import sys
from importlib.metadata import metadata, PackageNotFoundError
from typing import Iterator, Any

import piplicenses
from packaging.requirements import Requirement


class TestPackageLicenses:
    _GPL_V3_COMPATIBLE_DISTRIBUTIONS = (
        # We do not include basedtyping in any Betty distribution.
        "basedtyping",
    )

    _GPL_V3_COMPATIBLE_LICENSES = (
        "Apache Software License",
        "Apache-2.0",
        "BSD License",
        "BSD-3-Clause",
        "GPL v3",
        "GNU General Public License v3 (GPLv3)",
        "GNU Library or Lesser General Public License (LGPL)",
        "GNU Lesser General Public License v2 or later (LGPLv2+)",
        "Historical Permission Notice and Disclaimer (HPND)",
        "MIT",
        "MIT License",
        "Mozilla Public License 2.0 (MPL 2.0)",
        "Python Software Foundation License",
        "The Unlicense (Unlicense)",
    )

    def assert_is_compatible(self, package_license: dict[str, Any]) -> None:
        for compatible_license in self._GPL_V3_COMPATIBLE_LICENSES:
            if compatible_license in package_license["License"]:
                return
        raise AssertionError(
            "%s is released under the %s, which is not known to be compatible with Betty's own license"
            % (
                package_license["Name"],
                package_license["License"],
            )
        )

    async def test_runtime_dependency_license_compatibility(self) -> None:
        """
        Assert that all runtime dependencies have licenses compatible with the GPLv3, so we can legally bundle them.
        """
        seen_distribution_names: set[str] = set()

        def _get_dependency_distribution_names(distribution_name: str) -> Iterator[str]:
            if distribution_name in seen_distribution_names:
                return
            seen_distribution_names.add(distribution_name)

            yield distribution_name
            # Work around https://github.com/sphinx-doc/sphinx/issues/11567.
            if distribution_name.startswith("sphinxcontrib-"):
                return
            try:
                distribution_metadata = metadata(distribution_name)
            except PackageNotFoundError:
                # Packages may not be found if they are only installed under certain conditions.
                # This is the case for many backports, which are installed only on older Python versions.
                return
            else:
                for requirement_string in distribution_metadata.get_all(
                    "Requires-Dist", ()
                ):
                    yield from _get_dependency_distribution_names(
                        Requirement(requirement_string).name
                    )

        distribution_names = list(
            filter(
                lambda x: x not in self._GPL_V3_COMPATIBLE_DISTRIBUTIONS,
                _get_dependency_distribution_names("betty"),
            )
        )

        piplicenses_stdout = io.StringIO()
        argv = sys.argv
        stdout = sys.stdout
        try:
            sys.argv = [
                "",
                "--format",
                "json",
                "--packages",
                *distribution_names,
            ]
            sys.stdout = piplicenses_stdout
            piplicenses.main()
            package_licenses = json.loads(piplicenses_stdout.getvalue())
            assert len(package_licenses) > 1
            for package_license in package_licenses:
                self.assert_is_compatible(package_license)
        finally:
            sys.argv = argv
            sys.stdout = stdout
