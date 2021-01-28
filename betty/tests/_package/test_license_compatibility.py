import io
import json
import sys

from pkg_resources import get_distribution

from betty.tests import TestCase
import piplicenses


class PackageLicensesTest(TestCase):
    _GPL_V3_COMPATIBLE_DISTRIBUTIONS = (
        'PyQt5-sip',
        'graphlib-backport',  # Released under the Python Software Foundation License.
    )

    _GPL_V3_COMPATIBLE_LICENSES = (
        'Apache Software License',
        'BSD License',
        'GPL v3',
        'GNU General Public License v3 (GPLv3)',
        'GNU Library or Lesser General Public License (LGPL)',
        'GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Historical Permission Notice and Disclaimer (HPND)',
        'MIT License',
        'Mozilla Public License 2.0 (MPL 2.0)',
        'Python Software Foundation License',
    )

    def assert_is_compatible(self, package_license: dict) -> None:
        for compatible_license in self._GPL_V3_COMPATIBLE_LICENSES:
            if compatible_license in package_license['License']:
                return
        self.fail("%s is released under the %s, which is not known to be compatible with Betty's own license" % (
            package_license['Name'],
            package_license['License'],
        ))

    def test_runtime_dependency_license_compatibility(self) -> None:
        """
        Assert that all runtime dependencies have licenses compatible with the GPLv3, so we can legally bundle them.
        """

        def _get_dependency_distribution_names(name: str):
            yield name
            for dependency in get_distribution(name).requires():
                yield from _get_dependency_distribution_names(dependency.project_name)
        distribution_names = list(filter(lambda x: x not in self._GPL_V3_COMPATIBLE_DISTRIBUTIONS, _get_dependency_distribution_names('betty')))

        piplicenses_stdout = io.StringIO()
        argv = sys.argv
        stdout = sys.stdout
        try:
            sys.argv = [
                '',
                '--format',
                'json',
                '--packages',
                *distribution_names,
            ]
            sys.stdout = piplicenses_stdout
            piplicenses.main()
            package_licenses = json.loads(piplicenses_stdout.getvalue())
            self.assertGreater(len(package_licenses), 1)
            for package_license in package_licenses:
                self.assert_is_compatible(package_license)
        finally:
            sys.argv = argv
            sys.stdout = stdout
