[![PyPI-Server](https://img.shields.io/pypi/v/orgdb.svg)](https://pypi.org/project/orgdb/)
![Unit tests](https://github.com/BiocPy/orgdb/actions/workflows/run-tests.yml/badge.svg)

# orgdb

**OrgDb** provides an interface to access and query **Organism Database (OrgDb)** SQLite files in Python. It mirrors functionality from the R/Bioconductor `AnnotationDbi` package, enabling seamless integration of organism-wide gene annotation into Python workflows.

> [!NOTE]
>
> If you are looking to access TxDb databases, check out the [txdb package](https://www.github.com/biocpy/txdb).

## Install

To get started, install the package from [PyPI](https://pypi.org/project/orgdb/)

```bash
pip install orgdb
```

## Usage

### Using OrgDbRegistry

The registry download the AnnotationHub's metadata sqlite file and filters for all available OrgDb databases. You can fetch standard organism databases via the registry (backed by AnnotationHub).

```py
from orgdb import OrgDbRegistry

# Initialize registry and list available organisms
registry = OrgDbRegistry()
available = registry.list_orgdb()
print(available[:5])
# ["org.'Caballeronia_concitans'.eg", "org.'Chlorella_vulgaris'_C-169.eg", ...]

# Load the database for Homo sapiens (downloads and caches automatically)
db = registry.load_db("org.Hs.eg.db")
print(db.species)
# 'Homo sapiens'
```

### Inspecting metadata

Explore the available columns and key types in the database.

```py
# List available columns (and keytypes)
cols = db.columns()
print(cols[:5])
# ['ENTREZID', 'PFAM', 'IPI', 'PROSITE', 'ACCNUM']

# Check available keys for a specific keytype
entrez_ids = db.keys("ENTREZID")
print(entrez_ids[:5])
# ['1', '2', '9', '10', '11']
```

### Querying Annotations (using `select`)

The `select` method retrieves data as a `BiocFrame`. It automatically handles complex joins across tables.

```py
# Retrieve Gene Symbols and Gene Names for a list of Entrez IDs
res = db.select(
    keys=["1", "10"],
    columns=["SYMBOL", "GENENAME"],
    keytype="ENTREZID"
)

print(res)
# BiocFrame with 2 rows and 3 columns
                   GENENAME ENTREZID SYMBOL
                     <list>   <list> <list>
# [0] alpha-1-B glycoprotein        1   A1BG
# [1]  N-acetyltransferase 2       10   NAT2

```

> [!NOTE]
>
> If you request "GO" columns, the result will automatically expand to include "EVIDENCE" and "ONTOLOGY" columns, matching Bioconductor behavior.

```py
go_res = db.select(
    keys="1",
    columns=["GO"],
    keytype="ENTREZID"
)
# BiocFrame with 12 rows and 4 columns
       ONTOLOGY ENTREZID         GO EVIDENCE
         <list>   <list>     <list>   <list>
#  [0]       BP        1 GO:0002764      IBA
#  [1]       CC        1 GO:0005576      HDA
#  [2]       CC        1 GO:0005576      IDA
#           ...      ...        ...      ...
#  [9]       CC        1 GO:0070062      HDA
# [10]       CC        1 GO:0072562      HDA
# [11]       CC        1 GO:1904813      TAS
```

### Accessing Genomic Ranges

Extract gene coordinates as a `GenomicRanges` object (requires the `chromosome_locations` table in the OrgDb database).

```py
gr = db.genes()
print(gr)
# GenomicRanges with 52232 ranges and 1 metadata column
#           seqnames                ranges          strand     gene_id
#              <str>             <IRanges> <ndarray[int8]>      <list>
#         1       19 -58345182 - -58336872               * |         1
#         2       12   -9067707 - -9019495               * |         2
#         2       12   -9067707 - -9019185               * |         2
#                ...                   ...             ... |       ...
# 116804918       11 121024101 - 121191490               * | 116804918
# 117779438        1   20154213 - 20160568               * | 117779438
# 118142757        6   42155405 - 42180056               * | 118142757
# ------
# seqinfo(369 sequences): 1 10 10_GL383545v1_alt ... X_KI270913v1_alt Y Y_KZ208924v1_fix
```

<!-- biocsetup-notes -->

## Note

This project has been set up using [BiocSetup](https://github.com/biocpy/biocsetup)
and [PyScaffold](https://pyscaffold.org/).
