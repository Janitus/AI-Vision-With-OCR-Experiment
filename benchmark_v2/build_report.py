"""Write the validation report from raw OCR results and strict score files."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding="utf-8"))


def main():
    matrix=read(ROOT/"approach_matrix.json")
    ocr=read(ROOT/"ocr_matrix.json")
    vision=read(ROOT/"vision_scores.json")
    names={x["id"]:x["title"] for x in read(ROOT/"manifest.json")}
    lines=["# Validation report: ten Finnish graph fixtures", "",
        "## Scope and method", "",
        "Ten 1400×850 synthetic PNGs were reviewed for clipped or overlapping text before benchmarking. All have paired Mermaid source and JSON ground truth. OCR ran on each full image. The scorer assigns recognized polygons to known printed text regions by location, then requires exact Unicode text; case and Finnish diacritics matter. This spatial assignment is evaluation only, so its node and edge categories do not mean an OCR engine inferred graph structure.", "",
        "The graph review was made by Codex from the images in the same conversation that created the fixtures. It is **non-blind** and must not be interpreted as an independent model accuracy estimate. No API keys or remote vision API were used. OCR models were downloaded once and run locally.", "",
        "## Aggregate matrix", "",
        "| Approach | Exact text recall | Exact text precision | Exact node labels | Exact edge labels | Rotated labels | Connections | Correct arrows | Fully correct edges | Shape / stroke |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in matrix:
        def pct(v):return "—" if v is None else f"{v*100:.1f}%"
        edges=f'{row["connections_found"]}/{row["connections_total"]}'
        shape=f'{pct(row["node_shape_accuracy"])} / {pct(row["edge_stroke_accuracy"])}'
        lines.append(f'| {row["approach"]} | {pct(row["all_visible_text_exact"])} | {pct(row["all_visible_text_precision"])} | {pct(row["node_labels_exact"])} | {pct(row["edge_labels_exact"])} | {pct(row["rotated_edge_labels_exact"])} | {edges} | {pct(row["arrow_accuracy"])} | {row["fully_correct_edges"]}/{row["connections_total"]} | {shape} |')
    lines += ["", "**Denominators:** 100 visible text items (10 titles, 49 node labels, 41 edge labels); 10 rotated edge labels; 49 nodes; 41 edges. Exact text precision counts false OCR items. A fully correct edge requires the two endpoints, arrow direction, and the printed relationship label all to match. Shape and dashed-stroke accuracy are scored on the non-blind visual reading. OCR-only rows do not attempt graph reconstruction, so their zero connection count is a capability boundary rather than a failed arrow detector.", "",
        "## Per-diagram exact text", "",
        "| Diagram | Printed items | Legacy Rapid | Paddle v5 Finnish | Rapid v6 medium Finnish |", "|---|---:|---:|---:|---:|"]
    lookup={r["approach"]:r["cases"] for r in ocr}
    for slug in names:
        total=lookup["rapid_v6_medium_fi"][slug]["all"]["total"]
        counts=[lookup[name][slug]["all"]["exact"] for name in ("legacy_rapid_v3","paddle_v5_fi","rapid_v6_medium_fi")]
        lines.append(f'| {names[slug]} | {total} | {counts[0]}/{total} | {counts[1]}/{total} | {counts[2]}/{total} |')
    lines += ["", "## Disagreements and potential extraction errors", ""]
    for approach in ("legacy_rapid_v3","paddle_v5_fi","rapid_v6_medium_fi"):
        problems=[];extras=[]
        for slug in names:
            report=read(ROOT/"reports"/(approach+"_"+slug+".json"))
            for d in report["details"]:
                if not d["exact"]:problems.append((slug,d))
            for o in report["unmatched_ocr"]:
                if o["text"].strip():extras.append((slug,o))
        lines.append(f'### {approach}')
        lines.append("")
        lines.append(f'{len(problems)} expected text items incorrect or missing; {len(extras)} extra OCR items. Full polygon coordinates, scores, and expected/observed strings are in `runs/` and `reports/`.')
        lines.append("")
        if problems:
            for slug,d in problems:
                lines.append(f'- {names[slug]} · {d["kind"]} {d["id"]}: expected `{d["expected"]}`; observed `{d["observed"] or "∅"}`.')
        if extras:
            for slug,o in extras:
                lines.append(f'- {names[slug]} · extra OCR `{o["text"]}` at {o["bbox"]}.')
        if not problems and not extras:lines.append('- None found on this set.')
        lines.append("")
    graph_errors=[(slug,e) for slug,r in vision.items() for e in r["errors"]]
    fusion_uncertainties=[(slug,u) for slug in names for u in read(ROOT/"inferred"/(slug+".json"))["uncertainties"]]
    lines += ["### Graph review and fusion", "",
        f'{len(graph_errors)} source-versus-visual-review node, edge, arrow, relationship, shape, or stroke errors. {sum(u["kind"]=="ocr_vision_disagreement" for _,u in fusion_uncertainties)} OCR/vision disagreements on assigned graph elements. {sum(u["kind"]=="unassigned_ocr_text" for _,u in fusion_uncertainties)} unassigned OCR items; these are retained in the extracted JSON rather than turned into nodes.', ""]
    for slug,u in fusion_uncertainties:
        lines.append(f'- {names[slug]} · {u["kind"]}: `{u.get("text",u.get("vision",""))}` at {u.get("bbox",u.get("location"))}.')
    lines += ["", "## Interpretation and limits", "",
        "On this clean set, PaddleOCR PP-OCRv5 Finnish and RapidOCR PP-OCRv6 medium Finnish tie at 100/100 exact expected text items. RapidOCR has fewer false positives (3 versus 5), so it is the better observed choice for these images. This does **not** establish a generally best Finnish OCR engine. The fixtures are large, high contrast, and mostly simple chains; the visual review is non-blind. A valid independent vision benchmark needs unseen diagrams and a separately run model. Color, font family, exact edge geometry, and real-world semantic truth are not scored here. The printed relationship string is scored literally; no hidden semantics are inferred.", "",
        "The original Finnish legislation image is outside this ten-fixture score set. Its smaller labels and crossed edges should be used as a separate stress test before making reliability claims.", ""]
    (ROOT/"VALIDATION.md").write_text("\n".join(lines),encoding="utf-8")
    print("Wrote VALIDATION.md with",len(lines),"lines")


if __name__=="__main__":main()
