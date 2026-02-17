import tarfile
from collections.abc import AsyncIterator
from io import BytesIO
from json import dumps
from pathlib import Path
from typing import TYPE_CHECKING, override

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

from betty.cache.file import BinaryFileCache
from betty.license import License
from betty.license.licenses import (
    AllRightsReserved,
    PublicDomain,
    SpdxLicenseBuilder,
    spdx_license_id_to_license_id,
)
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.service.level import UNIVERSE
from betty.test_utils.license import LicenseTestBase
from betty.test_utils.user import StaticUser

if TYPE_CHECKING:
    from betty.portable import PortableMapping


class TestAllRightsReserved(LicenseTestBase):
    @override
    @pytest.fixture
    def sut(self) -> License:
        return AllRightsReserved()


class TestPublicDomain(LicenseTestBase):
    @override
    @pytest.fixture
    def sut(self) -> License:
        return PublicDomain()


@pytest.mark.parametrize(
    ("expected", "spdx_license_id"),
    [
        ("spdx-mit", "MIT"),
        ("spdx-gpl-3--0-or-later", "GPL-3.0-or-later"),
    ],
)
def test_spdx_license_id_to_license_id(expected: str, spdx_license_id: str) -> None:
    assert spdx_license_id_to_license_id(spdx_license_id) == expected


class TestSpdxLicenseBuilder:
    @pytest.fixture
    async def sut_without_licenses(
        self,
        binary_file_cache: BinaryFileCache,
        http_client_mock: aioresponses,
        tmp_path: Path,
    ) -> AsyncIterator[SpdxLicenseBuilder]:
        spdx_directory_path = tmp_path / "spdx"
        spdx_directory_path.mkdir()
        licenses_data: PortableMapping = {
            "licenseListVersion": SpdxLicenseBuilder.VERSION,
            "licenses": [],
            "releaseDate": "2024-08-19",
        }
        licenses_file_path = (
            spdx_directory_path
            / f"license-list-data-{SpdxLicenseBuilder.VERSION}"
            / "json"
            / "licenses.json"
        )
        licenses_file_path.parent.mkdir(parents=True)
        with open(licenses_file_path, "w") as f:
            f.write(dumps(licenses_data))
        spdx_file = BytesIO()
        with tarfile.open(fileobj=spdx_file, mode="w:gz") as spdx_tar_file:
            spdx_tar_file.add(spdx_directory_path, "/")
        spdx_file.seek(0)
        http_client_mock.get(SpdxLicenseBuilder.URL, body=spdx_file.read())
        async with ClientSession() as http_client:
            sut = SpdxLicenseBuilder(
                http_client=http_client,
                binary_file_cache=binary_file_cache,
                user=StaticUser(),
            )
            yield sut

    @pytest.fixture
    async def sut_with_licenses(
        self,
        binary_file_cache: BinaryFileCache,
        http_client_mock: aioresponses,
        tmp_path: Path,
    ) -> AsyncIterator[SpdxLicenseBuilder]:
        spdx_directory_path = tmp_path / "spdx"
        spdx_directory_path.mkdir()
        licenses_data: PortableMapping = {
            "licenseListVersion": SpdxLicenseBuilder.VERSION,
            "licenses": [
                {
                    "reference": "https://spdx.org/licenses/0BSD.html",
                    "isDeprecatedLicenseId": False,
                    "detailsUrl": "https://spdx.org/licenses/0BSD.json",
                    "referenceNumber": 582,
                    "name": "BSD Zero Clause License",
                    "licenseId": "0BSD",
                    "seeAlso": [
                        "http://landley.net/toybox/license.html",
                        "https://opensource.org/licenses/0BSD",
                    ],
                    "isOsiApproved": True,
                },
            ],
            "releaseDate": "2024-08-19",
        }
        licenses_file_path = (
            spdx_directory_path
            / f"license-list-data-{SpdxLicenseBuilder.VERSION}"
            / "json"
            / "licenses.json"
        )
        licenses_file_path.parent.mkdir(parents=True)
        with open(licenses_file_path, "w") as f:
            f.write(dumps(licenses_data))
        license_data: PortableMapping = {
            "isDeprecatedLicenseId": False,
            "licenseText": 'Copyright (C) YEAR by AUTHOR EMAIL\n\nPermission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.\n\nTHE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.\n',
            "standardLicenseTemplate": '\u003c\u003cbeginOptional\u003e\u003e\u003c\u003cvar;name\u003d"title";original\u003d"BSD Zero Clause License";match\u003d"(BSD Zero[ -]Clause|Zero[ -]Clause BSD)( License)?( \\(0BSD\\))?"\u003e\u003e\n\n\u003c\u003cendOptional\u003e\u003e \u003c\u003cvar;name\u003d"copyright";original\u003d"Copyright (C) YEAR by AUTHOR EMAIL  ";match\u003d".{0,5000}"\u003e\u003e\n\nPermission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.\n\nTHE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.\n\n',
            "name": "BSD Zero Clause License",
            "licenseId": "0BSD",
            "crossRef": [
                {
                    "match": "N/A",
                    "url": "https://opensource.org/licenses/0BSD",
                    "isValid": True,
                    "isLive": False,
                    "timestamp": "2024-08-19T17:47:27Z",
                    "isWayBackLink": False,
                    "order": 1,
                },
                {
                    "match": "false",
                    "url": "http://landley.net/toybox/license.html",
                    "isValid": True,
                    "isLive": True,
                    "timestamp": "2024-08-19T17:47:28Z",
                    "isWayBackLink": False,
                    "order": 0,
                },
            ],
            "seeAlso": [
                "http://landley.net/toybox/license.html",
                "https://opensource.org/licenses/0BSD",
            ],
            "isOsiApproved": True,
            "licenseTextHtml": '\n      \u003cdiv class\u003d"optional-license-text"\u003e \n         \u003cp\u003e\u003cvar class\u003d"replaceable-license-text"\u003e BSD Zero Clause License\u003c/var\u003e\u003c/p\u003e\n\n      \u003c/div\u003e\n      \u003cdiv class\u003d"replaceable-license-text"\u003e \n         \u003cp\u003eCopyright (C) YEAR by AUTHOR EMAIL\u003c/p\u003e\n\n      \u003c/div\u003e\n\n      \u003cp\u003ePermission to use, copy, modify, and/or distribute this software for any purpose with or without fee is\n         hereby granted.\u003c/p\u003e\n\n      \u003cp\u003eTHE SOFTWARE IS PROVIDED \u0026quot;AS IS\u0026quot; AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE\n         INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE\n         LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING\n         FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS\n         ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.\u003c/p\u003e\n\n    ',
        }
        license_file_path = (
            spdx_directory_path
            / f"license-list-data-{SpdxLicenseBuilder.VERSION}"
            / "json"
            / "details"
            / "0BSD.json"
        )
        license_file_path.parent.mkdir()
        with open(license_file_path, "w") as f:
            f.write(dumps(license_data))
        spdx_tar_file_path = tmp_path / "spdx.tar.gz"
        with tarfile.open(spdx_tar_file_path, "w:gz") as spdx_tar_file:
            spdx_tar_file.add(spdx_directory_path, "/")
        spdx_file = BytesIO()
        with tarfile.open(fileobj=spdx_file, mode="w:gz") as spdx_tar_file:
            spdx_tar_file.add(spdx_directory_path, "/")
        spdx_file.seek(0)
        http_client_mock.get(SpdxLicenseBuilder.URL, body=spdx_file.read())
        async with ClientSession() as http_client:
            sut = SpdxLicenseBuilder(
                http_client=http_client,
                binary_file_cache=binary_file_cache,
                user=StaticUser(),
            )
            yield sut

    async def test_build__with_licenses(
        self, sut_with_licenses: SpdxLicenseBuilder
    ) -> None:
        zero_bsd_type = [
            license
            async for license in sut_with_licenses.build()  # noqa: A001
        ][0]
        assert (
            zero_bsd_type.label.localize(DEFAULT_LOCALIZER) == "BSD Zero Clause License"
        )
        zero_bsd = await UNIVERSE.factory.new(zero_bsd_type.cls)
        assert zero_bsd.summary.localize(DEFAULT_LOCALIZER) == "BSD Zero Clause License"
        assert (
            zero_bsd.text.localize(DEFAULT_LOCALIZER)
            == 'Copyright (C) YEAR by AUTHOR EMAIL\n\nPermission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted.\n\nTHE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.\n'
        )
        url = zero_bsd.url
        assert url is not None
        assert url.localize(DEFAULT_LOCALIZER) == "https://spdx.org/licenses/0BSD.html"

    async def test_build__without_licenses(
        self, sut_without_licenses: SpdxLicenseBuilder
    ) -> None:
        assert not [
            license
            async for license in sut_without_licenses.build()  # noqa: A001
        ]
