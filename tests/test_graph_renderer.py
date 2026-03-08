import pytest
import tempfile
from pathlib import Path
from src.visualization.graph_renderer import KnowledgeGraphRenderer, GraphNode, GraphEdge


def test_render_empty_graph():
    renderer = KnowledgeGraphRenderer()
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
        result = renderer.render([], [], f.name, "Test Graph")
    assert result is True
    assert Path(f.name).exists()
    content = Path(f.name).read_text()
    assert "Test Graph" in content


def test_render_with_nodes_and_edges():
    nodes = [
        GraphNode(id="center", label="Center Doc", path="a.md", is_center=True, score=1.0),
        GraphNode(id="related", label="Related Doc", path="b.md", is_center=False, score=0.8),
    ]
    edges = [
        GraphEdge(source="center", target="related", edge_type="semantic", weight=0.8),
    ]
    renderer = KnowledgeGraphRenderer()
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
        result = renderer.render(nodes, edges, f.name, "Test")
    assert result is True
    content = Path(f.name).read_text()
    assert "Center Doc" in content
