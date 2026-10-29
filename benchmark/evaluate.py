"""Strict, inspectable graph comparison independent of the source node IDs."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def iou(a: list[int], b: list[int]) -> float:
    x = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    y = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - x*y
    return x*y/union if union else 0.0


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b)+1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(curr[-1]+1, prev[j]+1, prev[j-1]+(ca != cb)))
        prev = curr
    return prev[-1]


def ratio(correct: int, total: int) -> float | None:
    return round(correct/total, 4) if total else None


def evaluate(predicted: dict, truth: dict) -> dict:
    errors = []
    preds, trues = predicted.get("nodes", []), truth["nodes"]
    candidates = sorted(((iou(p["bbox"], t["bbox"]), pi, ti)
                         for pi,p in enumerate(preds) for ti,t in enumerate(trues)), reverse=True)
    matched_p, matched_t, id_map = set(), set(), {}
    matches = []
    for overlap, pi, ti in candidates:
        if overlap < .5 or pi in matched_p or ti in matched_t:
            continue
        matched_p.add(pi); matched_t.add(ti)
        id_map[preds[pi]["id"]] = trues[ti]["id"]
        matches.append((preds[pi], trues[ti], overlap))
    for ti, t in enumerate(trues):
        if ti not in matched_t:
            errors.append({"kind":"missing_node","truth_id":t["id"],"truth_label":t["label"],"bbox":t["bbox"]})
    for pi, p in enumerate(preds):
        if pi not in matched_p:
            errors.append({"kind":"extra_node","predicted_id":p["id"],"predicted_label":p.get("label", ""),"bbox":p["bbox"]})
    exact_text = 0
    total_edits = 0
    total_chars = 0
    exact_type = 0
    total_iou = 0.0
    text_correct_by_truth_id = {}
    for p,t,overlap in matches:
        exact_type += p.get("type") == t.get("type")
        total_iou += overlap
        left, right = norm(p.get("label", "")), norm(t["label"])
        exact_text += left == right
        text_correct_by_truth_id[t["id"]] = left == right
        total_edits += edit_distance(left, right)
        total_chars += len(right)
        if left != right:
            errors.append({"kind":"wrong_node_text","truth_id":t["id"],"expected":right,"observed":left,
                           "character_edits":edit_distance(left,right),"bbox_iou":round(overlap,3)})
        if p.get("type") != t.get("type"):
            errors.append({"kind":"wrong_node_type","truth_id":t["id"],"expected":t.get("type"),
                           "observed":p.get("type")})
        if overlap < .9:
            errors.append({"kind":"bbox_mismatch","truth_id":t["id"],"bbox_iou":round(overlap,3),
                           "expected":t["bbox"],"observed":p["bbox"]})
    truth_edges = truth["edges"]
    pred_edges = predicted.get("edges", [])
    used = set()
    matched_edges = []
    for pi,p in enumerate(pred_edges):
        a,b = id_map.get(p.get("source")),id_map.get(p.get("target"))
        if not a or not b:
            errors.append({"kind":"edge_with_unmatched_endpoint","predicted_edge":p})
            continue
        possibilities = [(ti,t) for ti,t in enumerate(truth_edges)
                         if ti not in used and {a,b} == {t["source"],t["target"]}]
        if not possibilities:
            errors.append({"kind":"extra_edge","predicted_edge":p})
            continue
        ti,t = possibilities[0]
        used.add(ti)
        matched_edges.append((p,t,a,b))
        if (p.get("direction") != t["direction"] or
            (t["direction"] == "source_to_target" and (a,b) != (t["source"],t["target"]))):
            errors.append({"kind":"wrong_arrow","expected":f'{t["source"]}->{t["target"]}' if t["direction"] == "source_to_target" else "undirected",
                           "observed":f"{a}->{b}" if p.get("direction") == "source_to_target" else p.get("direction")})
        if norm(p.get("relationship", "unknown")) != norm(t["relationship"]):
            errors.append({"kind":"wrong_relationship","source":t["source"],"target":t["target"],
                           "expected":t["relationship"],"observed":p.get("relationship", "unknown")})
    for ti,t in enumerate(truth_edges):
        if ti not in used:
            errors.append({"kind":"missing_edge","truth_edge":t})
    correct_full = sum(
        p.get("direction") == t["direction"] and
        (t["direction"] != "source_to_target" or (a,b) == (t["source"],t["target"])) and
        norm(p.get("relationship", "unknown")) == norm(t["relationship"])
        for p,t,a,b in matched_edges)
    correct_end_to_end = sum(
        p.get("direction") == t["direction"] and
        (t["direction"] != "source_to_target" or (a,b) == (t["source"],t["target"])) and
        norm(p.get("relationship", "unknown")) == norm(t["relationship"]) and
        text_correct_by_truth_id.get(a,False) and text_correct_by_truth_id.get(b,False)
        for p,t,a,b in matched_edges)
    correct_arrow = sum(p.get("direction") == t["direction"] and
                        (t["direction"] != "source_to_target" or (a,b) == (t["source"],t["target"]))
                        for p,t,a,b in matched_edges)
    correct_relation = sum(norm(p.get("relationship", "unknown")) == norm(t["relationship"])
                           for p,t,a,b in matched_edges)
    expected_text = [truth.get("rendered_title", truth["title"] + " · synteettinen testikaavio")]
    expected_text += [n["label"] for n in trues]
    expected_text += [e["relationship"] for e in truth_edges]
    observed_text = predicted.get("visible_text", [])
    expected_counts = Counter(norm(s) for s in expected_text if norm(s))
    observed_counts = Counter(norm(s) for s in observed_text if norm(s) and norm(s) != "unknown")
    text_matches = sum(min(expected_counts[s], observed_counts[s]) for s in expected_counts)
    for label, count in (expected_counts - observed_counts).items():
        errors.append({"kind":"missing_visible_text","text":label,"count":count})
    for label, count in (observed_counts - expected_counts).items():
        errors.append({"kind":"extra_or_wrong_visible_text","text":label,"count":count})
    return {"counts":{"truth_nodes":len(trues),"predicted_nodes":len(preds),"matched_nodes":len(matches),
                      "truth_edges":len(truth_edges),"predicted_edges":len(pred_edges),"matched_topology":len(matched_edges),
                      "truth_text_items":sum(expected_counts.values()),"observed_text_items":sum(observed_counts.values())},
            "metrics":{
                "node_precision":ratio(len(matches),len(preds)),
                "node_recall":ratio(len(matches),len(trues)),
                "node_text_exact":ratio(exact_text,len(matches)),
                "node_label_recall":ratio(exact_text,len(trues)),
                "node_cer":round(total_edits/total_chars,4) if total_chars else None,
                "node_type_exact":ratio(exact_type,len(matches)),
                "mean_bbox_iou":round(total_iou/len(matches),4) if matches else None,
                "visible_text_precision":ratio(text_matches,sum(observed_counts.values())),
                "visible_text_recall":ratio(text_matches,sum(expected_counts.values())),
                "topology_precision":ratio(len(matched_edges),len(pred_edges)),
                "topology_recall":ratio(len(matched_edges),len(truth_edges)),
                "arrow_accuracy":ratio(correct_arrow,len(matched_edges)),
                "relationship_exact":ratio(correct_relation,len(matched_edges)),
                "full_edge_precision":ratio(correct_full,len(pred_edges)),
                "full_edge_recall":ratio(correct_full,len(truth_edges)),
                "end_to_end_edge_precision":ratio(correct_end_to_end,len(pred_edges)),
                "end_to_end_edge_recall":ratio(correct_end_to_end,len(truth_edges))},
            "errors":errors}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
