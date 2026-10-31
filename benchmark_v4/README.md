# Corrected ten-diagram benchmark

This rerun replaces the v3 graph reliability claim. V3 source links sometimes passed behind non-endpoint nodes or shared the same route. `generate.py` removes eight such links and checks the remaining source edges for occlusion and coincident routes. The ten generated figures retain varied Finnish-context designs and contain 83 nodes, 105 edges, and 198 printed text regions.

The figures are rendered by Python from graph definitions also exported as Mermaid. The Mermaid files are graph definitions, not the pixel renderer. `*.source.json`, `*.mmd`, and `*.png` are retained separately. `text_qa.json` and `edge_qa.json` record source-image checks.

## Reproduce the machine scores

Run from the repository root after installing the local OCR dependencies and model caches described in `benchmark_v3/README.md`:

```powershell
python benchmark_v4/run_rapid.py
python benchmark_v4/run_paddle.py
python benchmark_v4/run_legacy.py
python benchmark_v4/score_ocr.py
python benchmark_v4/evaluate_blind.py blind_vision
python benchmark_v4/evaluate_blind.py blind_fusion
python benchmark_v4/build_union.py
python benchmark_v4/evaluate_blind.py vision_ocr_union
python benchmark_v4/summarize.py
python benchmark_v4/build_pdf.py
```

The blind prediction JSON files are already frozen and tracked. Do not score before saving predictions in a new rerun. Recreate anonymous inputs with `python benchmark_v4/prepare_blind_inputs.py`; these duplicate input files are ignored by Git. The independent blind vision task received only anonymous PNGs; the independent fusion task received PNGs and raw RapidOCR JSON. Their access logs are self-reports, so blinding was procedural rather than enforced by filesystem isolation.

`REPORT.md` explains metrics and limitations; `approach_matrix.csv`, `item_error_ledger.json`, and `results_viewer.html` contain the machine-readable results and side-by-side images. OCR-only rows and graph rows share a fixed 198-item denominator but measure different tasks.
