# Benchmark v3 validation report

Ten new Finnish-context figures contain 83 nodes and 113 edges (v2: 49 nodes, 41 edges). Mermaid source, structured truth, rendered images, raw OCR, and blind predictions are retained separately.

## Source image QA

Automated text checks: 0 clipped labels, 0 overlapping text regions; minimum text/background contrast 7.49:1. All ten PNGs were inspected with `view_image`. Text-only nodes have a background patch that keeps lines from crossing letters. Shape boundaries and every printed label are fully visible. The diagrams are synthetic Finnish-context examples, not verified real-world organizational facts.

## Approach matrix

**P/R means precision/recall.** Precision asks: of the nodes or connections the method reported, what fraction matched the source? Recall asks: of the source nodes or connections, what fraction did it find? Connection matching checks endpoints; arrow, label, and stroke are scored separately. For example, vision-only edge P/R of 96.3%/92.9% means 105 of 109 reported connections and 105 of 113 source connections matched.

**Total error** counts wrong or missing source items plus extra reported items, divided by source items plus extra items. For OCR, an item is one printed text region (title, node label, or edge label). For vision, an item is a title, a node with the correct label and shape, or an edge with the correct endpoints, arrow, label, and dashed state. Extra items raise the error count and denominator. The OCR and vision totals cover different outputs, so compare within each modality; the per-type columns show why a row failed.

Other rates are errors divided by expected items; lower is better. `—` means the approach does not produce that output. OCR text scores use location-matched visible text regions, including rotated edge labels. Graph scores use coordinate-matched nodes (155 px tolerance). Missing edges count as errors in each edge error rate.

| Approach | Total error | Title text error | Node text error | Edge text error | Node P/R | Edge P/R | Arrow error | Shape error | Full edge error | False positives |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| legacy_rapid_v3 | 61/206 (29.6%) | 70.0% | 20.5% | 32.7% | —/— | —/— | — | — | — | 0 text |
| paddle_v5_fi | 59/246 (24.0%) | 0.0% | 0.0% | 16.8% | —/— | —/— | — | — | — | 40 text |
| rapid_v6_medium_fi | 18/221 (8.1%) | 0.0% | 1.2% | 1.8% | —/— | —/— | — | — | — | 15 text |
| blind_vision | 26/210 (12.4%) | 0.0% | 0.0% | 8.8% | 100.0%/100.0% | 96.3%/92.9% | 8.8% | 12.0% | 10.6% | 0 nodes, 4 edges |
| blind_fusion | 54/211 (25.6%) | 0.0% | 0.0% | 7.1% | 100.0%/100.0% | 95.5%/94.7% | 14.2% | 36.1% | 16.8% | 0 nodes, 5 edges |

Other per-type rates and counts, including relationship, dashed stroke, unknowns, all visible text, and false positives, are in [approach_matrix.csv](approach_matrix.csv). Every mismatch and extra item is in [item_error_ledger.json](item_error_ledger.json). Self-reported ambiguities and OCR/vision conflicts are in [uncertainties.json](uncertainties.json). Unmatched OCR snippets are potential false positives under this spatial matcher; some could be misplaced fragments of real text.

## Observed result

RapidOCR PP-OCRv6 was strongest on literal text here: 203/206 exact visible regions, versus PaddleOCR's 187/206 and the old baseline's 145/206. Both Codex sessions found all 83 nodes and read their labels exactly. Vision-only recovered 105/113 connections and 101/113 fully correct edges; fusion recovered 107/113 connections but 94/113 fully correct edges. OCR assistance coincided with two more found connections, while the fully correct edge count fell by seven. These separate sessions cannot isolate OCR as the cause of either difference.

## Blind evaluation protocol

The two fresh Codex tasks received anonymous case images. Blind fusion also received the ten raw outputs from **RapidOCR 3.10, PP-OCRv6 medium, configured for Finnish detection and recognition**. Codex visually compared those OCR strings and polygons with each image and wrote its own graph prediction; there was no automated text-merging algorithm. PaddleOCR and the older OCR baseline were scored separately; neither fed blind fusion. Neither prompt provided source Mermaid, truth JSON, prior results, or case mapping. Predictions were written before this scoring step. The task logs were audited for file/tool access; this is a procedural blind test, not filesystem isolation. See `session_audit.json`.

## Interpretation and limits

The source PNGs were drawn by the Python renderer from the same structured graphs exported as Mermaid; the Mermaid text is a reproducible graph definition, not the exact pixel renderer. OCR-only rows measure text recognition and do not claim graph reconstruction. Vision rows measure one session each, so differences between them cannot establish a general causal gain from OCR. The figures are clean synthetic diagrams; performance on scanned academic pages or production diagrams may be lower. Edge text accuracy is literal exact match, and connection matching uses endpoint proximity, not semantic equivalence.

Open [results_viewer.html](results_viewer.html) for source, vision-only, and fusion figures side by side.
