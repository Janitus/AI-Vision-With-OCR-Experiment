# Ten-graph benchmark results

Synthetic Finnish-context graphs; 60 nodes and 70 source edges. All scores are exact except box matching (IoU ≥ 0.5).

| Approach | Cases | Exact node labels | All visible text | Connections | Arrow direction | Edge labels | Fully correct edges |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rapidocr_full | 10 | 81.7% | 55.7% | 0.0% | — | — | 0.0% |
| rapidocr_crops | 10 | 83.3% | 35.7% | 0.0% | — | — | 0.0% |
| codex_vision | 10 | 100.0% | 85.0% | 84.3% | 85.0% | 75.3% | 54.3% |
| codex_plus_rapidocr | 10 | 100.0% | 85.0% | 84.3% | 85.0% | 75.3% | 54.3% |

Blank cells mean a metric has no denominator, never zero.
The two OCR approaches locate colored boxes and read text but do not reconstruct edges.
Those OCR rows use legacy rapidocr_onnxruntime 1.2.3 with bundled ch_PP-OCRv3 models, not a Finnish OCR configuration.
Codex visual review was performed on the rendered images; the fixture generator was authored in the same session, so it is not a blind independent model evaluation.
The exact Codex model identifier was not recorded, so that row is an unversioned visual review.
The OCR-plus-Codex row keeps vision text unless OCR independently agrees. Its accuracy matches the vision row here; OCR primarily adds disagreement flags.
Source graphs are synthetic tests in Finnish contexts, not factual diagrams of Finnish institutions or services.
Some lines and labels overlap in the rendered images. Source-data scoring counts them even where they are hard to see.

## Error counts by approach

| Approach | Error type | Count |
| --- | --- | ---: |
| rapidocr_full | extra_or_wrong_visible_text | 39 |
| rapidocr_full | missing_edge | 70 |
| rapidocr_full | missing_visible_text | 54 |
| rapidocr_full | wrong_node_text | 11 |
| rapidocr_full | wrong_node_type | 60 |
| rapidocr_crops | extra_or_wrong_visible_text | 10 |
| rapidocr_crops | missing_edge | 70 |
| rapidocr_crops | missing_visible_text | 70 |
| rapidocr_crops | wrong_node_text | 10 |
| rapidocr_crops | wrong_node_type | 60 |
| codex_vision | extra_edge | 10 |
| codex_vision | extra_or_wrong_visible_text | 9 |
| codex_vision | missing_edge | 11 |
| codex_vision | missing_visible_text | 19 |
| codex_vision | wrong_arrow | 9 |
| codex_vision | wrong_relationship | 14 |
| codex_plus_rapidocr | extra_edge | 10 |
| codex_plus_rapidocr | extra_or_wrong_visible_text | 9 |
| codex_plus_rapidocr | missing_edge | 11 |
| codex_plus_rapidocr | missing_visible_text | 19 |
| codex_plus_rapidocr | wrong_arrow | 9 |
| codex_plus_rapidocr | wrong_relationship | 14 |

See `results/matrix.csv` for every graph × metric and `runs/<approach>/<case>.errors.json` for every mismatch.
