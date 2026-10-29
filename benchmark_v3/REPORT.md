# Benchmark v3 validation report

Ten new Finnish-context figures contain 83 nodes and 113 edges (v2: 49 nodes, 41 edges). Mermaid source, structured truth, rendered images, raw OCR, and blind predictions are retained separately.

## Source image QA

Automated text checks: 0 clipped labels, 0 overlapping text regions; minimum text/background contrast 7.49:1. All ten PNGs were inspected with `view_image`. Text-only nodes have a background patch that keeps lines from crossing letters. Shape boundaries and every printed label are fully visible. The diagrams are synthetic Finnish-context examples, not verified real-world organizational facts.

## Approach matrix

**P/R means precision/recall.** Precision asks: of the nodes or connections the method reported, what fraction matched the source? Recall asks: of the source nodes or connections, what fraction did it find? Connection matching checks endpoints; arrow, label, and stroke are scored separately. For example, vision-only edge P/R of 96.3%/92.9% means 105 of 109 reported connections and 105 of 113 source connections matched.

**Total errors per source item** uses the same fixed denominator for all approaches: 206 source items (10 titles, 83 nodes, 113 edges). The numerator is wrong or missing source items plus extra reported outputs. For OCR, those items mean printed text regions only. The OCR engine may also return unmatched text boxes; those are extra outputs, not extra source items. For vision, an item is a title, a node with the correct label and shape, or an edge with the correct endpoints, arrow, label, and dashed state. Extra outputs are counted separately in the detail tables. This is an error-event rate, so it could exceed 100% if a method emitted many extras. The denominator is numerically equal across modalities, but the checks differ. **RapidOCR's text-only rate cannot rank it above vision on graph extraction**, because OCR alone does not reconstruct connections or arrow directions. Compare totals within each modality.

Other rates are errors divided by expected items; lower is better. `—` means the approach does not produce that output. OCR text scores use location-matched visible text regions, including rotated edge labels. Graph scores use coordinate-matched nodes (155 px tolerance). Missing edges count as errors in each edge error rate.

| Approach | Scored unit | Errors / 206 source items |
|---|---|---:|
| legacy_rapid_v3 | OCR text | 61/206 (29.6%) |
| paddle_v5_fi | OCR text | 59/206 (28.6%) |
| rapid_v6_medium_fi | OCR text | 18/206 (8.7%) |
| blind_vision | Graph | 26/206 (12.6%) |
| blind_fusion | Graph | 34/206 (16.5%) |

### OCR text errors

| Approach | Title | Node labels | Edge labels | Unmatched OCR boxes |
|---|---:|---:|---:|---:|
| legacy_rapid_v3 | 70.0% | 20.5% | 32.7% | 0 |
| paddle_v5_fi | 0.0% | 0.0% | 16.8% | 40 |
| rapid_v6_medium_fi | 0.0% | 1.2% | 1.8% | 15 |

### Graph detection

| Approach | Node P/R | Connection P/R | Extra nodes | Extra edges |
|---|---:|---:|---:|---:|
| blind_vision | 100.0%/100.0% | 96.3%/92.9% | 0 | 4 |
| blind_fusion | 100.0%/100.0% | 95.5%/94.7% | 0 | 5 |

### Graph error types

| Error type | Vision only | Vision + OCR |
|---|---:|---:|
| Title text | 0.0% | 0.0% |
| Node label | 0.0% | 0.0% |
| Edge label | 8.8% | 7.1% |
| Arrow direction | 8.8% | 14.2% |
| Dashed/solid stroke | 7.1% | 7.1% |
| Node shape | 12.0% | 12.0% |
| Fully correct edge | 10.6% | 16.8% |
| Unknown directions (count) | 0 | 10 |

Other per-type rates and counts, including relationship, dashed stroke, unknown directions and relationships, all visible text, and false positives, are in [approach_matrix.csv](approach_matrix.csv). Every mismatch and extra item is in [item_error_ledger.json](item_error_ledger.json). Self-reported ambiguities and OCR/vision conflicts are in [uncertainties.json](uncertainties.json). An unmatched OCR box is a text detection that could not be assigned to one of the 206 printed regions; it may be a false detection or a misplaced fragment of real text.

## Observed result

RapidOCR PP-OCRv6 was strongest on literal text here: 203/206 exact visible regions, versus PaddleOCR's 187/206 and the old baseline's 145/206. Both Codex sessions found all 83 nodes and read their labels exactly. Vision-only recovered 105/113 connections and 101/113 fully correct edges; fusion recovered 107/113 connections but 94/113 fully correct edges. Fusion marked ten directions `unknown`, often on links with no visible arrowhead, while vision-only used `undirected` for those links. The sessions also differed on the two opposite edges in case 10. OCR assistance coincided with two more found connections, while the fully correct edge count fell by seven. These separate sessions cannot isolate OCR as the cause of either difference.

A scoring correction maps the fusion output's `plain` node shape to the source's `text` (unboxed) shape. Both vision runs therefore have 73/83 correct node shapes. Earlier fusion shape and total error figures that treated `plain` as a distinct shape were inflated; the current matrix and ledger supersede them.

## Blind evaluation protocol

The two fresh Codex tasks received anonymous case images. Blind fusion also received the ten raw outputs from **RapidOCR 3.10, PP-OCRv6 medium, configured for Finnish detection and recognition**. Codex visually compared those OCR strings and polygons with each image and wrote its own graph prediction; there was no automated text-merging algorithm. PaddleOCR and the older OCR baseline were scored separately; neither fed blind fusion. Neither prompt provided source Mermaid, truth JSON, prior results, or case mapping. Predictions were written before this scoring step. The task logs were audited for file/tool access; this is a procedural blind test, not filesystem isolation. See `session_audit.json`.

## Interpretation and limits

The source PNGs were drawn by the Python renderer from the same structured graphs exported as Mermaid; the Mermaid text is a reproducible graph definition, not the exact pixel renderer. OCR-only rows measure text recognition and do not claim graph reconstruction. Vision rows measure one session each, so differences between them cannot establish a general causal gain from OCR. The figures are clean synthetic diagrams; performance on scanned academic pages or production diagrams may be lower. Edge text accuracy is literal exact match, and connection matching uses endpoint proximity, not semantic equivalence.

Open [matrix_viewer.html](matrix_viewer.html) for a readable matrix, or [results_viewer.html](results_viewer.html) for source, vision-only, and fusion figures side by side.
