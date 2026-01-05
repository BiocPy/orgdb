import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from pybiocfilecache import BiocFileCache

from ._ahub import ORGDB_CONFIG
from .orgdb import OrgDb
from .record import OrgDbRecord

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

# copied over from the txdb package


class OrgDbRegistry:
    """Registry for OrgDb resources backed by ORGDB_CONFIG and a BiocFileCache."""

    def __init__(
        self,
        config: Dict[str, Dict[str, Any]] = ORGDB_CONFIG,
        cache_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initialize the OrgDb registry.

        Args:
            config:
                ORGDB_CONFIG-style mapping:
                    orgdb_id -> {"release_date": "YYYY-MM-DD", "url": "..."}

            cache_dir:
                Directory for the BiocFileCache database and cached files.
                If None, defaults to "~/.cache/orgdb_bfc".
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "orgdb_bfc"

        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)

        self._bfc = BiocFileCache(cache_dir)
        self._config = config

    def list_orgdb(self) -> list[str]:
        """List all available OrgDb IDs.

        Returns:
            A list of valid OrgDb ID strings.
        """
        return list(self._config.keys())

    def get_record(self, orgdb_id: str) -> OrgDbRecord:
        """Get the metadata record for a given OrgDb ID.

        Args:
            orgdb_id:
                The OrgDb ID to look up (e.g., 'org.Hs.eg.db').

        Returns:
            A OrgDbRecord object containing metadata.

        Raises:
            KeyError: If the ID is not found in the configuration.
        """
        if orgdb_id not in self._config:
            raise KeyError(f"OrgDb ID '{orgdb_id}' not found in registry.")

        entry = self._config[orgdb_id]
        return OrgDbRecord.from_config_entry(orgdb_id, entry)

    def _get_absolute_path(self, x: str):
        return f"{self._bfc.config.cache_dir}/{x}"

    def download(self, orgdb_id: str, force: bool = False) -> str:
        """Download and cache the OrgDb file.

        Args:
            orgdb_id:
                The OrgDb ID to fetch.

            force:
                If True, forces re-download even if already cached.
                Defaults to False.

        Returns:
            Local filesystem path to the cached file.
        """
        record = self.get_record(orgdb_id)
        url = record.url
        key = orgdb_id

        if force:
            try:
                self._bfc.remove(key)
            except Exception:
                pass

        resource = self._bfc.add(
            key,
            url,
            rtype="web",
            download=True,
        )

        path = self._resource_path(resource)
        if path is None:
            raise RuntimeError(f"Could not resolve local path for resource {key!r}")

        abs_path = self._get_absolute_path(path)

        if not os.path.exists(abs_path) or os.path.getsize(abs_path) == 0:
            try:
                self._bfc.remove(key)
            except Exception:
                pass
            raise RuntimeError(
                f"Download failed for {orgdb_id}: File at {abs_path} is empty or missing. "
                "Please check your internet connection or the resource URL."
            )

        return str(abs_path)

    def load_db(self, orgdb_id: str, force: bool = False) -> OrgDb:
        """Load an OrgDb object for the given ID.

        If the resource is already downloaded and valid, it returns the local copy
        immediately (unless force=True).

        Args:
            orgdb_id:
                The ID of the OrgDb to load.

            force:
                If True, forces re-download of the database file.

        Returns:
            An initialized OrgDb object connected to the cached database.
        """
        if not force and self.exists_locally(orgdb_id):
            path = self.local_path(orgdb_id)
            if path:
                return OrgDb(path)

        path = self.download(orgdb_id, force=force)
        return OrgDb(path)

    def exists_locally(self, orgdb_id: str) -> bool:
        """Check if the file for a given OrgDb ID is already present in the cache."""
        try:
            resource = self._bfc.get(orgdb_id)
        except Exception:
            return False

        path = self._resource_path(resource)
        abs_path = self._get_absolute_path(path)
        return bool(abs_path and os.path.exists(abs_path) and os.path.getsize(abs_path) > 0)

    def local_path(self, orgdb_id: str) -> Optional[str]:
        """Return local path if cached, else None."""
        try:
            resource = self._bfc.get(orgdb_id)
        except Exception:
            return None

        path = self._resource_path(resource)
        abs_path = self._get_absolute_path(path)
        if not abs_path or not os.path.exists(abs_path) or os.path.getsize(abs_path) == 0:
            return None

        return str(abs_path)

    def _resource_path(self, resource: Any) -> Optional[str]:
        """Helper to extract path from a BiocFileCache resource object."""
        if hasattr(resource, "rpath"):
            return str(resource.rpath)

        return str(resource.get("rpath")) if hasattr(resource, "get") else None
