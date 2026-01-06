"""This list of OrgDB resources was generated from AnnotationHub.

Code to generate:

```bash
wget https://annotationhub.bioconductor.org/metadata/annotationhub.sqlite3
sqlite3 annotationhub.sqlite3
```

```sql
SELECT
    r.title,
    r.rdatadateadded,
    lp.location_prefix || rp.rdatapath AS full_rdatapath
FROM resources r
LEFT JOIN location_prefixes lp
    ON r.location_prefix_id = lp.id
LEFT JOIN rdatapaths rp
    ON rp.resource_id = r.id
WHERE r.title LIKE 'org%.sqlite';
```

Note: we only keep the latest version of these files.

"""

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

AHUB_METADATA_URL = "https://annotationhub.bioconductor.org/metadata/annotationhub.sqlite3"
