import sqlite3
from typing import Dict, List, Union

from biocframe import BiocFrame
from genomicranges import GenomicRanges
from iranges import IRanges

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


class OrgDb:
    """Interface for accessing OrgDb SQLite databases in Python."""

    def __init__(self, dbpath: str):
        """Initialize the OrgDb object.

        Args:
            dbpath:
                Path to the SQLite database file.
        """
        print(dbpath)
        self.dbpath = dbpath
        self.conn = sqlite3.connect(dbpath)
        self.conn.row_factory = sqlite3.Row
        self._metadata = None
        self._table_map = self._define_tables()

    def _query_as_biocframe(self, query: str, params: tuple = ()) -> BiocFrame:
        """Execute a SQL query and return the result as a BiocFrame."""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()

        if not results:
            if cursor.description:
                col_names = [desc[0] for desc in cursor.description]
                return BiocFrame({}, column_names=col_names)
            return BiocFrame({})

        col_names = [desc[0] for desc in cursor.description]
        columns_data = list(zip(*results))

        data_dict = {}
        for i, name in enumerate(col_names):
            data_dict[name] = list(columns_data[i])

        return BiocFrame(data_dict)

    @property
    def metadata(self) -> BiocFrame:
        """Get the metadata table from the database."""
        if self._metadata is None:
            self._metadata = self._query_as_biocframe("SELECT * FROM metadata")
        return self._metadata

    @property
    def species(self) -> str:
        """Get the organism/species name from metadata."""
        meta = self.metadata

        if "name" in meta.column_names and "value" in meta.column_names:
            names = meta.get_column("name")
            values = meta.get_column("value")
            for n, v in zip(names, values):
                if n in ["ORGANISM", "Organism", "Genus and Species"]:
                    return v
        return "Unknown"

    def _define_tables(self) -> Dict[str, tuple]:
        """Define the mapping between column names and (table, field).

        Mirrors .definePossibleTables from R/methods-geneCentricDbs.R
        """
        species = self.species
        db_class = "OrgDb"

        # Mapping: COLUMN_NAME -> (TABLE_NAME, COLUMN_NAME)
        mapping = {
            "ENTREZID": ("genes", "gene_id"),
            "PFAM": ("pfam", "pfam_id"),
            "IPI": ("pfam", "ipi_id"),
            "PROSITE": ("prosite", "prosite_id"),
            "ACCNUM": ("accessions", "accession"),
            "ALIAS": ("alias", "alias_symbol"),
            "ALIAS2EG": ("alias", "alias_symbol"),
            "ALIAS2PROBE": ("alias", "alias_symbol"),
            "CHR": ("chromosomes", "chromosome"),
            "CHRLOCCHR": ("chromosome_locations", "seqname"),
            "CHRLOC": ("chromosome_locations", "start_location"),
            "CHRLOCEND": ("chromosome_locations", "end_location"),
            "ENZYME": ("ec", "ec_number"),
            "MAP": ("cytogenetic_locations", "cytogenetic_location"),
            "PATH": ("kegg", "path_id"),
            "PMID": ("pubmed", "pubmed_id"),
            "REFSEQ": ("refseq", "accession"),
            "SYMBOL": ("gene_info", "symbol"),
            "GENETYPE": ("genetype", "gene_type"),
            "ENSEMBL": ("ensembl", "ensembl_id"),
            "ENSEMBLPROT": ("ensembl_prot", "prot_id"),
            "ENSEMBLTRANS": ("ensembl_trans", "trans_id"),
            "GENENAME": ("gene_info", "gene_name"),
            "UNIPROT": ("uniprot", "uniprot_id"),
            "GO": ("go", "go_id"),
            "EVIDENCE": ("go", "evidence"),
            "ONTOLOGY": ("go", "ontology"),
            "GOALL": ("go_all", "go_id"),
            "EVIDENCEALL": ("go_all", "evidence"),
            "ONTOLOGYALL": ("go_all", "ontology"),
        }

        if db_class == "OrgDb":
            if "ALIAS2PROBE" in mapping:
                del mapping["ALIAS2PROBE"]

        if db_class == "ChipDb":
            mapping["PROBEID"] = ("c.probes", "probe_id")

        if species == "Anopheles gambiae":
            for k in [
                "ALIAS",
                "ALIAS2PROBE",
                "MAP",
                "CHRLOC",
                "CHRLOCEND",
                "GENETYPE",
                "CHRLOCCHR",
                "PFAM",
                "IPI",
                "PROSITE",
            ]:
                mapping.pop(k, None)

        elif species == "Arabidopsis thaliana":
            mapping.update(
                {
                    "TAIR": ("genes", "gene_id"),
                    "ARACYC": ("aracyc", "pathway_name"),
                    "ARACYCENZYME": ("enzyme", "ec_name"),
                }
            )
            for k in [
                "ACCNUM",
                "ALIAS",
                "ALIAS2EG",
                "ALIAS2PROBE",
                "MAP",
                "GENETYPE",
                "PFAM",
                "IPI",
                "PROSITE",
                "ENSEMBL",
                "ENSEMBLPROT",
                "ENSEMBLTRANS",
                "UNIPROT",
                "ENTREZID",
                "CHR",
            ]:
                mapping.pop(k, None)

            # "re-add" these
            mapping["ENTREZID"] = ("entrez_genes", "gene_id")
            mapping["CHR"] = ("gene_info", "chromosome")

        elif species == "Bos taurus":
            mapping.pop("MAP", None)

        elif species == "Caenorhabditis elegans":
            mapping["WORMBASE"] = ("wormbase", "wormbase_id")
            for k in ["MAP", "PFAM", "GENETYPE", "IPI", "PROSITE"]:
                mapping.pop(k, None)

        elif species == "Canis familiaris":
            for k in ["MAP", "PFAM", "IPI", "PROSITE"]:
                mapping.pop(k, None)

        elif species == "Drosophila melanogaster":
            mapping.update(
                {
                    "FLYBASE": ("flybase", "flybase_id"),
                    "FLYBASECG": ("flybase_cg", "flybase_cg_id"),
                    "FLYBASEPROT": ("flybase_prot", "prot_id"),
                }
            )
            for k in ["PFAM", "IPI", "PROSITE"]:
                mapping.pop(k, None)

        elif species == "Danio rerio":
            mapping["ZFIN"] = ("zfin", "zfin_id")
            for k in ["MAP", "GENETYPE"]:
                mapping.pop(k, None)

        elif species == "Escherichia coli":
            for k in [
                "CHR",
                "MAP",
                "GENETYPE",
                "CHRLOC",
                "CHRLOCEND",
                "CHRLOCCHR",
                "PFAM",
                "IPI",
                "PROSITE",
                "ENSEMBL",
                "ENSEMBLPROT",
                "ENSEMBLTRANS",
                "UNIPROT",
            ]:
                mapping.pop(k, None)

        elif species == "Gallus gallus":
            mapping.pop("MAP", None)

        elif species == "Homo sapiens":
            mapping["OMIM"] = ("omim", "omim_id")
            mapping["UCSCKG"] = ("ucsc", "ucsc_id")

        elif species == "Mus musculus":
            mapping["MGI"] = ("mgi", "mgi_id")
            mapping.pop("MAP", None)

        elif species == "Macaca mulatta":
            for k in ["ALIAS", "ALIAS2PROBE", "MAP", "PFAM", "IPI", "PROSITE"]:
                mapping.pop(k, None)

        elif species == "Plasmodium falciparum":
            mapping["ORF"] = ("genes", "gene_id")
            # Drops
            for k in [
                "ENTREZID",
                "ACCNUM",
                "ALIAS",
                "ALIAS2PROBE",
                "ALIAS2EG",
                "CHR",
                "CHRLOC",
                "CHRLOCEND",
                "CHRLOCCHR",
                "GENETYPE",
                "MAP",
                "PMID",
                "REFSEQ",
                "PFAM",
                "IPI",
                "PROSITE",
                "ENSEMBL",
                "ENSEMBLPROT",
                "ENSEMBLTRANS",
                "UNIPROT",
            ]:
                mapping.pop(k, None)
            mapping["ALIAS"] = ("alias", "alias_symbol")

        elif species == "Pan troglodytes":
            for k in ["ALIAS", "ALIAS2PROBE", "MAP", "GENETYPE", "PFAM", "IPI", "PROSITE"]:
                mapping.pop(k, None)

        elif species == "Rattus norvegicus":
            mapping.pop("MAP", None)

        elif species == "Saccharomyces cerevisiae":
            mapping.update(
                {
                    "ORF": ("gene2systematic", "systematic_name"),
                    "DESCRIPTION": ("chromosome_features", "feature_description"),
                    "COMMON": ("gene2systematic", "gene_name"),
                    "INTERPRO": ("interpro", "interpro_id"),
                    "SMART": ("smart", "smart_id"),
                    "SGD": ("sgd", "sgd_id"),
                }
            )
            for k in [
                "ACCNUM",
                "MAP",
                "SYMBOL",
                "GENETYPE",
                "PROSITE",
                "ALIAS",
                "ALIAS2EG",
                "ALIAS2PROBE",
                "CHRLOC",
                "CHRLOCEND",
                "CHRLOCCHR",
                "GENENAME",
                "IPI",
                "CHR",
            ]:
                mapping.pop(k, None)
            mapping.update(
                {
                    "ALIAS": ("gene2alias", "alias"),
                    "CHRLOC": ("chromosome_features", "start"),
                    "CHRLOCEND": ("chromosome_features", "stop"),
                    "CHRLOCCHR": ("chromosome_features", "chromosome"),
                    "GENENAME": ("sgd", "gene_name"),
                    "CHR": ("chromosome_features", "chromosome"),
                }
            )

        elif species == "Sus scrofa":
            for k in [
                "MAP",
                "CHRLOC",
                "CHRLOCEND",
                "CHRLOCCHR",
                "PFAM",
                "IPI",
                "PROSITE",
                "ENSEMBL",
                "ENSEMBLPROT",
                "ENSEMBLTRANS",
            ]:
                mapping.pop(k, None)

        elif species == "Xenopus laevis":
            for k in [
                "ALIAS",
                "ALIAS2PROBE",
                "MAP",
                "CHRLOC",
                "CHRLOCEND",
                "CHRLOCCHR",
                "PFAM",
                "IPI",
                "PROSITE",
                "ENSEMBL",
                "ENSEMBLPROT",
                "ENSEMBLTRANS",
            ]:
                mapping.pop(k, None)

        stock_species = [
            "Anopheles gambiae",
            "Arabidopsis thaliana",
            "Bos taurus",
            "Caenorhabditis elegans",
            "Canis familiaris",
            "Drosophila melanogaster",
            "Danio rerio",
            "Escherichia coli",
            "Gallus gallus",
            "Homo sapiens",
            "Mus musculus",
            "Macaca mulatta",
            "Plasmodium falciparum",
            "Pan troglodytes",
            "Rattus norvegicus",
            "Saccharomyces cerevisiae",
            "Sus scrofa",
            "Xenopus laevis",
        ]

        if species not in stock_species:
            mapping = {
                "ENTREZID": ("genes", "gene_id"),
                "ACCNUM": ("accessions", "accession"),
                "ALIAS": ("alias", "alias_symbol"),
                "ALIAS2EG": ("alias", "alias_symbol"),
                "ALIAS2PROBE": ("alias", "alias_symbol"),
                "CHR": ("chromosomes", "chromosome"),
                "PMID": ("pubmed", "pubmed_id"),
                "REFSEQ": ("refseq", "accession"),
                "SYMBOL": ("gene_info", "symbol"),
                "GENETYPE": ("genetype", "gene_type"),
                "GENENAME": ("gene_info", "gene_name"),
                "GO": ("go", "go_id"),
                "EVIDENCE": ("go", "evidence"),
                "ONTOLOGY": ("go", "ontology"),
            }

        if db_class == "GODb":
            mapping = {
                "GOID": ("go_term", "go_id"),
                "TERM": ("go_term", "term"),
                "ONTOLOGY": ("go_term", "ontology"),
                "DEFINITION": ("go_term", "definition"),
            }

        return mapping

    def columns(self) -> List[str]:
        """List all available columns/keytypes."""
        return list(self._table_map.keys())

    def keytypes(self) -> List[str]:
        """List all available keytypes (same as columns)."""
        return self.columns()

    def keys(self, keytype: str) -> List[str]:
        """Return keys for the given keytype."""
        if keytype not in self._table_map:
            raise ValueError(f"Invalid keytype: {keytype}. Use columns() to see valid options.")

        table, field = self._table_map[keytype]
        query = f"SELECT DISTINCT {field} FROM {table}"

        # check if table exists or let sqlite fail
        try:
            bf = self._query_as_biocframe(query)
            if bf.shape[0] > 0:
                return [str(x) for x in bf.get_column(field)]
            return []
        except sqlite3.OperationalError:
            return []

    def _expand_cols(self, cols: List[str]) -> List[str]:
        """Expand columns like GO into GO, EVIDENCE, ONTOLOGY."""
        new_cols = []
        for c in cols:
            new_cols.append(c)
            if c == "GO":
                if "EVIDENCE" not in new_cols:
                    new_cols.append("EVIDENCE")
                if "ONTOLOGY" not in new_cols:
                    new_cols.append("ONTOLOGY")
            if c == "CHRLOC":
                if "CHRLOCCHR" not in new_cols:
                    new_cols.append("CHRLOCCHR")
        return list(set(new_cols))  # remove duplicates

    def select(self, keys: Union[List[str], str], columns: Union[List[str], str], keytype: str) -> BiocFrame:
        """Retrieve data from the database.

        Args:
            keys:
                A list of keys to select.

            columns:
                List of columns to retrieve.

            keytype:
                The type of the provided keys (must be one of columns()).
        """
        if isinstance(keys, str):
            keys = [keys]

        if isinstance(columns, str):
            columns = [columns]

        if keytype not in self._table_map:
            raise ValueError(f"Invalid keytype: {keytype}")

        req_cols = columns + [keytype]
        req_cols = self._expand_cols(req_cols)

        tables_needed = set()
        fields_to_select = []

        for col in req_cols:
            if col not in self._table_map:
                continue
            t, f = self._table_map[col]
            tables_needed.add(t)
            fields_to_select.append(f"{t}.{f} AS {col}")

        base_table = "genes"
        kt_table, kt_field = self._table_map[keytype]
        select_clause = ", ".join(fields_to_select)
        joins = []
        sorted_tables = sorted(list(tables_needed))

        if kt_table not in tables_needed:
            pass

        from_clause = f"FROM {base_table}"

        for t in sorted_tables:
            if t == base_table:
                continue
            joins.append(f"LEFT JOIN {t} USING (_id)")

        if kt_table != base_table and kt_table not in sorted_tables:
            joins.append(f"LEFT JOIN {kt_table} USING (_id)")

        join_clause = " ".join(joins)

        placeholders = ",".join("?" * len(keys))
        where_clause = f"WHERE {kt_table}.{kt_field} IN ({placeholders})"

        sql = f"SELECT {select_clause} {from_clause} {join_clause} {where_clause}"

        return self._query_as_biocframe(sql, tuple(keys))

    def mapIds(
        self, keys: Union[List[str], str], column: str, keytype: str, multiVals: str = "first"
    ) -> Union[dict, list]:
        """Map keys to a specific column. A wrapper around select.

        Args:
            keys:
                Keys to map.

            column:
                The column to map to.

            keytype:
                The ID type of the keys.

            multiVals:
                How to handle multiple values ('first', 'list', 'filter').
        """
        bf = self.select(keys, [column], keytype)

        kt_data = bf.get_column(keytype)
        col_data = bf.get_column(column)

        res = {}
        for k, v in zip(kt_data, col_data):
            k = str(k)
            if k not in res:
                res[k] = []
            if v is not None:
                res[k].append(v)

        final_res = {}
        for k in keys:
            k = str(k)
            vals = res.get(k, [])

            if multiVals == "first":
                final_res[k] = vals[0] if vals else None
            elif multiVals == "list":
                final_res[k] = vals
            elif multiVals == "filter":
                if len(vals) == 1:
                    final_res[k] = vals[0]
            else:
                final_res[k] = vals[0] if vals else None

        if multiVals == "list":
            return final_res
        return final_res

    def genes(self) -> GenomicRanges:
        """Retrieve gene locations as GenomicRanges.

        Requires 'chromosome_locations' table in the DB.
        """
        try:
            self._query_as_biocframe("SELECT 1 FROM chromosome_locations LIMIT 1")
        except sqlite3.OperationalError:
            return GenomicRanges.empty()

        query = """
        SELECT 
            g.gene_id,
            c.seqname,
            c.start_location,
            c.end_location
        FROM genes g
        JOIN chromosome_locations c ON g._id = c._id
        """

        bf = self._query_as_biocframe(query)

        if bf.shape[0] == 0:
            return GenomicRanges.empty()

        names = [str(x) for x in bf.get_column("gene_id")]
        seqnames = [str(x) for x in bf.get_column("seqname")]
        starts = bf.get_column("start_location")
        ends = bf.get_column("end_location")

        widths = [abs(e - s) + 1 for s, e in zip(starts, ends)]
        strand = ["*"] * len(names)

        ranges = IRanges(start=starts, width=widths)
        mcols = BiocFrame({"gene_id": names}, row_names=names)

        return GenomicRanges(seqnames=seqnames, ranges=ranges, strand=strand, names=names, mcols=mcols)

    def close(self):
        """Close the database connection."""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
