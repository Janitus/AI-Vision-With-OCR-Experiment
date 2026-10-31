"""Update the short public note from measured v5 results."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
rows=json.loads((HERE/"approach_matrix.json").read_text(encoding="utf-8"))
paired=json.loads((HERE/"paired_results.json").read_text(encoding="utf-8"))
audit=json.loads((HERE/"validation.json").read_text(encoding="utf-8"))
sources=[json.loads(p.read_text(encoding="utf-8")) for p in HERE.glob("*.source.json")]
truth_nodes=sum(len(s["nodes"]) for s in sources)
truth_edges=sum(len(s["edges"]) for s in sources)

def fmt(value):return "—" if value is None else str(value)

lines=["# What happened in our graph-reading test?","",
       "**One-file version:** [Download the illustrated PDF](finnish_diagram_extraction_findings.pdf). These are informal experiment notes, not a research paper.","",
       "We tested twelve clean Finnish-context diagram images, including straight, curved, and right-angle renderings of one rail graph. The three rail images share graph content and are paired examples rather than independent graphs.","",
       f"The twelve images contain **{truth_nodes} node instances, {truth_edges} edge instances, and {audit['source_items']} printed text regions**. Source QA found {audit['clipped_text']} clipped labels, {audit['overlapping_text']} overlapping text regions, {audit['hidden_edges']} links obstructed by unrelated nodes, and {audit['coincident_edge_pairs']} coincident route pairs. The routed paths also passed their geometric checks.","",
       "## Results matrix","",
       "| Approach | Output | Scorer events / 240 | Exact figures | Main event types |",
       "|---|---|---:|---:|---|"]
for row in rows:
    if row["mode"]=="OCR text":
        detail=f"{row['title_errors']} title, {row['node_label_errors']} node, {row['edge_label_errors']} edge text errors; {row['extra_text']} unmatched boxes"
    else:
        detail=f"{row['shape_mismatches']} shape mismatches; {row['wrong_arrows']} wrong arrows; {row['wrong_strokes']} wrong strokes"
    lines.append(f"| {row['approach']} | {row['mode']} | **{row['errors']} ({row['error_rate']:.1f}%)** | {row['perfect_figures']}/12 | {detail} |")
lines += ["", "Every row uses 240 source items as the denominator (12 titles, 99 nodes, 129 edges); extra outputs add events to the numerator. OCR rows score printed text. Graph rows score nodes and complete edges. Their percentages describe different tasks and should not be ranked against each other as if they produce the same output.","",
          "## Paired route results","",
          "| Approach | Straight events / 21 | Curved events / 21 | Right-angle events / 21 |",
          "|---|---:|---:|---:|"]
for row in rows:
    values=[next(p["events"] for p in paired if p["approach"]==row["approach"] and p["route"]==route) for route in ("straight","curved","right_angle")]
    lines.append(f"| {row['approach']} | {values[0]} | {values[1]} | {values[2]} |")
lines += ["", "These are three renderings of **one** graph. The straight figure uses oval nodes while the routed figures use pill nodes; line and label placement differ too. This is a paired topology comparison, not an isolated route-shape test. It does not establish a general error rate for curved arrows or prove that OCR caused a fusion change. The prediction schema records graph connections, not the exact pixel path, so route reproduction itself is not scored.","",
          "The blind image-only run and the independent image-plus-RapidOCR run saved predictions before scoring. The fusion run saw raw RapidOCR PP-OCRv6 medium Finnish observations. A deterministic evidence union kept the image-only graph unchanged and merely attached OCR boxes, so its graph score is identical by design. Arrowless links labeled semantically unknown were counted as visually faithful, not as arrow mistakes.","",
          "| Straight baseline | Curved arrows | Right-angle detours |",
          "|---|---|---|",
          "| <img src=\"benchmark_v5/junaliikenteen_ohjaus.png\" alt=\"Straight rail graph\" width=\"300\"> | <img src=\"benchmark_v5/rail_curved.png\" alt=\"Curved rail graph\" width=\"300\"> | <img src=\"benchmark_v5/rail_elbow.png\" alt=\"Right-angle rail graph\" width=\"300\"> |","",
          "Browse the [12-case source / vision / fusion viewer](benchmark_v5/results_viewer.html), [full validation report](benchmark_v5/REPORT.md), [approach matrix](benchmark_v5/approach_matrix.csv), [paired route results](benchmark_v5/paired_results.csv), and [item-level ledger](benchmark_v5/item_error_ledger.json). This clean synthetic experiment does not test real-world semantic truth or a universal reliability rate."]
(ROOT/"FINDINGS.md").write_text("\n".join(lines)+"\n",encoding="utf-8")

readme=ROOT/"README.md"
content=readme.read_text(encoding="utf-8-sig")
old_lead="**Latest routed-arrow rerun (v5):** [findings](FINDINGS.md) · [12-case viewer](benchmark_v5/results_viewer.html) · [paired route matrix](benchmark_v5/paired_results.csv). The ten corrected v4 diagrams plus curved and right-angle rail renderings were tested with three OCR engines and fresh blind vision/fusion runs.\n\n"
lead="**Current findings:** [short report](FINDINGS.md) · [shareable PDF](finnish_diagram_extraction_findings.pdf) · [12-case viewer](benchmark_v5/results_viewer.html). Twelve Finnish-context images were tested with three OCR engines and blind vision approaches.\n\n"
content=content.replace(old_lead,lead)
if lead not in content:
    content=content.replace("# Conservative graph extraction\n\n","# Conservative graph extraction\n\n"+lead,1)
readme.write_text(content.rstrip()+"\n",encoding="utf-8")

summary=ROOT/"BENCHMARK_SUMMARY.md"
content=summary.read_text(encoding="utf-8-sig")
old_note="## Latest routed-arrow rerun (v5)\n\n[Short findings](FINDINGS.md) · [full report](benchmark_v5/REPORT.md) · [paired route results](benchmark_v5/paired_results.csv). This includes ten corrected v4 figures plus curved and right-angle versions of one rail graph. The rail trio is paired, not independent.\n\n"
note="## Current results\n\n[Short findings](FINDINGS.md) · [full report](benchmark_v5/REPORT.md) · [paired route results](benchmark_v5/paired_results.csv). The twelve images include three paired renderings of one rail graph, so those images are not independent examples.\n\n"
content=content.replace(old_note,note)
if note not in content:
    content=content.replace("# OCR + vision graph reconstruction: short report\n\n","# OCR + vision graph reconstruction: short report\n\n"+note,1)
summary.write_text(content.rstrip()+"\n",encoding="utf-8")
print("Updated FINDINGS.md, README.md, BENCHMARK_SUMMARY.md")
