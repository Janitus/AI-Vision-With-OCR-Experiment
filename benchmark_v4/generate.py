"""Create corrected v4 fixtures with visible, individually traceable edges.

V4 retains the v3 domains, layouts, text, and styles. It removes eight edges
whose straight routes were hidden by non-endpoint nodes or co-located with
another edge. The raw v3 fixtures remain unchanged for auditability.
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

from benchmark_v3 import generate as previous


ROOT = Path(__file__).resolve().parent
base = previous.base
base.ROOT = ROOT
base.W = 1800
base.H = 1100

DROP_SOURCE_EDGES = {
    "ministerioiden_hanke": [11],
    "rokotusketju": [10],
    "saatutkimus": [4, 6],
    "tulvaviestinta": [11],
    "tutkimusjulkaisu": [2, 8],
    "veron_oikaisu": [9],
}


def segment_inside_box(a, b, box):
    """Return length of a straight segment inside an axis-aligned node box."""
    x1, y1 = a
    x2, y2 = b
    dx, dy = x2 - x1, y2 - y1
    lo, hi = 0.0, 1.0
    for p, q in ((-dx, x1 - box[0]), (dx, box[2] - x1),
                 (-dy, y1 - box[1]), (dy, box[3] - y1)):
        if abs(p) < 1e-9:
            if q < 0:
                return 0.0
            continue
        t = q / p
        if p < 0:
            lo = max(lo, t)
        else:
            hi = min(hi, t)
        if lo > hi:
            return 0.0
    return max(0.0, hi - lo) * math.hypot(dx, dy)


def collinear_overlap(a, b, c, d):
    """Return shared pixel length for two nearly co-located segments."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(vx, vy)
    if length < 1:
        return 0.0
    ux, uy = vx / length, vy / length
    if max(abs((p[0] - a[0]) * uy - (p[1] - a[1]) * ux) for p in (c, d)) > 5:
        return 0.0
    tc = (c[0] - a[0]) * ux + (c[1] - a[1]) * uy
    td = (d[0] - a[0]) * ux + (d[1] - a[1]) * uy
    return max(0.0, min(length, max(tc, td)) - max(0.0, min(tc, td)))


def check_edge_routes(case):
    edges, nodes = case["edges"], case["nodes"]
    routes = [base.line_ends(nodes[e["source"]], nodes[e["target"]]) for e in edges]
    defects = []
    for i, (edge, (a, b)) in enumerate(zip(edges, routes)):
        for n, node in enumerate(nodes):
            if n in (edge["source"], edge["target"]):
                continue
            raw = base.shape_box(node)
            box = (raw[0] + 8, raw[1] + 8, raw[2] - 8, raw[3] - 8)
            overlap = segment_inside_box(a, b, box)
            if overlap > 18:
                defects.append({"kind": "edge_hidden_by_node", "edge": i,
                                "node": n, "pixels": round(overlap)})
        for j in range(i):
            overlap = collinear_overlap(a, b, *routes[j])
            if overlap > 25:
                defects.append({"kind": "coincident_edge_segments", "edges": [j, i],
                                "pixels": round(overlap)})
    if defects:
        raise ValueError(f"{case['id']}: visually ambiguous edge routes: {defects}")
    return {"hidden_by_nonendpoint_nodes": 0, "coincident_edge_pairs": 0,
            "checked_edges": len(edges)}


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest, text_qa, edge_qa = [], {}, {}
    for original in previous.CASES:
        case = copy.deepcopy(original)
        slug = case["id"]
        removed = set(DROP_SOURCE_EDGES.get(slug, []))
        case["edges"] = [e for i, e in enumerate(case["edges"]) if i not in removed]
        edge_qa[slug] = check_edge_routes(case)
        edge_qa[slug]["removed_v3_edge_indices"] = sorted(removed)
        previous.plan_labels(case)
        text_qa[slug] = base.render(case)
        (ROOT / f"{slug}.mmd").write_text(base.mermaid(case), encoding="utf-8")
        (ROOT / f"{slug}.source.json").write_text(
            json.dumps(case, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest.append({"id": slug, "title": case["title"], "context": case["context"],
                         "style": case["shape"], "font": case["font"],
                         "image": f"{slug}.png", "mermaid": f"{slug}.mmd"})
    for name, value in (("manifest", manifest), ("text_qa", text_qa), ("edge_qa", edge_qa)):
        (ROOT / f"{name}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Generated", len(manifest), "figures with", sum(x["checked_edges"] for x in edge_qa.values()),
          "QA-checked edges")


if __name__ == "__main__":
    main()
