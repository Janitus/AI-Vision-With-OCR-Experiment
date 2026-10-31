# Corrected ten-diagram benchmark (v4)

The earlier v3 graph rates should not be used as visible-error rates: several source links were hidden by nodes or coincident with other links. This v4 set removes eight such source edges, leaving 83 nodes and 105 edges across ten Finnish-context figures. The PDF's earlier red annotation was corrected separately.

Source QA: 0 clipped text regions; 0 overlapping text regions; 0 edges hidden by a non-endpoint node; 0 coincident edge pairs. Minimum text contrast 7.49:1. All ten images were inspected visually.

## Matrix

| Approach | Task | Total scorer events / 198 | Exact figures | Title | Node text | Edge text | Shape | Arrow | Extra text |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RapidOCR PP-OCRv6 Finnish | OCR text | 16/198 (8.1%) | 6/10 | 0 | 0 | 2 | — | — | 14 |
| PaddleOCR PP-OCRv5 Finnish | OCR text | 57/198 (28.8%) | 1/10 | 0 | 0 | 19 | — | — | 38 |
| Older RapidOCR baseline | OCR text | 60/198 (30.3%) | 0/10 | 7 | 17 | 36 | — | — | 0 |
| Blind Codex vision | Graph | 16/198 (8.1%) | 8/10 | 0 | 0 | 0 | 16 | 0 | — |
| Blind Codex + RapidOCR | Graph | 8/198 (4.0%) | 9/10 | 0 | 0 | 0 | 8 | 0 | — |
| Vision + deterministic OCR evidence | Graph | 16/198 (8.1%) | 8/10 | 0 | 0 | 0 | 16 | 0 | — |

OCR rows score exact printed title, node, and edge text at source positions, plus unmatched OCR boxes. Graph rows score exact titles, nodes (label and shape), and complete visual edges (endpoints, printed relationship, arrowheads, stroke). All rows use the same 198 source items, but OCR and graph tasks differ. The rate can exceed 100% if extra outputs are numerous.

Graph precision/recall (P/R) is in `approach_matrix.csv`. It means the fraction of reported nodes/connections that matched, and the fraction of source nodes/connections found. Shape mismatches are retained as strict taxonomy disagreements: ellipse/pill and pill/rounded rectangle in these figures. The edge scores concern visible marks, not semantic truth outside the figure.

An arrowless stroke shows no arrowhead. A prediction of `unknown` for its semantic direction is accepted as visually faithful and logged separately; it is not an arrow error. The independent OCR+vision run used RapidOCR PP-OCRv6 medium Finnish. The deterministic union only attaches OCR evidence to an existing vision graph; identical graph scores are expected.

## Error interpretation

The image-only run recovered all 105 source edge records under this scorer, and the OCR+vision run also recovered all 105 after the arrowless correction. The remaining strict graph events are shape-category disagreements. These results supersede the v3 rates and do not support a claim that vision fails on most clean synthetic diagrams. The two agents had access to crisp generated figures, ample time, and precise extraction instructions; this is not a universal accuracy estimate.

See `item_error_ledger.json` for each mismatch and `validation.json` for QA. Blind agents received anonymous images (and RapidOCR observations for fusion), saved predictions before scoring, and supplied access logs. Isolation was procedural, not filesystem-enforced. The source graphs, PNGs, Mermaid, raw OCR, predictions, and viewer are retained for review.
