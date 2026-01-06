from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


@dataclass(frozen=True)
class OrgDbRecord:
    """Container for a single OrgDb entry."""

    orgdb_id: str
    release_date: Optional[date]
    url: str

    species: Optional[str] = None  # e.g. "Hs" or "Hsapiens"
    id_type: Optional[str] = None  # e.g. "eg" (Entrez Gene) or "tair"

    bioc_version: Optional[str] = None

    @classmethod
    def from_config_entry(cls, orgdb_id: str, entry: dict) -> "OrgDbRecord":
        """Build a record from a ORGDB_CONFIG entry:
        {
            "release_date": "YYYY-MM-DD",  # optional
            "url": "https://..."
        }
        """
        url = entry["url"]

        date_str = entry.get("release_date")
        rel_date: Optional[date]
        if date_str:
            rel_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            rel_date = None

        species, id_type = _parse_orgdb_id(orgdb_id)
        bioc_version = _parse_bioc_version(url)

        return cls(
            orgdb_id=orgdb_id,
            release_date=rel_date,
            url=url,
            species=species,
            id_type=id_type,
            bioc_version=bioc_version,
        )


def _parse_orgdb_id(orgdb_id: str):
    """Parse IDs like:
      org.Hs.eg.db
      org.At.tair.db
    into (species, id_type).
    """
    name = orgdb_id
    if name.startswith("org."):
        name = name[len("org.") :]

    if name.endswith(".db"):
        name = name[: -len(".db")]

    if name.endswith(".sqlite"):
        name = name[: -len(".sqlite")]

    parts = name.split(".")

    if len(parts) < 2:
        return None, None

    species = parts[0]
    id_type = parts[1]

    return species, id_type


def _parse_bioc_version(url: str) -> Optional[str]:
    """Extract the Bioconductor/AnnotationHub-like version from URL.

    Example:
        .../standard/3.19/org.Hs.eg.sqlite -> "3.19"
    """
    parts = url.rstrip("/").split("/")
    if len(parts) < 2:
        return None

    candidate = parts[-2]

    if candidate.replace(".", "").isdigit():
        return candidate
    return None
