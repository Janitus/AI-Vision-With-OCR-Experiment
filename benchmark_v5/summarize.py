"""Build comparable v5 matrix, paired-route results, ledger, and viewer."""
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
    graph_names=[("blind_vision", "Blind Codex vision"), ("blind_fusion", "Blind Codex + RapidOCR")]
    for name, label in graph_names:
        s=read(ROOT / name / "scores.json"); c=s["counts"]
        assert len(mapping)+c["truth_nodes"]+c["truth_edges"] == total
        extras=(c["predicted_nodes"]-c["matched_nodes"])+(c["predicted_edges"]-c["matched_topology"])
        good=c["title_exact"]+c["fully_correct_nodes"]+c["fully_correct_edges"]
        kinds={}
        for case, result in s["cases"].items():
            for item in result["errors"]:
                kinds[item["kind"]]=kinds.get(item["kind"],0)+1
                ledger.append(dict(approach=name,case=case,**item))
        rows.append(dict(approach=label, mode="Graph", source_items=total, errors=total-good+extras, error_rate=pct(total-good+extras,total),
                         exact_text=None, extra_text=None, title_errors=len(mapping)-c["title_exact"], node_label_errors=c["truth_nodes"]-c["exact_node_labels"],
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
    # The three rail images share one graph. Keep this paired comparison separate.
    route_names={"junaliikenteen_ohjaus":"straight","rail_curved":"curved","rail_elbow":"right_angle"}
    paired=[]
    ocr_by_label={label:ocr[name] for name,label in [("rapid_v6_medium_fi","RapidOCR PP-OCRv6 Finnish"),("paddle_v5_fi","PaddleOCR PP-OCRv5 Finnish"),("legacy_rapid_v3","Older RapidOCR baseline")]}
    for row in rows:
        for slug,route in route_names.items():
            if row["mode"]=="OCR text":
                result=ocr_by_label[row["approach"]]["cases"][slug]["all"]
                paired.append({"approach":row["approach"],"route":route,"mode":"OCR text",
                               "source_items":result["total"],"events":result["total"]-result["exact"]+result["extra_ocr_items"],
                               "exact_text":result["exact"],"extra_text":result["extra_ocr_items"],
                               "topology":None,"complete_edges":None,"wrong_arrows":None,"shape_mismatches":None})
            else:
                case=next(case for case,name in mapping.items() if name==slug)
                approach=next(name for name,label in graph_names if label==row["approach"])
                result=read(ROOT/approach/"scores.json")["cases"][case]
                c=result["counts"]
                items=1+c["truth_nodes"]+c["truth_edges"]
                extras=(c["predicted_nodes"]-c["matched_nodes"])+(c["predicted_edges"]-c["matched_topology"])
                events=items-c["title_exact"]-c["fully_correct_nodes"]-c["fully_correct_edges"]+extras
                paired.append({"approach":row["approach"],"route":route,"mode":"Graph",
                               "source_items":items,"events":events,"exact_text":None,"extra_text":None,
                               "topology":c["matched_topology"],"complete_edges":c["fully_correct_edges"],
                               "wrong_arrows":c["wrong_arrows"],"shape_mismatches":sum(e["kind"]=="wrong_node_shape" for e in result["errors"])})
    with (ROOT/"paired_results.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(paired[0]));w.writeheader();w.writerows(paired)
    (ROOT/"paired_results.json").write_text(json.dumps(paired,ensure_ascii=False,indent=2),encoding="utf-8")
    audit=dict(case_count=len(mapping), source_items=total, clipped_text=sum(v["clipped_text_count"] for v in qa.values()),
               overlapping_text=sum(v["overlapping_text_count"] for v in qa.values()),
               hidden_edges=sum(v["hidden_by_nonendpoint_nodes"] for v in edge_qa.values()),
               coincident_edge_pairs=sum(v["coincident_edge_pairs"] for v in edge_qa.values()),
               minimum_text_contrast=min(v["minimum_text_contrast"] for v in qa.values()),
               blind_inputs_scored_after_predictions_saved=True,
               blind_access_logs=["blind_vision/access_log.txt","blind_fusion/access_log.txt"],
               blinding="procedural; agent file access was self-reported, not independently enforced")
    (ROOT/"validation.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")
    lines=["# Twelve-diagram benchmark with routed arrows","",
           f"Twelve Finnish-context diagram images contain {sum(len(read(ROOT/f'{s}.source.json')['nodes']) for s in mapping.values())} node instances and {sum(len(read(ROOT/f'{s}.source.json')['edges']) for s in mapping.values())} edge instances. The straight, curved, and right-angle rail cases share graph labels and topology. Exact route coordinates live in source JSON; Mermaid encodes topology.","",
           f"Source QA: {audit['clipped_text']} clipped text regions; {audit['overlapping_text']} overlapping text regions; {audit['hidden_edges']} edges hidden by a non-endpoint node; {audit['coincident_edge_pairs']} coincident edge pairs. Minimum text contrast {audit['minimum_text_contrast']:.2f}:1. The two routed images were inspected visually and passed 24 sampled route-to-node checks.","",
           "## Approach matrix","",
           f"| Approach | Task | Total scorer events / {total} | Exact figures | Title | Node text | Edge text | Shape | Arrow | Extra text |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        fmt=lambda v: "—" if v is None else str(v)
        arrows=None if r["wrong_arrows"] is None else r["wrong_arrows"]+r["unresolved_directed_arrows"]
        lines.append(f"| {r['approach']} | {r['mode']} | {r['errors']}/{total} ({r['error_rate']:.1f}%) | {r['perfect_figures']}/{len(mapping)} | {r['title_errors']} | {r['node_label_errors']} | {r['edge_label_errors']} | {fmt(r['shape_mismatches'])} | {fmt(arrows)} | {fmt(r['extra_text'])} |")
    lines += ["", f"OCR rows score exact printed text at source locations plus unmatched OCR boxes. Graph rows score titles, nodes (label and shape), and complete visible edges (endpoints, printed relationship, arrowhead, stroke). All rows use {total} source items, but OCR and graph rows measure different tasks. Precision/recall in the CSV is correct reported items / all reported items and correct source items / all source items. A total rate can exceed 100% when there are many extras.","",
              "An arrowless link predicted with unknown semantic direction is accepted as visually faithful and logged separately. The independent fusion run saw images and RapidOCR PP-OCRv6 medium Finnish observations.","",
              "## Paired rail-route comparison","",
              "| Approach | Straight events / 21 | Curved events / 21 | Right-angle events / 21 |",
              "|---|---:|---:|---:|"]
    for row in rows:
        vals=[next(x["events"] for x in paired if x["approach"]==row["approach"] and x["route"]==route) for route in ("straight","curved","right_angle")]
        lines.append(f"| {row['approach']} | {vals[0]} | {vals[1]} | {vals[2]} |")
    lines += ["", "The three rail images share one topology, so 12 images are not 12 independent graph samples. The straight figure uses oval nodes while the routed variants use pill nodes; line and label placement also differ. This is a paired topology comparison, not an isolated route-shape test. One paired set and independently prompted vision/fusion agents cannot establish a general curve penalty or OCR causal gain.","",
              "## Reproducibility and limits","",
              "Fresh blind agents received anonymous images only, or images plus raw RapidOCR, and saved all predictions before scoring. Their access logs are self-reports; filesystem access was not sealed. The diagrams are clean and synthetic. Relationship scoring checks what is printed, not real-world semantic truth. Source JSON, Mermaid, PNGs, OCR observations, predictions, matrix CSV, paired CSV, and item-level ledger are retained separately."]
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
    page=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Graph extraction benchmark</title><style>body{{font:16px system-ui;background:#f5f7fa;color:#172d3c;margin:20px}}main{{max-width:1850px;margin:auto}}section{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:12px}}figure{{margin:0;background:white;border:1px solid #bdcbd3;padding:8px}}img{{width:100%;height:auto;display:block}}figcaption{{font-weight:bold}}details{{background:white;border:1px solid #bdcbd3;margin:10px 0;padding:10px}}summary{{cursor:pointer;font-weight:bold}}table{{border-collapse:collapse;background:white;width:100%}}td,th{{padding:8px;border:1px solid #ccd7df;text-align:left}}th{{background:#e8f0f6}}.scroll{{overflow-x:auto}}@media(max-width:900px){{section{{grid-template-columns:1fr}}}}</style><main><h1>Graph extraction benchmark</h1><p>Twelve Finnish-context figures, including straight, curved, and right-angle routes for one paired rail graph. Open any case to compare its three images.</p>{''.join(case_sections)}<h2>Approach matrix</h2><div class="scroll"><table><thead><tr><th>Approach</th><th>Task</th><th>Scorer events / {total}</th><th>Exact figures</th><th>Node text errors</th><th>Edge text errors</th><th>Shape mismatches</th><th>Arrow errors</th></tr></thead><tbody>'''
    for r in rows:
        values=[r["approach"],r["mode"],f"{r['errors']}/{total} ({r['error_rate']:.1f}%)",f"{r['perfect_figures']}/{len(mapping)}",r["node_label_errors"],r["edge_label_errors"],r["shape_mismatches"] if r["shape_mismatches"] is not None else "—",(r["wrong_arrows"]+r["unresolved_directed_arrows"]) if r["wrong_arrows"] is not None else "—"]
        page+="<tr>"+"".join(f"<td>{html.escape(str(v))}</td>" for v in values)+"</tr>"
    page+='''</tbody></table></div><p>OCR text and graph rows use different scoring rules. Shape mismatches are strict visual taxonomy differences. <a href="REPORT.md">Validation report</a> · <a href="approach_matrix.csv">CSV</a> · <a href="paired_results.csv">Paired route results</a> · <a href="item_error_ledger.json">Error ledger</a></p></main></html>'''
    (ROOT/"results_viewer.html").write_text(page,encoding="utf-8")
    print("Wrote",len(rows),"matrix rows;",len(ledger),"ledger records; source items",total)


if __name__ == "__main__":
    main()
