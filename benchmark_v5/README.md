# Routed-arrow benchmark (v5)

This complete rerun contains all ten corrected v4 diagrams plus the curved and right-angle versions of the rail diagram. The straight rail diagram is already one of the ten v4 cases. The three rail figures have the same eight nodes and twelve edges; they are paired renderings of one graph, not independent examples.

Each of the twelve cases has a PNG, Mermaid graph definition, and structured source JSON. Exact cubic and polyline route coordinates are kept in the two routed source JSON files. Mermaid preserves only the graph connections. `build_sources.py` assembles the sources and text QA from v4 and `route_fixtures`; `route_fixtures/route_qa.json` records the geometric checks for the two new images.

## Reproduce the scores

Run these commands from the repository root with the same cached OCR installations/models used in v4:

```powershell
python benchmark_v5/build_sources.py
python benchmark_v5/run_rapid.py
python benchmark_v5/run_paddle.py
python benchmark_v5/run_legacy.py
python benchmark_v5/score_ocr.py
python benchmark_v5/evaluate_blind.py blind_vision
python benchmark_v5/evaluate_blind.py blind_fusion
python benchmark_v5/summarize.py
python benchmark_v5/build_pdf.py
```

The blind predictions were saved before scoring. To repeat the blind stage, create anonymous inputs with `python benchmark_v5/prepare_blind_inputs.py`, give one fresh agent only the images and another the images plus raw RapidOCR observations, and freeze all predictions before invoking the scorer. Duplicate anonymous inputs are ignored by Git. Blinding is procedural, not enforced by filesystem isolation; see the access logs.

The fixed source-item denominator is 240: twelve titles, 99 nodes, and 129 edges. OCR rows measure printed text; graph rows measure reconstructed graph elements. `paired_results.csv` isolates straight, curved, and right-angle rail results. `approach_matrix.csv`, `item_error_ledger.json`, `REPORT.md`, and `results_viewer.html` carry the detailed results. The aggregate 12-image rate should not be read as twelve independent graph topologies.

The saved `vision_ocr_union/` files preserve a deterministic attachment of OCR text boxes to the blind-vision graph. They are excluded from comparison tables because they do not change the graph prediction.
