"""Build the approach matrix, explicit error ledger, and validation report."""
import csv
import html
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
    union_stats=load(ROOT/"vision_ocr_union"/"union_summary.json")
    rows=[];ledger=[]
    ocr_order={"rapid_v6_medium_fi":0,"paddle_v5_fi":1,"legacy_rapid_v3":2}
    for run in sorted(ocr,key=lambda item:ocr_order.get(item["approach"],99)):
        t=run["totals"];a=t["all"]
        rows.append({"approach":run["approach"],"modality":"OCR only", "cases":run["cases_ran"],
            "title_text_error":rate(t["title"]["total"]-t["title"]["exact"],t["title"]["total"]),
            "node_text_error":rate(t["node"]["total"]-t["node"]["exact"],t["node"]["total"]),
            "edge_text_error":rate(t["edge"]["total"]-t["edge"]["exact"],t["edge"]["total"]),
            "all_text_error":rate(a["total"]-a["exact"],a["total"]),
            "text_precision":a["precision"],"text_recall":a["recall"],
            "false_positive_text":a["extra_ocr_items"],
            "perfect_figures":sum(case["all"]["exact"]==case["all"]["total"] and
                                  case["all"]["extra_ocr_items"]==0
                                  for case in run["cases"].values()),
            "node_precision":None,"node_recall":None,
            "false_positive_nodes":None,"edge_precision":None,"edge_recall":None,
            "false_positive_edges":None,"arrow_error":None,"wrong_arrow":None,
            "unresolved_arrow":None,"relationship_error":None,
            "dashed_error":None,"shape_error":None,"unknown_directions":None,
            "unknown_relationships":None,"full_edge_error":None})
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
    for approach in ("blind_vision","vision_ocr_union"):
        scores=load(ROOT/approach/"scores.json");c=scores["counts"];r=scores["error_rates"]
        rows.append({"approach":approach,"modality":"Codex vision" if approach=="blind_vision" else "Vision graph + deduplicated RapidOCR evidence",
            "cases":len(scores["cases"]),"title_text_error":r["title_error_rate"],
            "perfect_figures":scores["perfect_figures"],
            "node_text_error":r["node_label_error_rate"],"edge_text_error":r["relationship_error_rate"],
            "all_text_error":None,"text_precision":None,"text_recall":None,"false_positive_text":None,
            "node_precision":scores["node_precision"],"node_recall":scores["node_recall"],
            "false_positive_nodes":c["predicted_nodes"]-c["matched_nodes"],
            "edge_precision":scores["edge_precision"],"edge_recall":scores["edge_recall"],
            "false_positive_edges":c["predicted_edges"]-c["matched_topology"],
            "arrow_error":r["arrow_error_rate"],"wrong_arrow":r["wrong_arrow_rate"],
            "unresolved_arrow":r["unresolved_arrow_rate"],
            "relationship_error":r["relationship_error_rate"],
            "dashed_error":r["stroke_error_rate"],"shape_error":r["node_shape_error_rate"],
            "unknown_directions":scores["unknown_directions"],
            "unknown_relationships":scores["unknown_relationships"],"full_edge_error":r["full_edge_error_rate"]})
        for case,result in scores["cases"].items():
            for err in result["errors"]:ledger.append({"approach":approach,"case":case,
                "slug":mapping[case],**err})
    ocr_by_name={run["approach"]:run for run in ocr}
    for row in rows:
        if row["modality"]=="OCR only":
            row["total_error_scope"]="OCR text regions only"
            totals=ocr_by_name[row["approach"]]["totals"]["all"]
            expected=totals["total"]
            correct=totals["exact"]
            extras=totals["extra_ocr_items"]
        else:
            row["total_error_scope"]="graph titles, nodes, and complete edges"
            counts=load(ROOT/row["approach"]/"scores.json")["counts"]
            expected=len(mapping)+counts["truth_nodes"]+counts["truth_edges"]
            correct=counts["title_exact"]+counts["fully_correct_nodes"]+counts["fully_correct_edges"]
            extras=(counts["predicted_nodes"]-counts["matched_nodes"])+(
                counts["predicted_edges"]-counts["matched_topology"])
        row["total_error_count"]=expected-correct+extras
        row["source_items"]=expected
        row["total_error_rate"]=rate(row["total_error_count"],expected)
    keys=["approach","modality","cases","total_error_scope","total_error_count","source_items","total_error_rate"]+[k for k in rows[0] if k not in {"approach","modality","cases","total_error_scope","total_error_count","source_items","total_error_rate"}]
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
    for approach in ("blind_vision","vision_ocr_union"):
        for case in mapping:
            pred=load(ROOT/approach/"predictions"/f"{case}.json")
            for detail in pred.get("uncertainties",[]):
                notes.append({"approach":approach,"case":case,"kind":"self_reported_uncertainty","detail":detail})
            for detail in pred.get("ocr_disagreements",[]):
                notes.append({"approach":approach,"case":case,"kind":"ocr_vision_disagreement","detail":detail})
            for detail in pred.get("ocr_unassigned",[]):
                notes.append({"approach":approach,"case":case,"kind":"unassigned_ocr_box","detail":detail})
    (ROOT/"uncertainties.json").write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding="utf-8")
    lines=["# Benchmark v3 validation report","",
        f"Ten new Finnish-context figures contain {total_nodes} nodes and {total_edges} edges (v2: 49 nodes, 41 edges). Mermaid source, structured truth, rendered images, raw OCR, and blind predictions are retained separately.","",
        "## Source image QA","",
        f"Automated text checks: {clipped} clipped labels, {overlapped} overlapping text regions; minimum text/background contrast {min_contrast:.2f}:1. All ten PNGs were inspected with `view_image`. Text-only nodes have a background patch that keeps lines from crossing letters. Shape boundaries and every printed label are fully visible. The diagrams are synthetic Finnish-context examples, not verified real-world organizational facts.","",
        "## Approach matrix","",
        "**P/R means precision/recall.** Precision asks: of the nodes or connections the method reported, what fraction matched the source? Recall asks: of the source nodes or connections, what fraction did it find? Connection matching checks endpoints; arrow, label, and stroke are scored separately. For example, vision-only edge P/R of 96.3%/92.9% means 105 of 109 reported connections and 105 of 113 source connections matched.","",
        "**Total errors per source item** uses the same fixed denominator for all approaches: 206 source items (10 titles, 83 nodes, 113 edges). The numerator is wrong or missing source items plus extra reported outputs. OCR rows score printed text regions only; graph rows score titles, nodes with exact label and shape, and edges with exact endpoints, arrow, label, and stroke. The denominator is numerically equal, but the checks differ. Compare OCR engines with each other, then compare vision with the deterministic vision+OCR union. The rate could exceed 100% if a method emitted many extras.","",
        "Other rates are errors divided by expected items; lower is better. `—` means the approach does not produce that output. OCR text scores use location-matched visible text regions, including rotated edge labels. Graph scores use coordinate-matched nodes (155 px tolerance). Missing edges count as errors in each edge error rate.","",
        "| Approach | Scored unit | Errors / 206 source items | Error-free figures / 10 |",
        "|---|---|---:|---:|"]
    def pct(v):return "—" if v is None else f"{v*100:.1f}%"
    for r in rows:
        scope="OCR text" if r["modality"]=="OCR only" else "Graph"
        lines.append(f"| {r['approach']} | {scope} | {r['total_error_count']}/{r['source_items']} ({pct(r['total_error_rate'])}) | {r['perfect_figures']}/10 |")
    lines += ["", "### OCR text errors", "",
        "| Approach | Title | Node labels | Edge labels | Unmatched OCR boxes |",
        "|---|---:|---:|---:|---:|"]
    for r in rows[:3]:
        lines.append(f"| {r['approach']} | {pct(r['title_text_error'])} | {pct(r['node_text_error'])} | {pct(r['edge_text_error'])} | {r['false_positive_text']} |")
    lines += ["", "### Graph detection", "",
        "| Approach | Node P/R | Connection P/R | Extra nodes | Extra edges |",
        "|---|---:|---:|---:|---:|"]
    for r in rows[3:]:
        lines.append(f"| {r['approach']} | {pct(r['node_precision'])}/{pct(r['node_recall'])} | {pct(r['edge_precision'])}/{pct(r['edge_recall'])} | {r['false_positive_nodes']} | {r['false_positive_edges']} |")
    lines += ["", "### Graph error types", "",
        "| Error type | Vision only | Vision + OCR union |",
        "|---|---:|---:|"]
    for label,key in [("Title text","title_text_error"),("Node label","node_text_error"),
                      ("Edge label","edge_text_error"),("Arrow not established (missing, wrong, or unknown)","arrow_error"),
                      ("Arrow visibly wrong","wrong_arrow"),("Arrow unresolved","unresolved_arrow"),
                      ("Dashed/solid stroke","dashed_error"),("Node shape","shape_error"),
                      ("Fully correct edge","full_edge_error")]:
        lines.append(f"| {label} | {pct(rows[3][key])} | {pct(rows[4][key])} |")
    lines += ["| Unknown directions (count) | " + str(rows[3]["unknown_directions"]) + " | " + str(rows[4]["unknown_directions"]) + " |"]
    lines += ["","An `unknown` arrow direction is logged as `unresolved_arrow`, not `wrong_arrow`. It still prevents a fully correct edge because the graph cannot be used without resolving that direction. Arrowless source links are scored against the source's visible no-arrow mark; the benchmark does not infer whether the underlying relationship is semantically undirected.", "",
        "Other per-type rates and counts are in [approach_matrix.csv](approach_matrix.csv). Every mismatch and extra item is in [item_error_ledger.json](item_error_ledger.json). Self-reported ambiguities and OCR conflicts are in [uncertainties.json](uncertainties.json). An unmatched OCR box may be a false detection or a misplaced fragment of real text.", "",
        "## Observed result", "",
        f"RapidOCR PP-OCRv6 read 203/206 visible text regions exactly; PaddleOCR read 187/206 and the old baseline 145/206. OCR-only does not reconstruct a graph. Vision-only recovered 105/113 connections and 101/113 fully correct edges, with four of ten figures entirely error-free under this rubric. The deterministic union matched {union_stats['exact_matches']} OCR boxes to existing vision text and retained {union_stats['unmatched_boxes']} unassigned boxes across {union_stats['cases_with_unmatched_boxes']}/10 figures. It added no nodes or edges, so its graph scores and four error-free figures match vision-only. The current union leaves those OCR boxes unresolved rather than silently discarding or promoting them. These results do not support fully automated, review-free reconstruction of every tested diagram.", "",
        "For the earlier independent joint Codex run, `plain` and `text` are both treated as unboxed shapes. Its `unknown` arrows are recorded as unresolved rather than visibly wrong; they still make those edges incomplete. That historical run is retained as a separate record and is not pooled with the deterministic union.", "",
        "## Blind evaluation protocol", "",
        "A fresh Codex task received anonymous images and saved its vision predictions before scoring. The deterministic union then read those saved predictions and **RapidOCR 3.10 PP-OCRv6 medium Finnish** observations. It assigns an exact-text OCR box to at most one vision element, retains unmatched OCR boxes, and never promotes OCR alone into a node or edge. The union script does not read source JSON. An earlier separate Codex task also read images plus raw OCR and produced a joint prediction; its historical result remains in [blind_fusion/scores.json](blind_fusion/scores.json), but it is not the deterministic union row. Task logs were audited for file access; blinding was procedural, not filesystem-enforced. See [session_audit.json](session_audit.json).", "",
        "## Interpretation and limits", "",
        "The source PNGs were drawn by the Python renderer from the same structured graphs exported as Mermaid; the Mermaid text is a graph definition, not the pixel renderer. These ten clean, synthetic figures cover several styles but do not represent the full variety of diagrams. The union deliberately preserves vision topology, so its identical graph score is expected; it tests traceable evidence merging, not a new edge detector. The OCR scorer uses spatial text matching and the graph scorer uses coordinate proximity, both of which can affect individual results. An error-free figure here means no scored error, not a guarantee about unscored semantics or future figures.", "",
        "Open [matrix_viewer.html](matrix_viewer.html) for a readable matrix, or [results_viewer.html](results_viewer.html) for source, vision-only, and evidence-union figures side by side."]
    (ROOT/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")

    def table(headers,body):
        head="".join(f"<th scope='col'>{html.escape(str(h))}</th>" for h in headers)
        records="".join("<tr>"+"".join(f"<td>{html.escape(str(cell))}</td>" for cell in record)+"</tr>" for record in body)
        return f"<div class='scroll'><table><thead><tr>{head}</tr></thead><tbody>{records}</tbody></table></div>"
    summary=table(["Approach","Scored unit","Errors / 206 source items","Error-free figures"],[(r["approach"],"OCR text" if r["modality"]=="OCR only" else "Graph",f"{r['total_error_count']}/{r['source_items']} ({pct(r['total_error_rate'])})",f"{r['perfect_figures']}/10") for r in rows])
    ocr_table=table(["Approach","Title","Node labels","Edge labels","Unmatched OCR boxes"],[(r["approach"],pct(r["title_text_error"]),pct(r["node_text_error"]),pct(r["edge_text_error"]),r["false_positive_text"]) for r in rows[:3]])
    detection=table(["Approach","Node P/R","Connection P/R","Extra nodes","Extra edges"],[(r["approach"],f"{pct(r['node_precision'])}/{pct(r['node_recall'])}",f"{pct(r['edge_precision'])}/{pct(r['edge_recall'])}",r["false_positive_nodes"],r["false_positive_edges"]) for r in rows[3:]])
    graph_errors=table(["Error type","Vision only","Vision + OCR union"],[(label,pct(rows[3][key]),pct(rows[4][key])) for label,key in [("Title text","title_text_error"),("Node label","node_text_error"),("Edge label","edge_text_error"),("Arrow incomplete","arrow_error"),("Arrow visibly wrong","wrong_arrow"),("Arrow unresolved","unresolved_arrow"),("Dashed/solid stroke","dashed_error"),("Node shape","shape_error"),("Fully correct edge","full_edge_error")]]+[("Unknown directions (count)",rows[3]["unknown_directions"],rows[4]["unknown_directions"])])
    page=f"""<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>Benchmark v3 approach matrix</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;background:#f5f7fa;color:#172d3c;margin:24px}}main{{max-width:1050px;margin:auto}}h1{{font-size:1.9rem}}h2{{margin-top:32px}}.card{{background:white;border:1px solid #cbd5df;border-radius:10px;padding:18px;margin:18px 0}}.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;background:white}}th,td{{padding:10px 12px;border-bottom:1px solid #d8e1e8;text-align:left;vertical-align:top}}th{{background:#e8f0f6}}tr:nth-child(even) td{{background:#f8fafc}}a{{color:#145889}}.muted{{color:#4e6473}}</style>
<main><h1>Graph benchmark: approach matrix</h1><p class='muted'>Ten Finnish-context diagrams. All headline rates divide error events by the same 206 source items; extra outputs count as errors, not additional source items. OCR engines share a text task. Vision and the deduplicated vision+OCR union share a graph task.</p>
<div class='card'><h2>All five approaches</h2>{summary}</div>
<div class='card'><h2>OCR text errors</h2><p>Each source item is one printed title, node label, or edge label. An unmatched OCR box is an extra text detection, possibly a false detection or a misplaced fragment of real text.</p>{ocr_table}</div>
<div class='card'><h2>Graph detection</h2><p>P/R means precision/recall. Connection matching checks endpoint pairs; arrow and label correctness are scored below. The union retains vision's nodes and edges and attaches OCR as evidence.</p>{detection}</div>
<div class='card'><h2>Graph error types</h2>{graph_errors}</div>
<p><a href='results_viewer.html'>Compare graph images</a> · <a href='REPORT.md'>Read the validation report</a> · <a href='approach_matrix.csv' download>Download full CSV</a></p></main></html>"""
    (ROOT/"matrix_viewer.html").write_text(page,encoding="utf-8")
    print("Matrix rows:",len(rows),"ledger items:",len(ledger),"QA:",clipped,overlapped,min_contrast)


if __name__=="__main__":main()
