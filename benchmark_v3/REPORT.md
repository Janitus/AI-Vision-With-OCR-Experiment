# Benchmark v3 validation report

Ten new Finnish-context figures contain 83 nodes and 113 edges (v2: 49 nodes, 41 edges). Mermaid source, structured truth, rendered images, raw OCR, and blind predictions are retained separately.

## Source image QA

Automated text checks: 0 clipped labels, 0 overlapping text regions; minimum text/background contrast 7.49:1. All ten PNGs were inspected with `view_image`. Text-only nodes have a background patch that keeps lines from crossing letters. Shape boundaries and every printed label are fully visible. The diagrams are synthetic Finnish-context examples, not verified real-world organizational facts.

## Approach matrix

**P/R means precision/recall.** Precision asks: of the nodes or connections the method reported, what fraction matched the source? Recall asks: of the source nodes or connections, what fraction did it find? Connection matching checks endpoints; arrow, label, and stroke are scored separately. For example, vision-only edge P/R of 96.3%/92.9% means 105 of 109 reported connections and 105 of 113 source connections matched.

**Total errors per source item** uses the same fixed denominator for all approaches: 206 source items (10 titles, 83 nodes, 113 edges). The numerator is wrong or missing source items plus extra reported outputs. OCR rows score printed text regions only; graph rows score titles, nodes with exact label and shape, and edges with exact endpoints, arrow, label, and stroke. The denominator is numerically equal, but the checks differ. Compare OCR engines with each other, then compare vision with the deterministic vision+OCR union. The rate could exceed 100% if a method emitted many extras.

Other rates are errors divided by expected items; lower is better. `—` means the approach does not produce that output. OCR text scores use location-matched visible text regions, including rotated edge labels. Graph scores use coordinate-matched nodes (155 px tolerance). Missing edges count as errors in each edge error rate.

| Approach | Scored unit | Errors / 206 source items | Error-free figures / 10 |
|---|---|---:|---:|
| rapid_v6_medium_fi | OCR text | 18/206 (8.7%) | 4/10 |
| paddle_v5_fi | OCR text | 59/206 (28.6%) | 0/10 |
| legacy_rapid_v3 | OCR text | 61/206 (29.6%) | 0/10 |
| blind_vision | Graph | 26/206 (12.6%) | 4/10 |
| vision_ocr_union | Graph | 26/206 (12.6%) | 4/10 |

### OCR text errors

| Approach | Title | Node labels | Edge labels | Unmatched OCR boxes |
|---|---:|---:|---:|---:|
| rapid_v6_medium_fi | 0.0% | 1.2% | 1.8% | 15 |
| paddle_v5_fi | 0.0% | 0.0% | 16.8% | 40 |
| legacy_rapid_v3 | 70.0% | 20.5% | 32.7% | 0 |

### Graph detection

| Approach | Node P/R | Connection P/R | Extra nodes | Extra edges |
|---|---:|---:|---:|---:|
| blind_vision | 100.0%/100.0% | 96.3%/92.9% | 0 | 4 |
| vision_ocr_union | 100.0%/100.0% | 96.3%/92.9% | 0 | 4 |

### Graph error types

| Error type | Vision only | Vision + OCR union |
|---|---:|---:|
| Title text | 0.0% | 0.0% |
| Node label | 0.0% | 0.0% |
| Edge label | 8.8% | 8.8% |
| Arrow not established (missing, wrong, or unknown) | 8.8% | 8.8% |
| Arrow visibly wrong | 1.8% | 1.8% |
| Arrow unresolved | 0.0% | 0.0% |
| Dashed/solid stroke | 7.1% | 7.1% |
| Node shape | 12.0% | 12.0% |
| Fully correct edge | 10.6% | 10.6% |
| Unknown directions (count) | 0 | 0 |

No matched connection had the wrong dashed/solid stroke: 105/105 matched connections had correct strokes. The displayed 8/113 stroke incompleteness comes entirely from eight missing source connections. Those omissions also enter the per-type arrow and label rates. The 26 non-overlapping blind-vision ledger entries are 10 wrong node shapes, 8 missing edges, 4 extra edges, 2 wrong relationship labels, and 2 wrong arrows.

An `unknown` arrow direction is logged as `unresolved_arrow`, not `wrong_arrow`. It still prevents a fully correct edge because the graph cannot be used without resolving that direction. Arrowless source links are scored against the source's visible no-arrow mark; the benchmark does not infer whether the underlying relationship is semantically undirected.

Other per-type rates and counts are in [approach_matrix.csv](approach_matrix.csv). Every mismatch and extra item is in [item_error_ledger.json](item_error_ledger.json). Self-reported ambiguities and OCR conflicts are in [uncertainties.json](uncertainties.json). An unmatched OCR box may be a false detection or a misplaced fragment of real text.

## Observed result

RapidOCR PP-OCRv6 read 203/206 visible text regions exactly; PaddleOCR read 187/206 and the old baseline 145/206. OCR-only does not reconstruct a graph. Vision-only recovered 105/113 connections and 101/113 fully correct edges, with four of ten figures entirely error-free under this rubric. The deterministic union matched 200 OCR boxes to existing vision text and retained 23 unassigned boxes across 10/10 figures. It added no nodes or edges, so its graph scores and four error-free figures match vision-only. The current union leaves those OCR boxes unresolved rather than silently discarding or promoting them. These results do not support fully automated, review-free reconstruction of every tested diagram.

For the earlier independent joint Codex run, `plain` and `text` are both treated as unboxed shapes. Its `unknown` arrows are recorded as unresolved rather than visibly wrong; they still make those edges incomplete. That historical run is retained as a separate record and is not pooled with the deterministic union.

## Blind evaluation protocol

A fresh Codex task received anonymous images and saved its vision predictions before scoring. The deterministic union then read those saved predictions and **RapidOCR 3.10 PP-OCRv6 medium Finnish** observations. It assigns an exact-text OCR box to at most one vision element, retains unmatched OCR boxes, and never promotes OCR alone into a node or edge. The union script does not read source JSON. An earlier separate Codex task also read images plus raw OCR and produced a joint prediction; its historical result remains in [blind_fusion/scores.json](blind_fusion/scores.json), but it is not the deterministic union row. Task logs were audited for file access; blinding was procedural, not filesystem-enforced. See [session_audit.json](session_audit.json).

## Interpretation and limits

The source PNGs were drawn by the Python renderer from the same structured graphs exported as Mermaid; the Mermaid text is a graph definition, not the pixel renderer. These ten clean, synthetic figures cover several styles but do not represent the full variety of diagrams. The union deliberately preserves vision topology, so its identical graph score is expected; it tests traceable evidence merging, not a new edge detector. The OCR scorer uses spatial text matching and the graph scorer uses coordinate proximity, both of which can affect individual results. An error-free figure here means no scored error, not a guarantee about unscored semantics or future figures.

Open [matrix_viewer.html](matrix_viewer.html) for a readable matrix, or [results_viewer.html](results_viewer.html) for source, vision-only, and evidence-union figures side by side.
