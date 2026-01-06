from biocframe import BiocFrame
from genomicranges import GenomicRanges
import pytest
from orgdb import OrgDb

def test_orgdb_init(mock_orgdb):
    assert isinstance(mock_orgdb, OrgDb)
    assert mock_orgdb.conn is not None

def test_species(mock_orgdb):
    assert mock_orgdb.species == "Homo sapiens"

def test_columns(mock_orgdb):
    cols = mock_orgdb.columns()
    assert "ENTREZID" in cols
    assert "SYMBOL" in cols
    assert "GO" in cols
    assert "GENENAME" in cols

def test_keys(mock_orgdb):
    keys = mock_orgdb.keys("ENTREZID")
    assert "1" in keys
    assert "10" in keys
    assert "100" in keys
    assert len(keys) == 3

    syms = mock_orgdb.keys("SYMBOL")
    assert "A1BG" in syms
    assert "ADA" in syms

    with pytest.raises(ValueError):
        mock_orgdb.keys("INVALID_TYPE")

def test_select_simple(mock_orgdb):
    res = mock_orgdb.select(keys="1", columns=["SYMBOL"], keytype="ENTREZID")
    assert isinstance(res, BiocFrame)
    assert len(res) == 1
    assert res.get_column("ENTREZID")[0] == "1"
    assert res.get_column("SYMBOL")[0] == "A1BG"

def test_select_multikey(mock_orgdb):
    res = mock_orgdb.select(keys=["1", "10"], columns=["SYMBOL"], keytype="ENTREZID")
    assert len(res) == 2
    
    symbols = res.get_column("SYMBOL")
    assert "A1BG" in symbols
    assert "NAT2" in symbols

def test_select_go_expansion(mock_orgdb):
    res = mock_orgdb.select(keys="1", columns=["GO"], keytype="ENTREZID")
    
    col_names = list(res.column_names)
    assert "GO" in col_names
    assert "EVIDENCE" in col_names
    assert "ONTOLOGY" in col_names
    
    assert len(res) == 2
    go_ids = res.get_column("GO")
    assert "GO:0000001" in go_ids
    assert "GO:0000002" in go_ids

def test_select_many_to_one(mock_orgdb):
    res = mock_orgdb.select(keys="AAC2", columns=["ENTREZID"], keytype="ALIAS")
    assert len(res) == 1
    assert res.get_column("ENTREZID")[0] == "10"

def test_mapIds(mock_orgdb):
    keys = ["1", "10", "100"]
    
    res = mock_orgdb.mapIds(keys, column="SYMBOL", keytype="ENTREZID")
    assert isinstance(res, dict)
    assert res["1"] == "A1BG"
    assert res["10"] == "NAT2"
    
    res_list = mock_orgdb.mapIds(["1"], column="GO", keytype="ENTREZID", multiVals="list")
    assert isinstance(res_list["1"], list)
    assert len(res_list["1"]) == 2
    assert "GO:0000001" in res_list["1"]

def test_genes_genomicranges(mock_orgdb):
    gr = mock_orgdb.genes()
    assert isinstance(gr, GenomicRanges)
    assert len(gr) == 2
    
    names = list(gr.names)
    idx = names.index("1")
    assert str(gr.seqnames[idx]) == "chr19"
    assert gr.start[idx] == 58346806
    assert gr.end[idx] == 58353492
    
    assert "gene_id" in gr.mcols.column_names
    assert gr.mcols.get_column("gene_id")[idx] == "1"