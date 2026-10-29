"""Join saved vision graph elements with OCR observations without adding graph elements.

Only blind vision predictions and raw RapidOCR output are read. Source graph truth is
never consulted. An OCR box is assigned to at most one exact-text vision element;
unassigned boxes remain available for review rather than becoming invented nodes.
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "vision_ocr_union" / "predictions"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: object) -> str:
    return " ".join(str(value or "").split())


def center(polygon: list[list[float]]) -> tuple[float, float]:
    return (sum(p[0] for p in polygon) / len(polygon),
            sum(p[1] for p in polygon) / len(polygon))


def main() -> None:
    mapping = read(ROOT / "blind_mapping.json")
    OUT.mkdir(parents=True, exist_ok=True)
    totals = {"cases": 0, "ocr_boxes": 0, "exact_matches": 0, "unmatched_boxes": 0,
              "cases_with_unmatched_boxes": 0,
              "graph_nodes_added": 0, "graph_edges_added": 0}
    for case, slug in mapping.items():
        vision = read(ROOT / "blind_vision" / "predictions" / f"{case}.json")
        ocr = read(ROOT / "runs" / "rapid_v6_medium_fi" / f"{slug}.json")
        graph = copy.deepcopy(vision)
        nodes = {str(n["id"]): n for n in graph["nodes"]}
        targets = [{"kind": "title", "key": "title", "text": clean(graph.get("title")),
                    "center": (300, 55)}]
        targets += [{"kind": "node", "key": str(n["id"]), "text": clean(n.get("label")),
                     "center": tuple(n["center"])} for n in graph["nodes"]]
        for index, edge in enumerate(graph["edges"]):
            a = nodes.get(str(edge.get("source")))
            b = nodes.get(str(edge.get("target")))
            if a and b:
                point = ((a["center"][0]+b["center"][0])/2,
                         (a["center"][1]+b["center"][1])/2)
                targets.append({"kind": "edge", "key": index,
                                "text": clean(edge.get("relationship")), "center": point})
        candidates = []
        observations = ocr["observations"]
        for oi, observation in enumerate(observations):
            value = clean(observation.get("text"))
            if not value or not observation.get("polygon"):
                continue
            xy = center(observation["polygon"])
            for ti, target in enumerate(targets):
                if value == target["text"]:
                    distance = math.dist(xy, target["center"])
                    if distance <= 500:
                        candidates.append((distance, oi, ti))
        used_ocr, used_targets = set(), set()
        evidence = []
        for distance, oi, ti in sorted(candidates):
            if oi in used_ocr or ti in used_targets:
                continue
            used_ocr.add(oi)
            used_targets.add(ti)
            target, observation = targets[ti], observations[oi]
            evidence.append({"target_kind": target["kind"], "target_key": target["key"],
                             "ocr_index": oi, "text": observation["text"],
                             "confidence": observation["confidence"],
                             "polygon": observation["polygon"],
                             "center_distance": round(distance, 1)})
        unmatched = [{"ocr_index": i, **observation} for i, observation in enumerate(observations)
                     if i not in used_ocr]
        graph["union_method"] = "Vision graph retained; exact-text RapidOCR boxes assigned once as evidence"
        graph["ocr_engine"] = ocr["engine"]
        graph["ocr_evidence"] = evidence
        graph["ocr_unassigned"] = unmatched
        graph["ocr_disagreements"] = []  # An unassigned box is not necessarily a conflict.
        (OUT / f"{case}.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
        totals["cases"] += 1
        totals["ocr_boxes"] += len(observations)
        totals["exact_matches"] += len(evidence)
        totals["unmatched_boxes"] += len(unmatched)
        totals["cases_with_unmatched_boxes"] += bool(unmatched)
        print(case, len(evidence), "matched OCR boxes,", len(unmatched), "unmatched")
    (ROOT / "vision_ocr_union" / "union_summary.json").write_text(
        json.dumps(totals, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Union complete:", totals)


if __name__ == "__main__":
    main()
