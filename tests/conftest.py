"""
    Dummy conftest.py for orgdb.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    - https://docs.pytest.org/en/stable/fixture.html
    - https://docs.pytest.org/en/stable/writing_plugins.html
"""

import sqlite3 
from orgdb import OrgDb
import pytest

@pytest.fixture
def mock_orgdb_path(tmp_path):
    """Create a temporary SQLite file with a standard OrgDb schema and sample data."""
    db_path = tmp_path / "mock_org.sqlite"
    conn = sqlite3.connect(db_path)

    # 1. metadata table
    conn.execute("CREATE TABLE metadata (name VARCHAR(80) PRIMARY KEY, value VARCHAR(255))")
    conn.execute("INSERT INTO metadata VALUES ('ORGANISM', 'Homo sapiens')")
    conn.execute("INSERT INTO metadata VALUES ('DBSCHEMA', 'H. sapiens')")

    # 2. genes table (Central table)
    # _id is internal PK, gene_id is Entrez ID
    conn.execute("""
        CREATE TABLE genes (
            _id INTEGER PRIMARY KEY,
            gene_id VARCHAR(10) NOT NULL UNIQUE
        )
    """)
    # Sample Genes:
    # 1: 1 (A1BG)
    # 2: 10 (NAT2)
    # 3: 100 (ADA)
    conn.execute("INSERT INTO genes VALUES (1, '1')")
    conn.execute("INSERT INTO genes VALUES (2, '10')")
    conn.execute("INSERT INTO genes VALUES (3, '100')")

    # 3. gene_info table (Symbol, Gene Name)
    conn.execute("""
        CREATE TABLE gene_info (
            _id INTEGER NOT NULL,
            gene_name VARCHAR(255) NOT NULL,
            symbol VARCHAR(80) NOT NULL,
            FOREIGN KEY (_id) REFERENCES genes (_id)
        )
    """)
    conn.execute("INSERT INTO gene_info VALUES (1, 'Alpha-1-B glycoprotein', 'A1BG')")
    conn.execute("INSERT INTO gene_info VALUES (2, 'N-acetyltransferase 2', 'NAT2')")
    conn.execute("INSERT INTO gene_info VALUES (3, 'Adenosine deaminase', 'ADA')")

    # 4. go table (GO terms)
    # Note: A gene can have multiple GO terms
    conn.execute("""
        CREATE TABLE go (
            _id INTEGER NOT NULL,
            go_id CHAR(10) NOT NULL,
            evidence CHAR(3) NOT NULL,
            ontology CHAR(10) NOT NULL,
            FOREIGN KEY (_id) REFERENCES genes (_id)
        )
    """)
    # Gene 1 (A1BG) -> GO:0000001 (CC), GO:0000002 (MF)
    conn.execute("INSERT INTO go VALUES (1, 'GO:0000001', 'IEA', 'CC')")
    conn.execute("INSERT INTO go VALUES (1, 'GO:0000002', 'TAS', 'MF')")
    # Gene 2 (NAT2) -> GO:0000003 (BP)
    conn.execute("INSERT INTO go VALUES (2, 'GO:0000003', 'IMP', 'BP')")

    # 5. chromosome_locations table (Genomic coordinates)
    conn.execute("""
        CREATE TABLE chromosome_locations (
            _id INTEGER NOT NULL,
            seqname VARCHAR(20) NOT NULL,
            start_location INTEGER NOT NULL,
            end_location INTEGER NOT NULL,
            FOREIGN KEY (_id) REFERENCES genes (_id)
        )
    """)
    # A1BG on chr19
    conn.execute("INSERT INTO chromosome_locations VALUES (1, 'chr19', 58346806, 58353492)")
    # NAT2 on chr8
    conn.execute("INSERT INTO chromosome_locations VALUES (2, 'chr8', 18248755, 18258723)")

    # 6. alias table (Aliases)
    conn.execute("""
        CREATE TABLE alias (
            _id INTEGER NOT NULL,
            alias_symbol VARCHAR(80) NOT NULL,
            FOREIGN KEY (_id) REFERENCES genes (_id)
        )
    """)
    conn.execute("INSERT INTO alias VALUES (2, 'AAC2')")

    conn.commit()
    conn.close()
    return str(db_path)

@pytest.fixture
def mock_orgdb(mock_orgdb_path):
    """Return an open OrgDb instance using the mock database."""
    db = OrgDb(mock_orgdb_path)
    yield db
    db.close()