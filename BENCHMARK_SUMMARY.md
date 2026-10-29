# OCR + vision graph reconstruction: short report

## Recommendation

Use **RapidOCR PP-OCRv6 medium with Finnish selected** to collect text and coordinates, then have a **fresh Codex vision session** inspect the image and reconcile OCR observations with visible nodes, edges, and arrowheads. Keep raw OCR, the image-only vision prediction, the fused prediction, and uncertainty records separately. Reject OCR detections that are line fragments or arrowheads; mark unresolved connections as `unknown` instead of inventing them.

## Evidence from the ten-diagram test

The test set contains ten synthetic Finnish-context diagrams with varied fonts, colors, node shapes, unboxed labels, and rotated edge text. It contains 100 printed text items, 49 nodes, and 41 edges. All source text was checked for clipping and overlaps before testing.

| Method | Expected text read exactly | Extra OCR text | Fully correct edges | Node-shape errors |
|---|---:|---:|---:|---:|
| Older bundled RapidOCR | 73/100 | 0 | Not attempted | Not attempted |
| PaddleOCR PP-OCRv5 Finnish | 100/100 | 5 | Not attempted | Not attempted |
| RapidOCR PP-OCRv6 medium Finnish | 100/100 | 3 | Not attempted | Not attempted |
| Fresh Codex vision, image only | 100/100 visible items | — | 40/41 | 4/49 |
| Fresh Codex vision + RapidOCR v6 | 100/100 visible items | 3 rejected | **41/41** | 4/49 |

The image-only session left one arrow direction unresolved. The OCR-assisted session interpreted that edge as undirected, matching the source. OCR has no arrow-direction signal, so this one difference may be a different visual judgment by a separate session rather than an OCR benefit. Both sessions called four capsule-shaped nodes “rounded rectangles” rather than the source category “pill.” The OCR-assisted session rejected all three spurious OCR detections after checking the pixels.

## Practical limits

This is a small, clean, synthetic set. The two Codex runs were fresh sessions that did not receive source answers; their recorded tool calls show image-only and image-plus-OCR reads respectively. Workspace access was not technically sealed, and these figures do not estimate accuracy on dense real-world graphs. Exact font, color, and edge geometry were not scored. The relationship score checks the **printed edge label**, not whether the underlying statement is true.

For the next test, use denser layouts, crossings, branches, bidirectional and arrowless edges, small labels, rotated labels, and more varied node shapes. Keep labels fully visible, hold source data back until predictions are saved, and report missing, wrong, and extra items separately.

## Artifacts

- `benchmark_v2/VALIDATION.md`: OCR details and prior non-blind review.
- `blind_vision/BLIND_REPORT.md`: fresh image-only extraction.
- `blind_fusion/FUSION_REPORT.md`: fresh OCR-assisted comparison and errors.
- `blind_fusion/comparison_viewer.html`: source, vision-only, and fused graphs side by side.
- `blind_vision/combined_approach_matrix.csv`: one row per approach.
