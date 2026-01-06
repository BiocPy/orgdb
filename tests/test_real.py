from orgdb import OrgDb, OrgDbRegistry

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def test_real_orgdb_workflow(tmp_path):
    registry = OrgDbRegistry(cache_dir=tmp_path / "cache")
    orgdb_id = "org.Mm.eg.db"

    assert orgdb_id in registry.list_orgdb()

    orgdb = registry.load_db(orgdb_id, force=True)
    assert isinstance(orgdb, OrgDb)

    res = orgdb.select(
        keytype="GO",
        keys=[
             "GO:0048709", #
             "GO:0048699",
             "GO:0048143"],
        columns="SYMBOL")
    
    assert res.shape == (104, 4)
    orgdb.close()
