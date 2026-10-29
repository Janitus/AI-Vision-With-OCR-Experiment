"""Conservative image-to-graph extraction using local PaddleOCR and Ollama.

The JSON intermediate files are part of the interface: a vision response can be
reviewed or replaced and replayed with --vision-json without calling a model.
"""
from __future__ import annotations

import argparse
import base64
import difflib
import json
import re
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image


PROMPT = """Inspect this graph image. Return ONLY one JSON object with keys nodes,
edges, uncertainties. Transcribe visible text exactly, including spelling and
punctuation. Do not repair clipped labels or infer legal/semantic facts. A node
has id, label, type, bbox=[left,top,right,bottom], confidence (0..1). Type is a
visually observable category such as colored_rectangle or container. An edge
has source, target, relationship (visible edge text or 'unknown'), direction
('source_to_target', 'undirected', or 'unknown'), points=[[x,y],...], confidence.
source/target must be node ids. For directed arrows, source is the tail and
target is the arrowhead. Give points along the visible line, including its two
ends; do not use a semantic guess to decide direction. Include only edges you
can visually trace. Put ambiguity and alternative readings in uncertainties.
All coordinates are pixels in the ORIGINAL image, width={width}, height={height}.
The OCR observations below may be wrong. Compare them with the image; do not
blindly adopt or silently correct them. OCR observations: {ocr}"""


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bbox(poly: list[list[float]]) -> list[int]:
    return [round(min(p[0] for p in poly)), round(min(p[1] for p in poly)),
            round(max(p[0] for p in poly)), round(max(p[1] for p in poly))]


def rotate_back(poly: list[list[float]], angle: int, width: int, height: int) -> list[list[float]]:
    # PIL rotates counterclockwise. Coordinates below invert that transform.
    if angle == 90:
        return [[width - y, x] for x, y in poly]
    if angle == 180:
        return [[width - x, height - y] for x, y in poly]
    if angle == 270:
        return [[y, height - x] for x, y in poly]
    return poly


def paddle_ocr(image: Path, lang: str = "fi", ocr_version: str = "PP-OCRv5") -> dict[str, Any]:
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError("Install PaddleOCR and PaddlePaddle; see README.md") from exc
    import numpy as np

    im = Image.open(image).convert("RGB")
    width, height = im.size
    engine = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False,
                       use_textline_orientation=True, lang=lang, ocr_version=ocr_version)
    observations: list[dict[str, Any]] = []
    for angle in (0, 90, 180, 270):
        rotated = im.rotate(angle, expand=True)
        result = engine.predict(np.asarray(rotated))
        for page in result or []:
            data = page.json.get("res", page.json)
            for label, confidence, poly in zip(data.get("rec_texts", []),
                                               data.get("rec_scores", []),
                                               data.get("rec_polys", [])):
                raw_poly = [[float(x), float(y)] for x, y in poly]
                original_poly = rotate_back(raw_poly, angle, width, height)
                obs = {"text": str(label), "confidence": round(float(confidence), 4),
                       "bbox": bbox(original_poly), "polygon": original_poly, "rotation": angle}
                # Multiple rotations can read the same line. Retain the best reading.
                match = next((i for i, old in enumerate(observations)
                              if overlap(old["bbox"], obs["bbox"]) > 0.55
                              and similarity(old["text"], obs["text"]) > 0.7), None)
                if match is None:
                    observations.append(obs)
                elif obs["confidence"] > observations[match]["confidence"]:
                    observations[match] = obs
    return {"image": str(image), "image_size": [width, height], "engine": "paddleocr",
            "language": lang, "ocr_version": ocr_version,
            "rotations": [0, 90, 180, 270], "observations": observations}


def overlap(a: list[int], b: list[int]) -> float:
    x = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    y = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    area = x * y
    aa = max(1, (a[2] - a[0]) * (a[3] - a[1]))
    ba = max(1, (b[2] - b[0]) * (b[3] - b[1]))
    return area / min(aa, ba)


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, re.sub(r"\s+", " ", a).strip().casefold(),
                                   re.sub(r"\s+", " ", b).strip().casefold()).ratio()


def ollama_vision(image: Path, ocr: dict[str, Any], model: str) -> dict[str, Any]:
    width, height = Image.open(image).size
    request_body = {"model": model, "stream": False, "format": "json",
                    "messages": [{"role": "user", "content": PROMPT.format(
                        width=width, height=height,
                        ocr=json.dumps(ocr["observations"], ensure_ascii=False)),
                        "images": [base64.b64encode(image.read_bytes()).decode("ascii")]}]}
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat",
                                 data=json.dumps(request_body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            return json.load(response)
    except Exception as exc:
        raise RuntimeError(f"Local Ollama vision request failed: {exc}") from exc


def parse_vision(raw: dict[str, Any]) -> dict[str, Any]:
    if "message" in raw:
        content = raw["message"]["content"]
        return json.loads(content)
    if all(key in raw for key in ("nodes", "edges")):
        return raw
    raise ValueError("Vision JSON must be an Ollama response or a graph object")


def center(box: list[int]) -> tuple[float, float]:
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2


def nearest_ocr(text: str, region: list[int] | None, observations: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = observations
    if region:
        candidates = [o for o in observations if overlap(region, o["bbox"]) > 0.3]
    if not candidates:
        return None
    return max(candidates, key=lambda o: similarity(text, o["text"]))


def node_ocr_candidate(text: str, region: list[int], observations: list[dict[str, Any]],
                       node_type: str) -> dict[str, Any] | None:
    inside = [o for o in observations if overlap(region, o["bbox"]) > 0.3]
    if not inside:
        return None
    candidates = list(inside)
    if node_type != "container" and len(inside) > 1:
        ordered = sorted(inside, key=lambda o: (center(o["bbox"])[1], center(o["bbox"])[0]))
        candidates.append({"text": " ".join(o["text"] for o in ordered),
                           "confidence": min(o["confidence"] for o in ordered),
                           "bbox": region})
    return max(candidates, key=lambda o: similarity(text, o["text"]))


def reconcile(ocr: dict[str, Any], vision: dict[str, Any]) -> dict[str, Any]:
    observations = ocr["observations"]
    uncertainties = list(vision.get("uncertainties", []))
    nodes = []
    ids = set()
    for item in vision.get("nodes", []):
        node_id = str(item.get("id", ""))
        box = item.get("bbox")
        if not node_id or node_id in ids or not isinstance(box, list) or len(box) != 4:
            uncertainties.append({"kind": "invalid_node", "vision_item": item})
            continue
        ids.add(node_id)
        visual_label = str(item.get("label", ""))
        match = node_ocr_candidate(visual_label, box, observations, item.get("type", "unknown"))
        score = similarity(visual_label, match["text"]) if match else 0.0
        if match and score >= 0.97:
            label = match["text"]
            evidence = "ocr_and_vision"
            confidence = min(float(item.get("confidence", 0.5)), match["confidence"])
        else:
            label = visual_label
            evidence = "vision_only"
            confidence = min(float(item.get("confidence", 0.5)), 0.65)
            uncertainties.append({"kind": "node_text_disagreement" if match else "node_text_unconfirmed", "node": node_id,
                                  "vision_text": visual_label,
                                  "ocr_text": match["text"] if match else None,
                                  "ocr_bbox": match["bbox"] if match else None})
        nodes.append({"id": node_id, "label": label, "type": item.get("type", "unknown"),
                      "bbox": box, "confidence": round(max(0.0, min(1.0, confidence)), 3),
                      "evidence": evidence})
    edges = []
    for i, item in enumerate(vision.get("edges", []), 1):
        source, target = item.get("source"), item.get("target")
        points = item.get("points", [])
        if source not in ids or target not in ids or len(points) < 2:
            uncertainties.append({"kind": "edge_not_visually_established", "vision_item": item})
            continue
        relationship = str(item.get("relationship", "unknown") or "unknown")
        direction = item.get("direction", "unknown")
        if direction not in ("source_to_target", "undirected", "unknown"):
            direction = "unknown"
        # Edge labels are usually near the line midpoint; node text is excluded.
        mx = sum(p[0] for p in points) / len(points)
        my = sum(p[1] for p in points) / len(points)
        node_boxes = [n["bbox"] for n in nodes]
        label_candidates = [o for o in observations
                            if abs(center(o["bbox"])[0] - mx) < 95
                            and abs(center(o["bbox"])[1] - my) < 45
                            and not any(overlap(o["bbox"], nb) > 0.5 for nb in node_boxes)]
        match = nearest_ocr(relationship, None, label_candidates) if relationship != "unknown" else None
        if match and similarity(relationship, match["text"]) >= 0.97:
            relationship = match["text"]
            evidence = "ocr_and_vision"
            confidence = min(float(item.get("confidence", 0.5)), match["confidence"])
        else:
            evidence = "vision_only"
            confidence = min(float(item.get("confidence", 0.5)), 0.6)
            if relationship != "unknown":
                uncertainties.append({"kind": "edge_text_disagreement" if match else "edge_text_unconfirmed", "edge": i,
                                      "vision_text": relationship,
                                      "ocr_text": match["text"] if match else None})
        if direction == "unknown":
            uncertainties.append({"kind": "direction_unresolved", "edge": i})
        edges.append({"source": source, "target": target, "relationship": relationship,
                      "direction": direction, "points": points,
                      "confidence": round(max(0.0, min(1.0, confidence)), 3),
                      "evidence": evidence})
    return {"image_size": ocr["image_size"], "nodes": nodes, "edges": edges,
            "uncertainties": uncertainties,
            "provenance": {"ocr_engine": ocr.get("engine"), "vision_source": vision.get("source", "ollama")}}


def mermaid(graph: dict[str, Any]) -> str:
    lines = ["flowchart TB"]
    for node in graph["nodes"]:
        safe_id = re.sub(r"[^A-Za-z0-9_]", "_", node["id"])
        label = node["label"].replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
        lines.append(f'  {safe_id}["{label}"]')
    for edge in graph["edges"]:
        a = re.sub(r"[^A-Za-z0-9_]", "_", edge["source"])
        b = re.sub(r"[^A-Za-z0-9_]", "_", edge["target"])
        label = edge["relationship"].replace("|", "&#124;").replace("\n", " ")
        if edge["direction"] == "unknown":
            label += " [direction unknown]"
        arrow = "-->" if edge["direction"] == "source_to_target" else "---"
        lines.append(f"  {a} {arrow}|{label}| {b}")
    return "\n".join(lines) + "\n"


def load_truth(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    text = path.read_text(encoding="utf-8")
    nodes = []
    edges = []
    if path.suffix.lower() in (".mmd", ".mermaid"):
        for line in text.splitlines():
            m = re.match(r'\s*([\w]+)\["(.*?)"\]', line)
            if m:
                nodes.append({"id": m[1], "label": m[2]})
            m = re.match(r'\s*([\w]+)\s+(-->|---)\|([^|]*)\|\s+([\w]+)', line)
            if m:
                edges.append({"source": m[1], "target": m[4], "relationship": m[3],
                              "direction": "source_to_target" if m[2] == "-->" else "undirected"})
    elif path.suffix.lower() == ".dot":
        # Supports quoted or unquoted IDs and optional label attributes.
        atom = r'("[^"]+"|[A-Za-z_][\w]*)'
        for m in re.finditer(atom + r'\s*(->|--)\s*' + atom + r'(?:\s*\[([^]]*)\])?', text):
            attrs = m[4] or ""
            label = re.search(r'label\s*=\s*"([^"]*)"', attrs)
            edges.append({"source": m[1].strip('"'), "target": m[3].strip('"'),
                          "relationship": label[1] if label else "unknown",
                          "direction": "source_to_target" if m[2] == "->" else "undirected"})
        for m in re.finditer(atom + r'\s*\[([^]]*)\]', text):
            label = re.search(r'label\s*=\s*"([^"]*)"', m[2])
            nodes.append({"id": m[1].strip('"'), "label": label[1] if label else m[1].strip('"')})
    else:
        raise ValueError("Ground truth must be .json, .mmd, .mermaid, or .dot")
    return {"nodes": nodes, "edges": edges}


def score(graph: dict[str, Any], truth: dict[str, Any]) -> dict[str, Any]:
    # Node matching uses exact visible labels; duplicate labels are counted once.
    predicted_nodes = {n["label"] for n in graph["nodes"]}
    true_nodes = {n["label"] for n in truth["nodes"]}
    pred_labels = {n["id"]: n["label"] for n in graph["nodes"]}
    true_labels = {n["id"]: n["label"] for n in truth["nodes"]}
    def signatures(edges: list[dict[str, Any]], labels: dict[str, str]) -> set[tuple[str, str, str, str]]:
        return {(labels.get(e["source"], e["source"]), labels.get(e["target"], e["target"]),
                 e.get("relationship", "unknown"), e.get("direction", "unknown")) for e in edges}
    predicted_edges = signatures(graph["edges"], pred_labels)
    true_edges = signatures(truth["edges"], true_labels)
    def pr(a: set[Any], b: set[Any]) -> dict[str, Any]:
        correct = len(a & b)
        return {"correct": correct, "predicted": len(a), "ground_truth": len(b),
                "precision": correct / len(a) if a else None,
                "recall": correct / len(b) if b else None}
    return {"nodes": pr(predicted_nodes, true_nodes), "edges": pr(predicted_edges, true_edges),
            "matching": "exact node labels and exact directed edge endpoints/relationship/direction"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--out", type=Path, default=Path("output"))
    parser.add_argument("--model", default="llava", help="Local Ollama vision model")
    parser.add_argument("--ocr-lang", default="fi", help="PaddleOCR language route (default: fi)")
    parser.add_argument("--ocr-version", default="PP-OCRv5", help="PaddleOCR model family")
    parser.add_argument("--vision-json", type=Path, help="Replay a saved local vision response")
    parser.add_argument("--ocr-json", type=Path, help="Replay saved OCR observations")
    parser.add_argument("--ground-truth", type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    ocr = json.loads(args.ocr_json.read_text(encoding="utf-8")) if args.ocr_json else paddle_ocr(args.image, args.ocr_lang, args.ocr_version)
    dump(args.out / "ocr.json", ocr)
    raw = json.loads(args.vision_json.read_text(encoding="utf-8")) if args.vision_json else ollama_vision(args.image, ocr, args.model)
    dump(args.out / "vision_raw.json", raw)
    graph = reconcile(ocr, parse_vision(raw))
    dump(args.out / "graph.json", graph)
    (args.out / "graph.mmd").write_text(mermaid(graph), encoding="utf-8")
    report = {"node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]),
              "uncertainty_count": len(graph["uncertainties"]),
              "uncertainties": graph["uncertainties"],
              "notes": ["Vision-only text has reduced confidence.",
                        "An edge is emitted only when the vision result includes trace points and valid endpoints.",
                        "Visual and OCR agreement does not prove semantic correctness."]}
    if args.ground_truth:
        report["ground_truth_metrics"] = score(graph, load_truth(args.ground_truth))
    dump(args.out / "validation.json", report)


if __name__ == "__main__":
    main()
