import json
import pytest
from pathlib import Path
from src.features.graph_related import GraphIndex

FIXTURE = {
    "directed": False, "multigraph": False, "graph": {},
    "nodes": [
        {"id": "aggregate_root", "label": "Aggregate Root", "source_file": "Aggregate.md"},
        {"id": "entity", "label": "Entity", "source_file": "Entity.md"},
        {"id": "value_object", "label": "Value Object", "source_file": "ValueObject.md"},
        {"id": "repository", "label": "Repository", "source_file": "Repository.md"},
    ],
    "links": [
        {"source": "aggregate_root", "target": "entity", "relation": "references",
         "confidence": "EXTRACTED", "confidence_score": 1.0, "weight": 1.0},
        {"source": "aggregate_root", "target": "value_object", "relation": "semantically_similar_to",
         "confidence": "INFERRED", "confidence_score": 0.85, "weight": 1.0},
        {"source": "aggregate_root", "target": "repository", "relation": "conceptually_related_to",
         "confidence": "INFERRED", "confidence_score": 0.6, "weight": 1.0},
    ],
}

@pytest.fixture
def graph_file(tmp_path):
    p = tmp_path / "graph.json"
    p.write_text(json.dumps(FIXTURE))
    return str(p)

def test_filter_keeps_extracted_and_high_inferred_drops_rest(graph_file):
    idx = GraphIndex(graph_file, confidence_threshold=0.8)
    neighbors = dict(idx.filtered_neighbors("aggregate_root"))
    assert "entity" in neighbors            # EXTRACTED
    assert "value_object" in neighbors      # INFERRED 0.85 >= 0.8
    assert "repository" not in neighbors    # INFERRED 0.6 < 0.8
    assert neighbors["entity"] == pytest.approx(1.0)
    assert neighbors["value_object"] == pytest.approx(0.85)

def test_source_file_lookup(graph_file):
    idx = GraphIndex(graph_file, confidence_threshold=0.8)
    assert idx.source_file_of("entity") == "Entity.md"


from src.features.graph_related import to_vault_relative

def test_to_vault_relative_bare_filename():
    assert to_vault_relative("Aggregate.md", "003-RESOURCES/DDD") == "003-RESOURCES/DDD/Aggregate.md"

def test_to_vault_relative_already_prefixed():
    assert to_vault_relative("003-RESOURCES/DDD/Aggregate.md", "003-RESOURCES/DDD") == "003-RESOURCES/DDD/Aggregate.md"

def test_to_vault_relative_partial_prefix():
    assert to_vault_relative("DDD/Aggregate.md", "003-RESOURCES/DDD") == "003-RESOURCES/DDD/Aggregate.md"

def test_to_vault_relative_strips_leading_dotslash():
    assert to_vault_relative("./Aggregate.md", "003-RESOURCES/DDD") == "003-RESOURCES/DDD/Aggregate.md"


from src.features.graph_related import project, GraphRelatedDoc

def test_project_maps_concepts_to_docs_and_ranks(graph_file):
    idx = GraphIndex(graph_file, confidence_threshold=0.8)
    results = project(idx, "003-RESOURCES/DDD/Aggregate.md", "003-RESOURCES/DDD", top_k=10)
    paths = [r.doc_path for r in results]
    # entity(1.0), value_object(0.85) included; repository(0.6<0.8) excluded; self excluded
    assert "003-RESOURCES/DDD/Entity.md" in paths
    assert "003-RESOURCES/DDD/ValueObject.md" in paths
    assert "003-RESOURCES/DDD/Repository.md" not in paths
    assert "003-RESOURCES/DDD/Aggregate.md" not in paths
    # descending score
    assert results[0].doc_path == "003-RESOURCES/DDD/Entity.md"
    assert results[0].score >= results[1].score

def test_project_unknown_doc_returns_empty(graph_file):
    idx = GraphIndex(graph_file, confidence_threshold=0.8)
    assert project(idx, "003-RESOURCES/DDD/Nonexistent.md", "003-RESOURCES/DDD") == []


from src.features.graph_related import compute_novelty

def test_compute_novelty_returns_graph_minus_vector():
    graph = ["a.md", "b.md", "c.md"]
    vector = ["b.md", "x.md"]
    assert compute_novelty(graph, vector) == ["a.md", "c.md"]

def test_compute_novelty_preserves_graph_order():
    assert compute_novelty(["c.md", "a.md"], []) == ["c.md", "a.md"]


from src.features.graph_related import vector_paths_vault_relative

class _Doc:
    def __init__(self, path): self.path = path

class _Res:
    def __init__(self, path, score): self.document = _Doc(path); self.similarity_score = score

def test_vector_paths_vault_relative_strips_vault_prefix():
    vault = "/Users/x/vault"
    results = [_Res("/Users/x/vault/003-RESOURCES/DDD/Entity.md", 0.7),
               _Res("003-RESOURCES/DDD/Repository.md", 0.6)]
    assert vector_paths_vault_relative(results, vault) == [
        "003-RESOURCES/DDD/Entity.md", "003-RESOURCES/DDD/Repository.md"]


from src.features.graph_related import deterministic_sample

def test_deterministic_sample_is_stable_and_even():
    docs = [f"{i}.md" for i in range(20)]
    s1 = deterministic_sample(docs, 4)
    s2 = deterministic_sample(list(reversed(docs)), 4)
    assert s1 == s2            # input order independent (sort-based)
    assert len(s1) == 4
    assert s1 == sorted(s1)   # sorted

def test_deterministic_sample_n_larger_than_corpus():
    docs = ["b.md", "a.md"]
    assert deterministic_sample(docs, 8) == ["a.md", "b.md"]


# ── Finding 1: to_absolute helper ────────────────────────────────────────────

from src.features.graph_related import to_absolute

def test_to_absolute_joins_vault_and_relative():
    vault = "/Users/x/vault"
    rel = "003-RESOURCES/DDD/Aggregate.md"
    assert to_absolute(vault, rel) == "/Users/x/vault/003-RESOURCES/DDD/Aggregate.md"

def test_to_absolute_trailing_slash_vault():
    # Path handles trailing slash cleanly
    vault = "/Users/x/vault/"
    rel = "003-RESOURCES/DDD/X.md"
    assert to_absolute(vault, rel) == "/Users/x/vault/003-RESOURCES/DDD/X.md"


# ── Finding 2: directed graph normalization ───────────────────────────────────

DIRECTED_FIXTURE = {
    "directed": True, "multigraph": False, "graph": {},
    "nodes": [
        {"id": "seed_node", "label": "Seed", "source_file": "Seed.md"},
        {"id": "nbr_node",  "label": "Nbr",  "source_file": "Nbr.md"},
    ],
    "links": [
        # Edge goes seed_node → nbr_node only (directed)
        {"source": "seed_node", "target": "nbr_node", "relation": "references",
         "confidence": "EXTRACTED", "confidence_score": 1.0, "weight": 1.0},
    ],
}

MULTIGRAPH_FIXTURE = {
    "directed": False, "multigraph": True, "graph": {},
    "nodes": [
        {"id": "A", "label": "A", "source_file": "A.md"},
        {"id": "B", "label": "B", "source_file": "B.md"},
    ],
    "links": [
        # Two parallel edges A─B; second has higher confidence_score
        {"source": "A", "target": "B", "key": 0, "relation": "references",
         "confidence": "INFERRED", "confidence_score": 0.7, "weight": 1.0},
        {"source": "A", "target": "B", "key": 1, "relation": "semantically_similar_to",
         "confidence": "INFERRED", "confidence_score": 0.9, "weight": 1.0},
    ],
}

@pytest.fixture
def directed_graph_file(tmp_path):
    p = tmp_path / "directed.json"
    p.write_text(json.dumps(DIRECTED_FIXTURE))
    return str(p)

@pytest.fixture
def multigraph_file(tmp_path):
    p = tmp_path / "multi.json"
    p.write_text(json.dumps(MULTIGRAPH_FIXTURE))
    return str(p)

def test_directed_graph_normalized_to_undirected(directed_graph_file):
    """After normalization, filtered_neighbors works from the directed-source side."""
    idx = GraphIndex(directed_graph_file, confidence_threshold=0.8)
    neighbors = dict(idx.filtered_neighbors("seed_node"))
    # EXTRACTED edge → neighbor must appear
    assert "nbr_node" in neighbors

def test_directed_graph_bidirectional_after_normalization(directed_graph_file):
    """Normalization makes the edge bidirectional: lookup from nbr_node must also find seed_node."""
    idx = GraphIndex(directed_graph_file, confidence_threshold=0.8)
    neighbors = dict(idx.filtered_neighbors("nbr_node"))
    assert "seed_node" in neighbors

def test_multigraph_collapses_keeping_highest_confidence_score(multigraph_file):
    """Parallel edges are collapsed; the edge with confidence_score=0.9 survives (>= 0.8 threshold)."""
    idx = GraphIndex(multigraph_file, confidence_threshold=0.8)
    neighbors = dict(idx.filtered_neighbors("A"))
    # The higher-score INFERRED edge (0.9) should survive the threshold and collapse
    assert "B" in neighbors
