"""
Provide :py:class:`betty.license.License` plugins.
"""

import re
import tarfile
from asyncio import to_thread
from collections.abc import AsyncIterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from io import BytesIO
from json import loads
from pathlib import Path
from typing import final

import aiofiles
from aiohttp import ClientError, ClientSession
from typing_extensions import override

from betty.cache.file import BinaryFileCache
from betty.exception import HumanFacingException
from betty.license import License, LicenseDefinition
from betty.locale.localizable import Localizable, Plain, _
from betty.machine_name import MachineName
from betty.user import User


@final
@LicenseDefinition(
    id="all-rights-reserved",
    label=_("All rights reserved"),
)
class AllRightsReserved(License):
    """
    A license that does not permit the public any rights.
    """

    @property
    @override
    def summary(self) -> Localizable:
        return self.plugin.label

    @property
    @override
    def text(self) -> Localizable:
        return _(
            "No part may be reproduced or distributed in any form or by any means, without express written permission from the copyright holder, or unless permitted by copyright law."
        )


@final
@LicenseDefinition(
    id="public-domain",
    label=_("Public domain"),
)
class PublicDomain(License):
    """
    A work is in the `public domain <https://en.wikipedia.org/wiki/Public_domain>`.
    """

    @property
    @override
    def summary(self) -> Localizable:
        return self.plugin.label

    @property
    @override
    def text(self) -> Localizable:
        return _(
            "Works in the public domain can be used or referenced without permission, because nobody holds any exclusive rights over these works (anymore)."
        )


_SPDX_LICENSE_ID_PATTERN = re.compile(r"[^a-z0-9-]")


def spdx_license_id_to_license_id(spdx_license_id: str) -> MachineName:
    """
    Get the Betty license plugin ID for the given SPDX license ID.
    """
    return f"spdx-{_SPDX_LICENSE_ID_PATTERN.sub('--', spdx_license_id.lower())}"


class SpdxLicenseBuilder:
    """
    Build licenses from the `SPDX License List <https://spdx.org/licenses/>`_.
    """

    VERSION = "3.27.0"
    URL = (
        f"https://github.com/spdx/license-list-data/archive/refs/tags/v{VERSION}.tar.gz"
    )

    def __init__(
        self,
        *,
        http_client: ClientSession,
        user: User,
        binary_file_cache: BinaryFileCache,
    ):
        self._http_client = http_client
        self._user = user
        self._cache_directory_path = (
            binary_file_cache.with_scope("spdx-licenses").with_scope(self.VERSION).path
        )

    async def build(self) -> AsyncIterable[LicenseDefinition]:
        """
        Build the licenses.
        """
        if not self._cache_directory_path.exists():
            try:
                spdx_licenses_response = await self._http_client.get(self.URL)
                spdx_licenses_data_tar = await spdx_licenses_response.read()
            except ClientError:
                await self._user.message_warning(
                    _("Betty could not load the SPDX licenses")
                )
                return

            await to_thread(
                self._extract_licenses,
                spdx_licenses_data_tar,
                self._cache_directory_path,
            )

        async with aiofiles.open(
            self._cache_directory_path
            / f"license-list-data-{self.VERSION}"
            / "json"
            / "licenses.json",
            encoding="utf-8",
        ) as spdx_licenses_data_f:
            spdx_licenses_data_json = await spdx_licenses_data_f.read()
        spdx_data = loads(spdx_licenses_data_json)
        assert isinstance(spdx_data, Mapping)

        spdx_licenses_data = spdx_data["licenses"]
        assert isinstance(spdx_licenses_data, Sequence)

        for spdx_license_data in spdx_licenses_data:
            assert isinstance(spdx_license_data, Mapping)

            if spdx_license_data.get("isDeprecatedLicenseId", False):
                continue

            spdx_license_id = spdx_license_data["licenseId"]
            assert isinstance(spdx_license_id, str)
            spdx_license_id_to_license_id(spdx_license_id)

            spdx_reference = spdx_license_data["reference"]
            assert isinstance(spdx_reference, str)

            yield await self._build_license(spdx_license_id, spdx_reference)

    async def _build_license(self, license_id: str, url: str) -> LicenseDefinition:
        async with aiofiles.open(
            self._cache_directory_path
            / f"license-list-data-{self.VERSION}"
            / "json"
            / "details"
            / f"{license_id}.json",
            encoding="utf-8",
        ) as spdx_license_data_f:
            spdx_license_data_json = await spdx_license_data_f.read()

        with self._catch_json_errors():
            spdx_license_data = loads(spdx_license_data_json)
            assert isinstance(spdx_license_data, Mapping)

            license_name = spdx_license_data["name"]
            assert isinstance(license_name, str)

            license_text = spdx_license_data["licenseText"]
            assert isinstance(license_text, str)

            class _SpdxLicense(License):
                @override
                @property
                def summary(self) -> Localizable:
                    return self.plugin.label

                @override
                @property
                def text(self) -> Localizable:
                    return Plain(
                        license_text  # type: ignore[arg-type]
                    )

                @override
                @property
                def url(self) -> Localizable | None:
                    return Plain(url)

            return LicenseDefinition(
                id=spdx_license_id_to_license_id(license_id),
                label=Plain(license_name),
                cls=_SpdxLicense,
            )

    @classmethod
    def _extract_licenses(
        cls, spdx_licenses_data_tar: bytes, cache_directory_path: Path
    ):
        with tarfile.open(
            fileobj=BytesIO(spdx_licenses_data_tar), mode="r:gz"
        ) as tar_file:
            tar_file.extractall(
                cache_directory_path,
                members=[
                    tar_file.getmember(
                        f"license-list-data-{cls.VERSION}/json/licenses.json"
                    ),
                    *[
                        tar_info
                        for tar_info in tar_file.getmembers()
                        if tar_info.name.startswith(
                            f"license-list-data-{cls.VERSION}/json/details/"
                        )
                    ],
                ],
                filter="data",
            )

    @contextmanager
    def _catch_json_errors(self) -> Iterator[None]:
        try:
            yield
        except (AssertionError, LookupError) as error:
            raise HumanFacingException(
                Plain(f"Invalid JSON response received from {self.URL}")
            ) from error
