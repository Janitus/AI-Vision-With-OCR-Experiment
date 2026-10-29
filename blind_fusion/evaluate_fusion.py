"""Score the independent OCR+vision predictions against the same ten fixtures."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"blind_vision"))
from evaluate_blind import compare, fraction


def load(path):return json.loads(path.read_text(encoding="utf-8"))


def main():
    sources=sorted(p.name.removesuffix(".source.json") for p in (ROOT.parent/"benchmark_v2").glob("*.source.json"))
    cases={}
    for i,slug in enumerate(sources,1):
        name=f"case_{i:02}";path=ROOT/"predictions"/(name+".json")
        if not path.exists():raise SystemExit(f"Missing {path}")
        pred=load(path)
        cases[name]=compare(slug,pred)
        cases[name]["ocr_disagreements"]=pred.get("ocr_disagreements",[])
    counts={k:sum(r["counts"][k] for r in cases.values()) for k in next(iter(cases.values()))["counts"]}
    rates={
        "title_error_rate":fraction(10-counts["title_exact"],10),
        "node_detection_error_rate":fraction(counts["truth_nodes"]-counts["matched_nodes"],counts["truth_nodes"]),
        "node_label_error_rate":fraction(counts["truth_nodes"]-counts["exact_node_labels"],counts["truth_nodes"]),
        "node_shape_error_rate":fraction(counts["truth_nodes"]-counts["exact_node_shapes"],counts["truth_nodes"]),
        "topology_error_rate":fraction(counts["truth_edges"]-counts["matched_topology"],counts["truth_edges"]),
        "arrow_error_rate":fraction(counts["truth_edges"]-counts["correct_arrows"],counts["truth_edges"]),
        "relationship_error_rate":fraction(counts["truth_edges"]-counts["correct_relationships"],counts["truth_edges"]),
        "stroke_error_rate":fraction(counts["truth_edges"]-counts["correct_strokes"],counts["truth_edges"]),
        "full_edge_error_rate":fraction(counts["truth_edges"]-counts["fully_correct_edges"],counts["truth_edges"]),
    }
    previous=load(ROOT.parent/"blind_vision"/"blind_scores.json")
    comparison={key:{"vision_only":value,"ocr_plus_vision":rates[key],"change":round(rates[key]-value,4)}
                for key,value in previous["error_rates"].items() if key in rates}
    disagreements=[{"case":name,"detail":entry} for name,r in cases.items() for entry in r["ocr_disagreements"]]
    result={"provenance":"Fresh separate Codex session with only ten images and ten raw RapidOCR v6 medium Finnish observation files supplied",
            "thread_id":"01a18753-3b3f-7442-af95-820405c62360","counts":counts,"error_rates":rates,
            "comparison":comparison,"ocr_disagreements":disagreements,"cases":cases}
    (ROOT/"fusion_scores.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    with (ROOT/"vision_comparison.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.writer(f);writer.writerow(["error_type","vision_only","ocr_plus_vision","change"])
        for key,val in comparison.items():writer.writerow([key,val["vision_only"],val["ocr_plus_vision"],val["change"]])
    lines=["# Blind vision-only versus blind OCR + vision", "",
        "Two separate fresh Codex sessions processed the same ten anonymous images. The fusion session also received raw RapidOCR PP-OCRv6 medium Finnish observations (text, confidence, coordinates), without ground truth. Both sessions saved predictions before this comparison. The fusion session's recorded tool calls show only its image copies, OCR files, and prediction folder; no ground-truth reads. Lower error rates are better.", "",
        "| Error type | Vision only | OCR + vision | Change |", "|---|---:|---:|---:|"]
    for key,v in comparison.items():
        lines.append(f'| {key.replace("_"," ")} | {v["vision_only"]*100:.1f}% | {v["ocr_plus_vision"]*100:.1f}% | {v["change"]*100:+.1f} pp |')
    lines += ["",f'Fusion session recorded {len(disagreements)} OCR disagreements or rejected OCR detections.', "", "## Per-case errors", ""]
    for name,r in cases.items():
        lines.append(f"### {name}");lines.append("")
        if not r["errors"]:lines.append("No scored errors.")
        else:
            for error in r["errors"]:lines.append("- "+json.dumps(error,ensure_ascii=False))
        if r["uncertainties"]:lines.append("- Uncertainties: "+json.dumps(r["uncertainties"],ensure_ascii=False))
        if r["ocr_disagreements"]:lines.append("- OCR disagreements: "+json.dumps(r["ocr_disagreements"],ensure_ascii=False))
        lines.append("")
    lines += ["## Interpretation", "",
        "This is an image-only versus OCR-assisted comparison on ten clean synthetic diagrams. It is procedurally blind: the fresh fusion session was told to read only the anonymized images and OCR observations. Workspace permissions did not technically prevent other file reads. OCR can corroborate printed text, but it cannot by itself establish a missing arrowhead or distinguish nearly identical rounded-box categories. The improved arrow result is a different visual judgment in a fresh session; this single comparison cannot show that OCR caused it. These ten examples are too small to estimate general error rates precisely."]
    (ROOT/"FUSION_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"counts":counts,"error_rates":rates,"ocr_disagreements":len(disagreements)},ensure_ascii=False,indent=2))


if __name__=="__main__":main()
