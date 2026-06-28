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
