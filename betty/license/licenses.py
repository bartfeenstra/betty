"""
Provide :py:class:`betty.license.License` plugins.
"""

import logging
import re
import tarfile
from asyncio import gather, get_running_loop
from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from concurrent.futures import Executor
from contextlib import contextmanager
from json import loads
from multiprocessing.managers import SyncManager
from pathlib import Path

import aiofiles
from typing_extensions import override

from betty.cache.file import BinaryFileCache
from betty.concurrent import AsynchronizedLock, Ledger, ensure_manager
from betty.error import UserFacingError
from betty.factory import Factory
from betty.fetch import Fetcher, FetchError
from betty.license import License
from betty.locale.localizable import Localizable, _, plain
from betty.locale.localizer import Localizer
from betty.machine_name import MachineName
from betty.plugin import PluginNotFound, PluginRepository, ShorthandPluginBase
from betty.typing import threadsafe


class AllRightsReserved(ShorthandPluginBase, License):
    """
    A license that does not permit the public any rights.
    """

    _plugin_id = "all-rights-reserved"
    _plugin_label = _("All rights reserved")

    @property
    @override
    def summary(self) -> Localizable:
        return self._plugin_label

    @property
    @override
    def text(self) -> Localizable:
        return _(
            "No part may be reproduced or distributed in any form or by any means, without express written permission from the copyright holder, or unless permitted by copyright law."
        )


class PublicDomain(ShorthandPluginBase, License):
    """
    A work is in the `public domain <https://en.wikipedia.org/wiki/Public_domain>`.
    """

    _plugin_id = "public-domain"
    _plugin_label = _("Public domain")

    @property
    @override
    def summary(self) -> Localizable:
        return _("Public domain")

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


@threadsafe
class SpdxLicenseRepository(PluginRepository[License]):
    """
    Provide licenses from the `SPDX License List <https://spdx.org/licenses/>`_.
    """

    SPDX_VERSION = "3.27.0"
    URL = f"https://github.com/spdx/license-list-data/archive/refs/tags/v{SPDX_VERSION}.tar.gz"

    def __init__(
        self,
        *,
        fetcher: Fetcher,
        localizer: Localizer,
        binary_file_cache: BinaryFileCache,
        process_pool: Executor,
        factory: Factory | None = None,
        manager: SyncManager | None = None,
    ):
        super().__init__(factory=factory)
        manager = ensure_manager(manager)
        self._fetcher = fetcher
        self._localizer = localizer
        self._cache_directory_path = binary_file_cache.with_scope(
            self.SPDX_VERSION
        ).path
        self._license_id_to_spdx_license_id_map: Mapping[MachineName, str]
        self._license_id_to_spdx_reference_map: Mapping[MachineName, str]
        self._license_id_to_spdx_details_url_map: Mapping[MachineName, str]
        self._licenses: Mapping[str, type[License] | None]
        self._lock = AsynchronizedLock(manager.Lock())
        self._ledger = Ledger(self._lock, manager=manager)
        self._licenses_loaded = False
        self._process_pool = process_pool

    async def license_id_to_spdx_license_id(self, license_id: MachineName) -> str:
        """
        Get the SPDX license ID for the given Betty license plugin ID.
        """
        await self._load_licenses()
        try:
            return self._license_id_to_spdx_license_id_map[license_id]
        except KeyError:
            raise PluginNotFound.new(license_id, await self.select()) from None

    @override
    async def get(self, plugin_id: MachineName) -> type[License]:
        return await self._load_license(plugin_id)

    async def _load_licenses(self) -> None:
        async with self._lock:
            # Check again to ensure licenses weren't added in the meantime.
            if self._licenses_loaded:
                return
            self._licenses_loaded = True

            self._license_id_to_spdx_license_id_map = {}
            self._license_id_to_spdx_reference_map = {}
            self._license_id_to_spdx_details_url_map = {}
            self._licenses = {}

            try:
                spdx_licenses_data_path = await self._fetcher.fetch_file(self.URL)
            except FetchError:
                logger = logging.getLogger(__name__)
                logger.warning(
                    self._localizer._("Betty could not load the SPDX licenses")
                )
                return

            if not self._cache_directory_path.exists():
                loop = get_running_loop()
                await loop.run_in_executor(
                    self._process_pool,
                    self._extract_licenses,
                    spdx_licenses_data_path,
                    self._cache_directory_path,
                )

            async with aiofiles.open(
                self._cache_directory_path
                / f"license-list-data-{self.SPDX_VERSION}"
                / "json"
                / "licenses.json"
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
                license_id = spdx_license_id_to_license_id(spdx_license_id)

                spdx_reference = spdx_license_data["reference"]
                assert isinstance(spdx_reference, str)

                spdx_details_url = spdx_license_data["detailsUrl"]
                assert isinstance(spdx_details_url, str)

                self._license_id_to_spdx_license_id_map[license_id] = spdx_license_id
                self._license_id_to_spdx_reference_map[license_id] = spdx_reference
                self._license_id_to_spdx_details_url_map[license_id] = spdx_details_url
                self._licenses[license_id] = None

    @classmethod
    def _extract_licenses(
        cls, spdx_licenses_data_path: Path, cache_directory_path: Path
    ):
        with tarfile.open(spdx_licenses_data_path, "r:gz") as tar_file:
            tar_file.extractall(
                cache_directory_path,
                members=[
                    tar_file.getmember(
                        f"license-list-data-{cls.SPDX_VERSION}/json/licenses.json"
                    ),
                    *[
                        tar_info
                        for tar_info in tar_file.getmembers()
                        if tar_info.name.startswith(
                            f"license-list-data-{cls.SPDX_VERSION}/json/details/"
                        )
                    ],
                ],
                filter="data",
            )

    async def _load_license(self, license_id: MachineName) -> type[License]:
        await self._load_licenses()
        async with self._ledger.ledger(license_id):
            try:
                license = self._licenses[license_id]  # noqa a001
            except KeyError:
                raise PluginNotFound.new(license_id, await self.select()) from None
            else:
                if license is None:
                    license = await self._create_license(license_id)  # noqa a001
                    self._licenses[license_id] = license  # type: ignore[index]
                return license

    @override
    async def __aiter__(self) -> AsyncIterator[type[License]]:
        await self._load_licenses()
        for license in await gather(  # noqa A001
            *(self._load_license(license_id) for license_id in self._licenses)
        ):
            yield license

    @contextmanager
    def _catch_json_errors(self) -> Iterator[None]:
        try:
            yield
        except (AssertionError, LookupError) as error:
            raise UserFacingError(
                plain(f"Invalid JSON response received from {self.URL}")
            ) from error

    async def _create_license(self, license_id: MachineName) -> type[License]:
        async with aiofiles.open(
            self._cache_directory_path
            / f"license-list-data-{self.SPDX_VERSION}"
            / "json"
            / "details"
            / f"{self._license_id_to_spdx_license_id_map[license_id]}.json"
        ) as spdx_license_data_f:
            spdx_license_data_json = await spdx_license_data_f.read()

        with self._catch_json_errors():
            spdx_license_data = loads(spdx_license_data_json)
            assert isinstance(spdx_license_data, Mapping)

            url = self._license_id_to_spdx_reference_map[license_id]

            license_name = spdx_license_data["name"]
            assert isinstance(license_name, str)
            plugin_label = plain(license_name)

            license_text = spdx_license_data["licenseText"]
            assert isinstance(license_text, str)

            class _SpdxLicense(ShorthandPluginBase, License):
                _plugin_id = license_id
                _plugin_label = plugin_label

                @override
                @property
                def summary(self) -> Localizable:
                    return self.plugin_label()

                @override
                @property
                def text(self) -> Localizable:
                    return plain(
                        license_text  # type: ignore[arg-type]
                    )

                @override
                @property
                def url(self) -> Localizable | None:
                    return plain(url)

            return _SpdxLicense
