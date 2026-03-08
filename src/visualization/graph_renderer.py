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
    depth: int = 0
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
            # Depth-aware sizing: deeper nodes are smaller
            depth_factor = max(0.4, 1.0 - n.depth * 0.25)
            size = 25 if n.is_center else max(6, int(n.score * 20 * depth_factor))
            font_size = 14 if n.is_center else max(8, int(11 * depth_factor))
            opacity = max(0.4, 1.0 - n.depth * 0.2)
            G.add_node(
                n.id,
                label=n.label,
                title=f"{n.path}\nScore: {n.score:.3f}\nDepth: {n.depth}",
                color={'background': color, 'border': color,
                       'highlight': {'background': color, 'border': '#fff'},
                       'opacity': opacity},
                size=size,
                shape="dot",
                font={'size': font_size,
                      'color': '#dcddde',
                      'strokeWidth': 2,
                      'strokeColor': '#1e1e1e'},
                level=n.depth,  # custom attr for JS filtering
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

        max_depth = max(n.depth for n in nodes)
        _inject_html_extras(output_path, title, max_depth)
        return True


def _inject_html_extras(path: str, title: str, max_depth: int = 1):
    """Inject title bar, edge legend, and depth slider into the generated HTML."""
    html = Path(path).read_text(encoding='utf-8')

    # Depth slider (only show when multi-depth)
    slider_html = ""
    if max_depth > 1:
        slider_html = f'''
        <div style="margin-top:10px;padding-top:8px;border-top:1px solid #3e3e3e;">
            <label style="display:block;margin-bottom:4px;">
                Depth: <span id="depthValue">{max_depth}</span>
            </label>
            <input type="range" id="depthSlider" min="1" max="{max_depth}" value="{max_depth}"
                   style="width:100%;accent-color:#B4A7FA;cursor:pointer;">
            <div style="display:flex;justify-content:space-between;font-size:11px;color:#888;">
                <span>1</span><span>{max_depth}</span>
            </div>
        </div>
        '''

    panel = f'''
    <div id="controlPanel" style="position:fixed;top:10px;left:10px;z-index:1000;
                background:#262626;padding:12px 16px;border-radius:8px;
                border:1px solid #3e3e3e;font-family:monospace;color:#dcddde;font-size:13px;
                min-width:200px;">
        <div style="font-size:15px;font-weight:bold;margin-bottom:8px;">{title}</div>
        <div><span style="color:#7DDCB5;">━━</span> wikilink (existing)</div>
        <div><span style="color:#FDBA8C;">╌╌</span> semantic (discovered)</div>
        <div><span style="color:#B4A7FA;">━━</span> both</div>
        <div style="margin-top:6px;"><span style="color:#FFD700;">●</span> center document</div>
        <div id="nodeCount" style="margin-top:6px;color:#888;font-size:11px;"></div>
        {slider_html}
    </div>
    '''

    # JavaScript for depth filtering
    depth_script = ""
    if max_depth > 1:
        depth_script = '''
    <script>
    document.addEventListener("DOMContentLoaded", function() {
        var slider = document.getElementById("depthSlider");
        var depthLabel = document.getElementById("depthValue");
        var countLabel = document.getElementById("nodeCount");
        if (!slider || !nodes) return;

        function updateCount(maxD) {
            var visible = 0, total = nodes.length;
            nodes.forEach(function(n) { if (n.level <= maxD) visible++; });
            countLabel.textContent = visible + " / " + total + " nodes";
        }
        updateCount(parseInt(slider.value));

        slider.addEventListener("input", function() {
            var maxD = parseInt(this.value);
            depthLabel.textContent = maxD;

            // Update node visibility
            var updates = [];
            nodes.forEach(function(n) {
                var hidden = (n.level > maxD);
                updates.push({id: n.id, hidden: hidden});
            });
            nodes.update(updates);

            // Hide edges connected to hidden nodes
            var hiddenNodes = new Set();
            nodes.forEach(function(n) { if (n.level > maxD) hiddenNodes.add(n.id); });
            var edgeUpdates = [];
            edges.forEach(function(e) {
                var hidden = hiddenNodes.has(e.from) || hiddenNodes.has(e.to);
                edgeUpdates.push({id: e.id, hidden: hidden});
            });
            edges.update(edgeUpdates);

            updateCount(maxD);
        });
    });
    </script>
    '''

    html = html.replace('<body>', f'<body>{panel}', 1)
    html = html.replace('</body>', f'{depth_script}</body>', 1)
    Path(path).write_text(html, encoding='utf-8')
