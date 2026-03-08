"""PyVis-based knowledge graph renderer with Obsidian theme."""

from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx
from pyvis.network import Network


@dataclass
class GraphNode:
    id: str
    label: str
    path: str
    is_center: bool
    score: float
    folder: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class GraphEdge:
    source: str
    target: str
    edge_type: str  # "wikilink", "semantic", "both"
    weight: float


# Obsidian-inspired palette
FOLDER_COLORS = {
    "000-SLIPBOX": "#B4A7FA",
    "001-INBOX": "#FDE68A",
    "002-PRIVATE": "#FCA5A5",
    "003-RESOURCES": "#7DDCB5",
    "004-ARCHIVE": "#CBD5E1",
    "notes": "#93C5FD",
}

CENTER_COLOR = "#FFD700"  # gold
DEFAULT_COLOR = "#78909C"


def _folder_color(path: str) -> str:
    parts = path.split('/')
    if parts:
        for prefix, color in FOLDER_COLORS.items():
            if parts[0].startswith(prefix) or parts[0] == prefix:
                return color
    return DEFAULT_COLOR


class KnowledgeGraphRenderer:
    """Render knowledge graph as interactive pyvis HTML."""

    def render(
        self,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
        output_path: str,
        title: str,
    ) -> bool:
        G = nx.Graph()

        for n in nodes:
            color = CENTER_COLOR if n.is_center else _folder_color(n.path)
            size = 25 if n.is_center else max(8, int(n.score * 20))
            G.add_node(
                n.id,
                label=n.label,
                title=f"{n.path}\nScore: {n.score:.3f}",
                color=color,
                size=size,
                shape="dot",
                font={'size': 14 if n.is_center else 11,
                      'color': '#dcddde',
                      'strokeWidth': 2,
                      'strokeColor': '#1e1e1e'},
            )

        for e in edges:
            if e.edge_type == "wikilink":
                style = {'color': '#7DDCB5', 'opacity': 0.8}
                width = 1.5
                dashes = False
            elif e.edge_type == "both":
                style = {'color': '#B4A7FA', 'opacity': 0.9}
                width = 2.5
                dashes = False
            else:  # semantic
                style = {'color': '#FDBA8C', 'opacity': 0.4}
                width = max(0.5, e.weight * 2)
                dashes = True

            G.add_edge(
                e.source, e.target,
                title=f"{e.edge_type} ({e.weight:.3f})",
                color=style,
                width=width,
                dashes=dashes,
            )

        net = Network(
            height="100vh",
            width="100%",
            bgcolor="#1e1e1e",
            font_color="#dcddde",
            directed=False,
            select_menu=False,
            filter_menu=False,
        )
        net.from_nx(G)
        net.set_options('''{
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -80,
                    "centralGravity": 0.01,
                    "springLength": 120,
                    "springConstant": 0.08,
                    "damping": 0.4
                },
                "solver": "forceAtlas2Based",
                "stabilization": {"iterations": 150}
            },
            "interaction": {
                "hover": true,
                "tooltipDelay": 100,
                "navigationButtons": false,
                "keyboard": {"enabled": true}
            }
        }''')

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        net.save_graph(output_path)

        # Inject title and legend into HTML
        _inject_html_extras(output_path, title)
        return True


def _inject_html_extras(path: str, title: str):
    """Inject title bar and edge legend into the generated HTML."""
    html = Path(path).read_text(encoding='utf-8')
    legend = f'''
    <div style="position:fixed;top:10px;left:10px;z-index:1000;
                background:#262626;padding:12px 16px;border-radius:8px;
                border:1px solid #3e3e3e;font-family:monospace;color:#dcddde;font-size:13px;">
        <div style="font-size:15px;font-weight:bold;margin-bottom:8px;">{title}</div>
        <div><span style="color:#7DDCB5;">━━</span> wikilink (existing)</div>
        <div><span style="color:#FDBA8C;">╌╌</span> semantic (discovered)</div>
        <div><span style="color:#B4A7FA;">━━</span> both</div>
        <div style="margin-top:6px;"><span style="color:#FFD700;">●</span> center document</div>
    </div>
    '''
    html = html.replace('<body>', f'<body>{legend}', 1)
    Path(path).write_text(html, encoding='utf-8')
