"""Build the approach matrix, explicit error ledger, and validation report."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def load(path):return json.loads(path.read_text(encoding="utf-8"))
def rate(good,total):return round(good/total,4) if total else None


def main():
    ocr=load(ROOT/"ocr_matrix.json")
    mapping=load(ROOT/"blind_mapping.json")
    qa=load(ROOT/"text_qa.json")
    rows=[];ledger=[]
    for run in ocr:
        t=run["totals"];a=t["all"]
        rows.append({"approach":run["approach"],"modality":"OCR only", "cases":run["cases_ran"],
            "title_text_error":rate(t["title"]["total"]-t["title"]["exact"],t["title"]["total"]),
            "node_text_error":rate(t["node"]["total"]-t["node"]["exact"],t["node"]["total"]),
            "edge_text_error":rate(t["edge"]["total"]-t["edge"]["exact"],t["edge"]["total"]),
            "all_text_error":rate(a["total"]-a["exact"],a["total"]),
            "text_precision":a["precision"],"text_recall":a["recall"],
            "false_positive_text":a["extra_ocr_items"],"node_precision":None,"node_recall":None,
            "false_positive_nodes":None,"edge_precision":None,"edge_recall":None,
            "false_positive_edges":None,"arrow_error":None,"relationship_error":None,
            "dashed_error":None,"shape_error":None,"unknown_relationships":None,"full_edge_error":None})
        for case,slug in mapping.items():
            path=ROOT/"reports"/f"{run['approach']}_{slug}.json"
            if not path.exists():continue
            result=load(path)
            for item in result["details"]:
                if not item["exact"]:ledger.append({"approach":run["approach"],"case":case,"slug":slug,
                    "kind":"wrong_"+item["kind"]+"_text","expected":item["expected"],"observed":item["observed"],
                    "bbox":item["bbox"]})
            for item in result["unmatched_ocr"]:
                ledger.append({"approach":run["approach"],"case":case,"slug":slug,
                    "kind":"extra_ocr_text","observed":item["text"],"bbox":item["bbox"]})
    for approach in ("blind_vision","blind_fusion"):
        scores=load(ROOT/approach/"scores.json");c=scores["counts"];r=scores["error_rates"]
        rows.append({"approach":approach,"modality":"Codex vision" if approach=="blind_vision" else "Codex vision + RapidOCR PP-OCRv6 medium Finnish",
            "cases":len(scores["cases"]),"title_text_error":r["title_error_rate"],
            "node_text_error":r["node_label_error_rate"],"edge_text_error":r["relationship_error_rate"],
            "all_text_error":None,"text_precision":None,"text_recall":None,"false_positive_text":None,
            "node_precision":scores["node_precision"],"node_recall":scores["node_recall"],
            "false_positive_nodes":c["predicted_nodes"]-c["matched_nodes"],
            "edge_precision":scores["edge_precision"],"edge_recall":scores["edge_recall"],
            "false_positive_edges":c["predicted_edges"]-c["matched_topology"],
            "arrow_error":r["arrow_error_rate"],"relationship_error":r["relationship_error_rate"],
            "dashed_error":r["stroke_error_rate"],"shape_error":r["node_shape_error_rate"],
            "unknown_relationships":scores["unknown_relationships"],"full_edge_error":r["full_edge_error_rate"]})
        for case,result in scores["cases"].items():
            for err in result["errors"]:ledger.append({"approach":approach,"case":case,
                "slug":mapping[case],**err})
    ocr_by_name={run["approach"]:run for run in ocr}
    for row in rows:
        if row["modality"]=="OCR only":
            totals=ocr_by_name[row["approach"]]["totals"]["all"]
            expected=totals["total"]
            correct=totals["exact"]
            extras=totals["extra_ocr_items"]
        else:
            counts=load(ROOT/row["approach"]/"scores.json")["counts"]
            expected=len(mapping)+counts["truth_nodes"]+counts["truth_edges"]
            correct=counts["title_exact"]+counts["fully_correct_nodes"]+counts["fully_correct_edges"]
            extras=(counts["predicted_nodes"]-counts["matched_nodes"])+(
                counts["predicted_edges"]-counts["matched_topology"])
        row["total_error_count"]=expected-correct+extras
        row["total_items_scored"]=expected+extras
        row["total_error_rate"]=rate(row["total_error_count"],row["total_items_scored"])
    keys=["approach","modality","cases","total_error_count","total_items_scored","total_error_rate"]+[k for k in rows[0] if k not in {"approach","modality","cases","total_error_count","total_items_scored","total_error_rate"}]
    with (ROOT/"approach_matrix.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    (ROOT/"approach_matrix.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    (ROOT/"item_error_ledger.json").write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding="utf-8")
    min_contrast=min(v["minimum_text_contrast"] for v in qa.values())
    clipped=sum(v["clipped_text_count"] for v in qa.values())
    overlapped=sum(v["overlapping_text_count"] for v in qa.values())
    total_nodes=sum(len(load(ROOT/f"{slug}.source.json")["nodes"]) for slug in mapping.values())
    total_edges=sum(len(load(ROOT/f"{slug}.source.json")["edges"]) for slug in mapping.values())
    notes=[]
    for approach in ("blind_vision","blind_fusion"):
        for case in mapping:
            pred=load(ROOT/approach/"predictions"/f"{case}.json")
            for detail in pred.get("uncertainties",[]):
                notes.append({"approach":approach,"case":case,"kind":"self_reported_uncertainty","detail":detail})
            for detail in pred.get("ocr_disagreements",[]):
                notes.append({"approach":approach,"case":case,"kind":"ocr_vision_disagreement","detail":detail})
    (ROOT/"uncertainties.json").write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Benchmark v3 validation report","",
        f"Ten new Finnish-context figures contain {total_nodes} nodes and {total_edges} edges (v2: 49 nodes, 41 edges). Mermaid source, structured truth, rendered images, raw OCR, and blind predictions are retained separately.","",
        "## Source image QA","",
        f"Automated text checks: {clipped} clipped labels, {overlapped} overlapping text regions; minimum text/background contrast {min_contrast:.2f}:1. All ten PNGs were inspected with `view_image`. Text-only nodes have a background patch that keeps lines from crossing letters. Shape boundaries and every printed label are fully visible. The diagrams are synthetic Finnish-context examples, not verified real-world organizational facts.","",
        "## Approach matrix","",
        "**P/R means precision/recall.** Precision asks: of the nodes or connections the method reported, what fraction matched the source? Recall asks: of the source nodes or connections, what fraction did it find? Connection matching checks endpoints; arrow, label, and stroke are scored separately. For example, vision-only edge P/R of 96.3%/92.9% means 105 of 109 reported connections and 105 of 113 source connections matched.","",
        "**Total error** counts wrong or missing source items plus extra reported items, divided by source items plus extra items. For OCR, an item is one printed text region (title, node label, or edge label). For vision, an item is a title, a node with the correct label and shape, or an edge with the correct endpoints, arrow, label, and dashed state. Extra items raise the error count and denominator. The OCR and vision totals cover different outputs, so compare within each modality; the per-type columns show why a row failed.","",
        "Other rates are errors divided by expected items; lower is better. `—` means the approach does not produce that output. OCR text scores use location-matched visible text regions, including rotated edge labels. Graph scores use coordinate-matched nodes (155 px tolerance). Missing edges count as errors in each edge error rate.","",
        "| Approach | Total error | Title text error | Node text error | Edge text error | Node P/R | Edge P/R | Arrow error | Shape error | Full edge error | False positives |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    def pct(v):return "—" if v is None else f"{v*100:.1f}%"
    for r in rows:
        fp=(f"{r['false_positive_text']} text" if r["modality"]=="OCR only" else
            f"{r['false_positive_nodes']} nodes, {r['false_positive_edges']} edges")
        lines.append(f"| {r['approach']} | {r['total_error_count']}/{r['total_items_scored']} ({pct(r['total_error_rate'])}) | {pct(r['title_text_error'])} | {pct(r['node_text_error'])} | {pct(r['edge_text_error'])} | {pct(r['node_precision'])}/{pct(r['node_recall'])} | {pct(r['edge_precision'])}/{pct(r['edge_recall'])} | {pct(r['arrow_error'])} | {pct(r['shape_error'])} | {pct(r['full_edge_error'])} | {fp} |")
    lines += ["","Other per-type rates and counts, including relationship, dashed stroke, unknowns, all visible text, and false positives, are in [approach_matrix.csv](approach_matrix.csv). Every mismatch and extra item is in [item_error_ledger.json](item_error_ledger.json). Self-reported ambiguities and OCR/vision conflicts are in [uncertainties.json](uncertainties.json). Unmatched OCR snippets are potential false positives under this spatial matcher; some could be misplaced fragments of real text.", "",
        "## Observed result", "",
        "RapidOCR PP-OCRv6 was strongest on literal text here: 203/206 exact visible regions, versus PaddleOCR's 187/206 and the old baseline's 145/206. Both Codex sessions found all 83 nodes and read their labels exactly. Vision-only recovered 105/113 connections and 101/113 fully correct edges; fusion recovered 107/113 connections but 94/113 fully correct edges. OCR assistance coincided with two more found connections, while the fully correct edge count fell by seven. These separate sessions cannot isolate OCR as the cause of either difference.", "",
        "## Blind evaluation protocol", "",
        "The two fresh Codex tasks received anonymous case images. Blind fusion also received the ten raw outputs from **RapidOCR 3.10, PP-OCRv6 medium, configured for Finnish detection and recognition**. Codex visually compared those OCR strings and polygons with each image and wrote its own graph prediction; there was no automated text-merging algorithm. PaddleOCR and the older OCR baseline were scored separately; neither fed blind fusion. Neither prompt provided source Mermaid, truth JSON, prior results, or case mapping. Predictions were written before this scoring step. The task logs were audited for file/tool access; this is a procedural blind test, not filesystem isolation. See `session_audit.json`.", "",
        "## Interpretation and limits", "",
        "The source PNGs were drawn by the Python renderer from the same structured graphs exported as Mermaid; the Mermaid text is a reproducible graph definition, not the exact pixel renderer. OCR-only rows measure text recognition and do not claim graph reconstruction. Vision rows measure one session each, so differences between them cannot establish a general causal gain from OCR. The figures are clean synthetic diagrams; performance on scanned academic pages or production diagrams may be lower. Edge text accuracy is literal exact match, and connection matching uses endpoint proximity, not semantic equivalence.", "",
        "Open [results_viewer.html](results_viewer.html) for source, vision-only, and fusion figures side by side."]
    (ROOT/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("Matrix rows:",len(rows),"ledger items:",len(ledger),"QA:",clipped,overlapped,min_contrast)


if __name__=="__main__":main()
