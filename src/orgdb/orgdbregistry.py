import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pybiocfilecache import BiocFileCache

from ._ahub import AHUB_METADATA_URL
from .orgdb import OrgDb
from .record import OrgDbRecord

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


class OrgDbRegistry:
    """Registry for OrgDb resources, dynamically populated from AnnotationHub."""

    def __init__(
        self,
        cache_dir: Optional[Union[str, Path]] = None,
        force: bool = False,
    ) -> None:
        """Initialize the OrgDb registry.

        Args:
            cache_dir:
                Directory for the BiocFileCache database and cached files.
                If None, defaults to "~/.cache/orgdb_bfc".

            force:
                If True, force re-download of the AnnotationHub metadata database.
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "orgdb_bfc"

        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._bfc = BiocFileCache(self._cache_dir)

        self._registry_map: Dict[str, OrgDbRecord] = {}

        self._initialize_registry(force=force)

    def _initialize_registry(self, force: bool = False):
        """Fetch the AnnotationHub metadata and populate the registry."""
        rname = "annotationhub_metadata"

        existing = None
        try:
            existing = self._bfc.get(rname)
        except Exception:
            pass

        if force and existing:
            try:
                self._bfc.remove(rname)
            except Exception:
                pass
            existing = None

        if existing:
            md_resource = existing
        else:
            md_resource = self._bfc.add(rname, AHUB_METADATA_URL, rtype="web")

        md_path = self._get_filepath(md_resource)

        if not md_path or not os.path.exists(md_path):
            if existing and not force:
                return self._initialize_registry(force=True)

            raise RuntimeError("Failed to retrieve AnnotationHub metadata database.")

        conn = sqlite3.connect(md_path)
        try:
            query = """
            SELECT
                r.title,
                r.rdatadateadded,
                lp.location_prefix || rp.rdatapath AS full_rdatapath
            FROM resources r
            LEFT JOIN location_prefixes lp
                ON r.location_prefix_id = lp.id
            LEFT JOIN rdatapaths rp
                ON rp.resource_id = r.id
            WHERE r.title LIKE 'org.%.sqlite'
            ORDER BY r.rdatadateadded DESC;
            """
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
        finally:
            conn.close()

        for title, date_added, url in rows:
            if title.endswith(".sqlite"):
                orgdb_id = title[:-7]
            else:
                orgdb_id = title

            if orgdb_id in self._registry_map:
                continue

            entry = {"url": url, "release_date": str(date_added).split(" ")[0] if date_added else None}

            record = OrgDbRecord.from_config_entry(orgdb_id, entry)
            self._registry_map[orgdb_id] = record

    def list_orgdb(self) -> List[str]:
        """List all available OrgDb IDs (e.g., 'org.Hs.eg.db').

        Returns:
            A sorted list of valid OrgDb ID strings.
        """
        return sorted(list(self._registry_map.keys()))

    def get_record(self, orgdb_id: str) -> OrgDbRecord:
        """Get the metadata record for a given OrgDb ID.

        Args:
            orgdb_id:
                The OrgDb ID to look up (e.g., 'org.Hs.eg.db').

        Returns:
            A OrgDbRecord object containing metadata.

        Raises:
            KeyError: If the ID is not found.
        """
        if orgdb_id not in self._registry_map:
            raise KeyError(f"OrgDb ID '{orgdb_id}' not found in registry.")

        return self._registry_map[orgdb_id]

    def download(self, orgdb_id: str, force: bool = False) -> str:
        """Download and cache the OrgDb file.

        Args:
            orgdb_id:
                The OrgDb ID to fetch.

            force:
                If True, forces re-download even if already cached.

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

        # Check if already exists
        if not force:
            try:
                existing = self._bfc.get(key)
                if existing:
                    path = self._get_filepath(existing)
                    if path and os.path.exists(path) and os.path.getsize(path) > 0:
                        return path
            except Exception:
                pass

        # Add/Download
        resource = self._bfc.add(
            key,
            url,
            rtype="web",
            download=True,
        )

        path = self._get_filepath(resource)

        # Validation
        if not path or not os.path.exists(path) or os.path.getsize(path) == 0:
            # Cleanup bad download
            try:
                self._bfc.remove(key)
            except Exception:
                pass
            raise RuntimeError(f"Download failed for {orgdb_id}. File is empty or missing.")

        return path

    def load_db(self, orgdb_id: str, force: bool = False) -> OrgDb:
        """Load an OrgDb object for the given ID.

        Args:
            orgdb_id:
                The ID of the OrgDb to load.

            force:
                If True, forces re-download of the database file.

        Returns:
            An initialized OrgDb object.
        """
        path = self.download(orgdb_id, force=force)
        return OrgDb(path)

    def _get_filepath(self, resource: Any) -> Optional[str]:
        """Helper to extract absolute path from a BiocFileCache resource."""
        if hasattr(resource, "rpath"):
            rel_path = str(resource.rpath)
        elif hasattr(resource, "get"):
            rel_path = str(resource.get("rpath"))
        else:
            return None

        return str(self._cache_dir / rel_path)
