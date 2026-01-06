import sqlite3
from typing import Dict, List, Union

from biocframe import BiocFrame
from genomicranges import GenomicRanges
from iranges import IRanges


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
