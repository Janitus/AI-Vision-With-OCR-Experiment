"""Build comparable v4 matrix, error ledger, report, and offline viewer."""
import csv
import html
import json
from pathlib import Path

from export_viewer import render

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def pct(n, d):
    return round(100 * n / d, 1) if d else None


def main():
    mapping = read(ROOT / "blind_mapping.json")
    qa = read(ROOT / "text_qa.json")
    edge_qa = read(ROOT / "edge_qa.json")
    ocr = {r["approach"]: r for r in read(ROOT / "ocr_matrix.json")}
    total = sum(1 + len(read(ROOT / f"{s}.source.json")["nodes"]) + len(read(ROOT / f"{s}.source.json")["edges"]) for s in mapping.values())
    rows, ledger = [], []
    for name, label in [("rapid_v6_medium_fi", "RapidOCR PP-OCRv6 Finnish"), ("paddle_v5_fi", "PaddleOCR PP-OCRv5 Finnish"), ("legacy_rapid_v3", "Older RapidOCR baseline")]:
        t = ocr[name]["totals"]
        misses = t["all"]["total"] - t["all"]["exact"]
        extras = t["all"]["extra_ocr_items"]
        assert t["all"]["total"] == total
        rows.append(dict(approach=label, mode="OCR text", source_items=total, errors=misses + extras, error_rate=pct(misses + extras, total),
                         exact_text=t["all"]["exact"], extra_text=extras, title_errors=t["title"]["total"]-t["title"]["exact"],
                         node_label_errors=t["node"]["total"]-t["node"]["exact"], edge_label_errors=t["edge"]["total"]-t["edge"]["exact"],
                         shape_mismatches=None, missing_nodes=None, extra_nodes=None, missing_edges=None, extra_edges=None,
                         wrong_arrows=None, unresolved_directed_arrows=None, arrowless_semantics_unknown=None, wrong_strokes=None,
                         fully_correct_edges=None, node_precision=None, node_recall=None, edge_precision=None, edge_recall=None,
                         perfect_figures=sum(x["all"]["exact"]==x["all"]["total"] and x["all"]["extra_ocr_items"]==0 for x in ocr[name]["cases"].values())))
        for case, slug in mapping.items():
            report=read(ROOT / "reports" / f"{name}_{slug}.json")
            for item in report["details"]:
                if not item["exact"]:
                    ledger.append(dict(approach=name, case=case, kind="ocr_"+item["kind"]+"_text", expected=item["expected"], observed=item["observed"], bbox=item["bbox"]))
            for item in report["unmatched_ocr"]:
                ledger.append(dict(approach=name, case=case, kind="unmatched_ocr_box", observed=item["text"], bbox=item["bbox"]))
    graph_names=[("blind_vision", "Blind Codex vision"), ("blind_fusion", "Blind Codex + RapidOCR"), ("vision_ocr_union", "Vision + deterministic OCR evidence")]
    for name, label in graph_names:
        s=read(ROOT / name / "scores.json"); c=s["counts"]
        assert 10+c["truth_nodes"]+c["truth_edges"] == total
        extras=(c["predicted_nodes"]-c["matched_nodes"])+(c["predicted_edges"]-c["matched_topology"])
        good=c["title_exact"]+c["fully_correct_nodes"]+c["fully_correct_edges"]
        kinds={}
        for case, result in s["cases"].items():
            for item in result["errors"]:
                kinds[item["kind"]]=kinds.get(item["kind"],0)+1
                ledger.append(dict(approach=name,case=case,**item))
        rows.append(dict(approach=label, mode="Graph", source_items=total, errors=total-good+extras, error_rate=pct(total-good+extras,total),
                         exact_text=None, extra_text=None, title_errors=10-c["title_exact"], node_label_errors=c["truth_nodes"]-c["exact_node_labels"],
                         edge_label_errors=c["truth_edges"]-c["correct_relationships"], shape_mismatches=kinds.get("wrong_node_shape",0),
                         missing_nodes=kinds.get("missing_node",0), extra_nodes=kinds.get("extra_node",0), missing_edges=kinds.get("missing_edge",0),
                         extra_edges=kinds.get("extra_edge",0), wrong_arrows=c["wrong_arrows"], unresolved_directed_arrows=c["unresolved_arrows"],
                         arrowless_semantics_unknown=kinds.get("arrowless_semantics_unknown",0), wrong_strokes=kinds.get("wrong_stroke",0),
                         fully_correct_edges=c["fully_correct_edges"], node_precision=s["node_precision"], node_recall=s["node_recall"],
                         edge_precision=s["edge_precision"], edge_recall=s["edge_recall"], perfect_figures=s["perfect_figures"]))
    keys=list(rows[0]);
    with (ROOT/"approach_matrix.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    (ROOT/"approach_matrix.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    (ROOT/"item_error_ledger.json").write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding="utf-8")
    audit=dict(case_count=len(mapping), source_items=total, clipped_text=sum(v["clipped_text_count"] for v in qa.values()),
               overlapping_text=sum(v["overlapping_text_count"] for v in qa.values()),
               hidden_edges=sum(v["hidden_by_nonendpoint_nodes"] for v in edge_qa.values()),
               coincident_edge_pairs=sum(v["coincident_edge_pairs"] for v in edge_qa.values()),
               minimum_text_contrast=min(v["minimum_text_contrast"] for v in qa.values()),
               blind_inputs_scored_after_predictions_saved=True,
               blind_access_logs=["blind_vision/access_log.txt","blind_fusion/access_log.txt"],
               blinding="procedural; agent file access was self-reported, not independently enforced")
    (ROOT/"validation.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
    lines=["# Corrected ten-diagram benchmark (v4)","",
           "The earlier v3 graph rates should not be used as visible-error rates: several source links were hidden by nodes or coincident with other links. This v4 set removes eight such source edges, leaving 83 nodes and 105 edges across ten Finnish-context figures. The PDF's earlier red annotation was corrected separately.","",
           f"Source QA: {audit['clipped_text']} clipped text regions; {audit['overlapping_text']} overlapping text regions; {audit['hidden_edges']} edges hidden by a non-endpoint node; {audit['coincident_edge_pairs']} coincident edge pairs. Minimum text contrast {audit['minimum_text_contrast']:.2f}:1. All ten images were inspected visually.","",
           "## Matrix","",
           "| Approach | Task | Total scorer events / 198 | Exact figures | Title | Node text | Edge text | Shape | Arrow | Extra text |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        fmt=lambda v: "—" if v is None else str(v)
        arrows=None if r["wrong_arrows"] is None else r["wrong_arrows"]+r["unresolved_directed_arrows"]
        lines.append(f"| {r['approach']} | {r['mode']} | {r['errors']}/198 ({r['error_rate']:.1f}%) | {r['perfect_figures']}/10 | {r['title_errors']} | {r['node_label_errors']} | {r['edge_label_errors']} | {fmt(r['shape_mismatches'])} | {fmt(arrows)} | {fmt(r['extra_text'])} |")
    lines += ["", "OCR rows score exact printed title, node, and edge text at source positions, plus unmatched OCR boxes. Graph rows score exact titles, nodes (label and shape), and complete visual edges (endpoints, printed relationship, arrowheads, stroke). All rows use the same 198 source items, but OCR and graph tasks differ. The rate can exceed 100% if extra outputs are numerous.","",
              "Graph precision/recall (P/R) is in `approach_matrix.csv`. It means the fraction of reported nodes/connections that matched, and the fraction of source nodes/connections found. Shape mismatches are retained as strict taxonomy disagreements: ellipse/pill and pill/rounded rectangle in these figures. The edge scores concern visible marks, not semantic truth outside the figure.","",
              "An arrowless stroke shows no arrowhead. A prediction of `unknown` for its semantic direction is accepted as visually faithful and logged separately; it is not an arrow error. The independent OCR+vision run used RapidOCR PP-OCRv6 medium Finnish. The deterministic union only attaches OCR evidence to an existing vision graph; identical graph scores are expected.","",
              "## Error interpretation","",
              "The image-only run recovered all 105 source edge records under this scorer, and the OCR+vision run also recovered all 105 after the arrowless correction. The remaining strict graph events are shape-category disagreements. These results supersede the v3 rates and do not support a claim that vision fails on most clean synthetic diagrams. The two agents had access to crisp generated figures, ample time, and precise extraction instructions; this is not a universal accuracy estimate.","",
              "See `item_error_ledger.json` for each mismatch and `validation.json` for QA. Blind agents received anonymous images (and RapidOCR observations for fusion), saved predictions before scoring, and supplied access logs. Isolation was procedural, not filesystem-enforced. The source graphs, PNGs, Mermaid, raw OCR, predictions, and viewer are retained for review."]
    (ROOT/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    # Offline four-way visual comparison.
    entries=[]
    for case,slug in mapping.items():
        item=dict(case=case,title=read(ROOT/f"{slug}.source.json")["title"],source=f"{slug}.png")
        for name in ("blind_vision","blind_fusion"):
            graph=read(ROOT/name/"predictions"/f"{case}.json")
            target=ROOT/name/"rendered";target.mkdir(exist_ok=True)
            render(graph,target/f"{case}.png")
            item[name]=f"{name}/rendered/{case}.png"
            item[name+"_uncertainties"]=graph.get("uncertainties",[])
        entries.append(item)
    case_sections=[]
    for index,item in enumerate(entries,1):
        figures="".join(
            f'<figure><figcaption>{label}</figcaption><img src="{html.escape(item[key],quote=True)}" alt="{html.escape(label+" for "+item["title"],quote=True)}"></figure>'
            for key,label in (("source","Source"),("blind_vision","Blind vision"),("blind_fusion","Blind vision + OCR"))
        )
        case_sections.append(f'<details id="{item["case"]}" {("open" if index==1 else "")}><summary>{index}. {html.escape(item["title"])}</summary><section>{figures}</section><p>Vision uncertainties: {len(item["blind_vision_uncertainties"])}; fusion uncertainties: {len(item["blind_fusion_uncertainties"])}.</p></details>')
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Corrected graph benchmark v4</title><style>body{{font:16px system-ui;background:#f5f7fa;color:#172d3c;margin:20px}}main{{max-width:1850px;margin:auto}}section{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:12px}}figure{{margin:0;background:white;border:1px solid #bdcbd3;padding:8px}}img{{width:100%;height:auto;display:block}}figcaption{{font-weight:bold}}details{{background:white;border:1px solid #bdcbd3;margin:10px 0;padding:10px}}summary{{cursor:pointer;font-weight:bold}}table{{border-collapse:collapse;background:white;width:100%}}td,th{{padding:8px;border:1px solid #ccd7df;text-align:left}}th{{background:#e8f0f6}}.scroll{{overflow-x:auto}}@media(max-width:900px){{section{{grid-template-columns:1fr}}}}</style><main><h1>Corrected graph extraction benchmark</h1><p>Ten Finnish-context figures. Source links hidden behind unrelated nodes or overlapping other links were removed before this rerun. Open any case to compare its three images.</p>{''.join(case_sections)}<h2>Approach matrix</h2><div class="scroll"><table><thead><tr><th>Approach</th><th>Task</th><th>Scorer events / 198</th><th>Exact figures</th><th>Node text errors</th><th>Edge text errors</th><th>Shape mismatches</th><th>Arrow errors</th></tr></thead><tbody>'''
    for r in rows:
        values=[r["approach"],r["mode"],f"{r['errors']}/198 ({r['error_rate']:.1f}%)",f"{r['perfect_figures']}/10",r["node_label_errors"],r["edge_label_errors"],r["shape_mismatches"] if r["shape_mismatches"] is not None else "—",(r["wrong_arrows"]+r["unresolved_directed_arrows"]) if r["wrong_arrows"] is not None else "—"]
        page+="<tr>"+"".join(f"<td>{html.escape(str(v))}</td>" for v in values)+"</tr>"
    page+='''</tbody></table></div><p>OCR text and graph rows use different scoring rules. Shape mismatches are strict visual taxonomy differences. <a href="REPORT.md">Validation report</a> · <a href="approach_matrix.csv">CSV</a> · <a href="item_error_ledger.json">Error ledger</a></p></main></html>'''
    (ROOT/"results_viewer.html").write_text(page,encoding="utf-8")
    print("Wrote",len(rows),"matrix rows;",len(ledger),"ledger records; source items",total)


if __name__ == "__main__":
    main()
