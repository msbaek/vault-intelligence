#!/usr/bin/env python3
"""graphify 개념 그래프(graph.json) → Obsidian graph view 스타일 인터랙티브 HTML.

graphify 가 만든 networkx node_link 포맷 graph.json 을 읽어, 외부 의존성 0
(CDN·설치 불필요)인 self-contained HTML 한 장으로 렌더한다. 브라우저에서 바로
열어 노드 드래그·줌·이웃 강조·개념 검색을 할 수 있다.

사용법:
    python3 scripts/graphify_view.py cache/graph/ddd/graph.json
    python3 scripts/graphify_view.py cache/graph/ddd/graph.json --open
    python3 scripts/graphify_view.py <graph.json> -o out.html -t "DDD 개념 그래프"

옵션:
    graph_json        graphify 가 생성한 graph.json 경로 (필수)
    -o, --output      출력 HTML 경로 (기본: graph.json 과 같은 폴더의 graph-view.html)
    -t, --title       그래프 제목 (기본: graph.json 의 상위 폴더 이름)
    --open            생성 후 기본 브라우저로 자동 열기
"""
import argparse
import json
import webbrowser
from collections import Counter
from pathlib import Path

# 외부 script 태그 0개 — 데이터(__DATA__)와 제목(__TITLE__)만 치환해 임베드한다.
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; background: #1a1a1a;
    color: #dcddde; font-family: -apple-system, "Apple SD Gothic Neo", sans-serif; }
  #graph { display: block; }
  .panel { position: fixed; background: rgba(26,26,28,.92); border: 1px solid #34343a;
    border-radius: 10px; padding: 12px 14px; font-size: 12px; line-height: 1.5;
    box-shadow: 0 6px 24px rgba(0,0,0,.45); }
  #info { top: 14px; left: 14px; max-width: 320px; }
  #info h1 { font-size: 14px; margin: 0 0 8px; color: #e8e8ec; }
  #info .stat { color: #8a8a92; }
  #legend { margin-top: 8px; }
  #legend .row { margin: 2px 0; }
  .edge-key { display:inline-block; width:18px; border-top:2px solid #9a9aa2;
    margin-right:6px; vertical-align: middle; }
  .edge-key.dash { border-top-style: dashed; }
  #detail { margin-top: 10px; padding-top: 8px; border-top: 1px solid #34343a; display:none; }
  #detail .dlabel { font-size: 13px; color: #fff; font-weight: 600; }
  #detail .src { color: #7d7d85; font-size: 11px; word-break: break-all; margin: 3px 0; }
  #detail .nbrs { color: #b5b5bd; margin-top: 4px; }
  #search { top: 14px; right: 14px; }
  #search input { background: #25252a; border: 1px solid #3a3a42; color: #ddd;
    padding: 7px 10px; border-radius: 7px; width: 180px; outline: none; font-size: 12px; }
  .hint { position: fixed; bottom: 12px; left: 14px; color: #5a5a62; font-size: 11px; }
</style>
</head>
<body>
<div id="info" class="panel">
  <h1>__TITLE__</h1>
  <div class="stat" id="stats"></div>
  <div id="legend"></div>
  <div id="detail"></div>
</div>
<div id="search" class="panel"><input id="q" placeholder="개념 검색…" autocomplete="off"></div>
<div class="hint">드래그=노드 이동/배경 패닝 · 휠=줌 · 호버=이웃 강조 · 클릭=상세</div>
<canvas id="graph"></canvas>
<script>
const DATA = __DATA__;
const PALETTE = ["#7aa2f7","#bb9af7","#7dcfff","#9ece6a","#e0af68","#f7768e",
                 "#ff9e64","#2ac3de","#cfc9c2","#c0caf5","#73daca","#ff75a0"];
const KREP = 2600, KSPRING = 0.035, LREST = 72, KCENTER = 0.018, DAMP = 0.88;

const canvas = document.getElementById("graph");
const ctx = canvas.getContext("2d");
let W, H, DPR = window.devicePixelRatio || 1;
function resize() {
  W = window.innerWidth; H = window.innerHeight;
  canvas.width = W * DPR; canvas.height = H * DPR;
  canvas.style.width = W + "px"; canvas.style.height = H + "px";
}
resize();
window.addEventListener("resize", resize);

const nodes = DATA.nodes.map(n => Object.assign({}, n));
nodes.forEach(n => {
  n.x = (Math.random() - 0.5) * 600; n.y = (Math.random() - 0.5) * 600;
  n.vx = 0; n.vy = 0; n.r = 4 + Math.sqrt(n.deg) * 2.3;
});
const byId = new Map(nodes.map(n => [n.id, n]));
const links = DATA.links.map(l => ({
  s: byId.get(l.source), t: byId.get(l.target),
  confidence: l.confidence, score: l.score, relation: l.relation,
})).filter(l => l.s && l.t);

const adj = new Map(nodes.map(n => [n.id, new Set()]));
links.forEach(l => { adj.get(l.s.id).add(l.t.id); adj.get(l.t.id).add(l.s.id); });
const EMPTY = new Set();
const N = nodes.length;

let scale = 1, offsetX = W / 2, offsetY = H / 2;
let alpha = 1, dragNode = null, panning = false, px = 0, py = 0;
let hiId = null, nbset = EMPTY, searchQ = "";

function pick(wx, wy) {
  let best = null, bd = 1e9;
  for (const a of nodes) {
    const dx = a.x - wx, dy = a.y - wy, d = dx * dx + dy * dy, rr = (a.r + 4) * (a.r + 4);
    if (d < rr && d < bd) { bd = d; best = a; }
  }
  return best;
}
function setHi(node) {
  hiId = node ? node.id : null;
  nbset = node ? adj.get(node.id) : EMPTY;
  if (node) showDetail(node);
}
function showDetail(d) {
  const nb = [...adj.get(d.id)].map(id => byId.get(id).label).sort();
  const el = document.getElementById("detail");
  el.style.display = "block";
  el.innerHTML = '<div class="dlabel">' + d.label + '</div>' +
    '<div class="src">📄 ' + (d.source_file || "—") + '</div>' +
    '<div class="src">cluster ' + d.community + ' · 연결 ' + d.deg + '개</div>' +
    '<div class="nbrs">↔ ' + (nb.join(", ") || "—") + '</div>';
}

function step() {
  if (alpha > 0.003 || dragNode) {
    for (const a of nodes) { a.gx = 0; a.gy = 0; }
    for (let i = 0; i < N; i++) {
      const a = nodes[i];
      for (let j = i + 1; j < N; j++) {
        const b = nodes[j];
        let dx = a.x - b.x, dy = a.y - b.y, d2 = dx * dx + dy * dy || 0.01;
        let d = Math.sqrt(d2), f = (KREP / d2) * alpha, fx = dx / d * f, fy = dy / d * f;
        a.gx += fx; a.gy += fy; b.gx -= fx; b.gy -= fy;
      }
    }
    for (const l of links) {
      let dx = l.t.x - l.s.x, dy = l.t.y - l.s.y, d = Math.sqrt(dx * dx + dy * dy) || 0.01;
      let f = KSPRING * (d - LREST) * alpha, fx = dx / d * f, fy = dy / d * f;
      l.s.gx += fx; l.s.gy += fy; l.t.gx -= fx; l.t.gy -= fy;
    }
    for (const a of nodes) {
      a.gx += -a.x * KCENTER * alpha; a.gy += -a.y * KCENTER * alpha;
      if (a === dragNode) continue;
      a.vx = (a.vx + a.gx) * DAMP; a.vy = (a.vy + a.gy) * DAMP;
      a.x += a.vx; a.y += a.vy;
    }
    alpha *= 0.992;
  }
  draw();
  requestAnimationFrame(step);
}

function draw() {
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
  ctx.clearRect(0, 0, W, H);
  ctx.translate(offsetX, offsetY); ctx.scale(scale, scale);
  for (const l of links) {
    const on = hiId && (l.s.id === hiId || l.t.id === hiId);
    let op = hiId ? (on ? 0.85 : 0.03) : (searchQ ? 0.04 : (l.confidence === "INFERRED" ? 0.18 : 0.4));
    ctx.beginPath(); ctx.moveTo(l.s.x, l.s.y); ctx.lineTo(l.t.x, l.t.y);
    ctx.setLineDash(l.confidence === "INFERRED" ? [4, 3] : []);
    ctx.lineWidth = 0.4 + l.score; ctx.strokeStyle = "rgba(150,150,162," + op + ")"; ctx.stroke();
  }
  ctx.setLineDash([]);
  for (const a of nodes) {
    let dim = false;
    if (hiId) dim = !(a.id === hiId || nbset.has(a.id));
    else if (searchQ) dim = !a.label.toLowerCase().includes(searchQ);
    ctx.globalAlpha = dim ? 0.12 : 1;
    ctx.beginPath(); ctx.arc(a.x, a.y, a.r, 0, 6.2832);
    ctx.fillStyle = PALETTE[a.community % PALETTE.length]; ctx.fill();
    ctx.lineWidth = 1.2; ctx.strokeStyle = "#1a1a1a"; ctx.stroke();
    const showLbl = (hiId && (a.id === hiId || nbset.has(a.id))) ||
                    (searchQ && !dim) || (!hiId && !searchQ && scale > 0.55);
    if (showLbl) {
      ctx.fillStyle = "#b9b9c2"; ctx.font = "9px -apple-system, sans-serif"; ctx.textAlign = "center";
      ctx.fillText(a.label, a.x, a.y - a.r - 3);
    }
  }
  ctx.globalAlpha = 1;
}

canvas.addEventListener("wheel", e => {
  e.preventDefault();
  const f = Math.exp(-e.deltaY * 0.0012), mx = e.clientX, my = e.clientY;
  const wx = (mx - offsetX) / scale, wy = (my - offsetY) / scale;
  scale = Math.max(0.12, Math.min(8, scale * f));
  offsetX = mx - wx * scale; offsetY = my - wy * scale;
}, { passive: false });
canvas.addEventListener("mousedown", e => {
  const wx = (e.clientX - offsetX) / scale, wy = (e.clientY - offsetY) / scale;
  dragNode = pick(wx, wy);
  if (dragNode) { alpha = Math.max(alpha, 0.5); }
  else { panning = true; px = e.clientX; py = e.clientY; }
});
window.addEventListener("mousemove", e => {
  if (dragNode) {
    dragNode.x = (e.clientX - offsetX) / scale; dragNode.y = (e.clientY - offsetY) / scale;
    dragNode.vx = 0; dragNode.vy = 0; alpha = Math.max(alpha, 0.3);
  } else if (panning) {
    offsetX += e.clientX - px; offsetY += e.clientY - py; px = e.clientX; py = e.clientY;
  } else {
    setHi(pick((e.clientX - offsetX) / scale, (e.clientY - offsetY) / scale));
  }
});
window.addEventListener("mouseup", () => { dragNode = null; panning = false; });
document.getElementById("q").addEventListener("input", function () {
  searchQ = this.value.trim().toLowerCase();
});

const nComm = new Set(nodes.map(n => n.community)).size;
document.getElementById("stats").innerHTML =
  "개념 " + N + " · 연결 " + links.length + " · 클러스터 " + nComm;
document.getElementById("legend").innerHTML =
  '<div class="row"><span class="edge-key"></span>EXTRACTED (명시적 추출)</div>' +
  '<div class="row"><span class="edge-key dash"></span>INFERRED (추론, score≥0.8)</div>' +
  '<div class="row" style="margin-top:4px;color:#7d7d85">노드 색=클러스터 · 크기=연결 수</div>';
step();
</script>
</body>
</html>
"""


def build_view_html(graph_data: dict, title: str) -> str:
    """networkx node_link dict → self-contained HTML 문자열.

    노드 degree 를 집계하고 시각화에 필요한 필드만 추려 HTML 에 임베드한다.
    외부 script 태그를 만들지 않는다(완전 self-contained).
    """
    deg = Counter()
    for link in graph_data.get("links", []):
        deg[link["source"]] += 1
        deg[link["target"]] += 1

    nodes = [{
        "id": n["id"],
        "label": n.get("label") or n["id"],
        "source_file": n.get("source_file"),
        "community": n.get("community", 0),
        "deg": deg.get(n["id"], 0),
    } for n in graph_data.get("nodes", [])]
    links = [{
        "source": l["source"],
        "target": l["target"],
        "confidence": l.get("confidence", "INFERRED"),
        "relation": l.get("relation", ""),
        "score": float(l.get("confidence_score", 1.0)),
    } for l in graph_data.get("links", [])]

    payload = json.dumps({"nodes": nodes, "links": links}, ensure_ascii=False)
    return HTML_TEMPLATE.replace("__DATA__", payload).replace("__TITLE__", title)


def main():
    parser = argparse.ArgumentParser(
        description="graphify graph.json → Obsidian 스타일 인터랙티브 HTML (외부 의존성 0)")
    parser.add_argument("graph_json", help="graphify 가 생성한 graph.json 경로")
    parser.add_argument("-o", "--output", default=None,
                        help="출력 HTML 경로 (기본: graph.json 폴더의 graph-view.html)")
    parser.add_argument("-t", "--title", default=None,
                        help="그래프 제목 (기본: graph.json 상위 폴더 이름)")
    parser.add_argument("--open", action="store_true",
                        help="생성 후 기본 브라우저로 열기")
    args = parser.parse_args()

    src = Path(args.graph_json).expanduser().resolve()
    out = Path(args.output).expanduser().resolve() if args.output \
        else src.parent / "graph-view.html"
    title = args.title or (src.parent.name or src.stem)

    data = json.loads(src.read_text())
    out.write_text(build_view_html(data, title))
    print(f"생성: {out}  (노드 {len(data.get('nodes', []))}, 엣지 {len(data.get('links', []))})")
    print(f"열기: open '{out}'   (또는 --open 옵션)")
    if args.open:
        webbrowser.open(out.as_uri())


if __name__ == "__main__":
    main()
