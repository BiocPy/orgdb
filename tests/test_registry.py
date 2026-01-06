import pytest
from orgdb import OrgDbRegistry

@pytest.fixture
def registry(tmp_path):
    """Initialize registry with a temp cache dir."""
    return OrgDbRegistry(cache_dir=tmp_path / "cache")

def test_registry_init(registry):
    assert isinstance(registry, OrgDbRegistry)
    assert "org.Hs.eg.db" in registry.list_orgdb()
    
def test_get_record(registry):
    rec = registry.get_record("org.Hs.eg.db")
    assert rec.orgdb_id == "org.Hs.eg.db"
    assert rec.species == "Hs"
    assert rec.id_type == "eg"
    assert rec.url.endswith("org.Hs.eg.db.sqlite")

def test_invalid_id(registry):
    with pytest.raises(KeyError):
        registry.get_record("org.Invalid.db")
