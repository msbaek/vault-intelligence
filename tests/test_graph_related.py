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
