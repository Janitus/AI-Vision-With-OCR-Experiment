# Ten-graph extraction benchmark

This benchmark contains ten **synthetic**, Finnish-language graph scenarios: healthcare, ministries, rescue services, rail transport, education, environment, taxation, libraries, energy, and municipal services. The relationships are test data, not assertions about real Finnish institutions. Every case has a Mermaid source (`*.mmd`), a rendered image (`*.png`), and exact source JSON (`*.truth.json`). The images are drawn by a deterministic Pillow renderer from the same specifications as the Mermaid files; they are not screenshots from the Mermaid renderer.

Each image has six nodes and seven source edges. The random seed fixes node layout and graph topology. Crossings, obscured arrowheads, Finnish characters, repeated edge labels, and occasional unlabeled-looking segments make the set a useful stress test. It is still a small, synthetic set with regular colored boxes; the scores do not estimate performance on real diagrams.

## Approaches

| Matrix row | What ran |
|---|---|
| `rapidocr_full` | RapidOCR on the whole image, plus color-contour box detection. No edge inference. |
| `rapidocr_crops` | RapidOCR on enlarged detected node crops. No edge inference. |
| `codex_vision` | Codex visual reading of each rendered PNG, saved in `reviewed/*.json`. |
| `codex_plus_rapidocr` | Conservative reconciliation of the Codex visual reading and whole-image OCR. |

No Ollama, API key, or hosted model call was used for these runs. The Codex review was created after the fixture generator in the same session, so this is **not a blinded independent evaluation**. The `reviewed/create.py` file records those ten visual readings and does not automate Codex on new images.
The exact Codex model identifier was not recorded with those reviewed images; treat that row as an unversioned visual review, not a reproducible model benchmark.

The OCR rows used `rapidocr_onnxruntime` 1.2.3 and its bundled `ch_PP-OCRv3` models. This is a legacy package and **not a Finnish-specific or current-best OCR comparison**. The two OCR variants differ only in full-image versus enlarged-node-crop preprocessing. To select an OCR engine for Finnish, benchmark current PaddleOCR with `lang="fi"`, current RapidOCR with a multilingual model, and Tesseract with `fin.traineddata` on the same images.

## Reproduce

On Windows PowerShell, from the repository root:

```powershell
$env:SSLKEYLOGFILE = ''
python -m pip install --target .vendor rapidocr-onnxruntime
python benchmark/generate.py
python benchmark/reviewed/create.py
python benchmark/run.py
python benchmark/export_mermaid.py
python benchmark/report.py
python benchmark/build_viewer.py --out benchmark-viewer.html
python -m unittest -v test_graph_extract.py benchmark.test_evaluate
```

`benchmark/run.py` reads existing reviewed JSON. If you change the generated images, create new visual annotations before trusting that row. `benchmark/generate.py` uses Pillow; `benchmark/run.py` uses OpenCV and NumPy provided by RapidOCR's dependencies.

## Read the results

- [`results/summary.md`](results/summary.md): compact results and error counts.
- [`results/matrix_compact.csv`](results/matrix_compact.csv): one row per approach, aggregate metrics.
- [`results/matrix.csv`](results/matrix.csv): one row per approach, columns for every graph and metric plus macro averages.
- [`results/all_errors.csv`](results/all_errors.csv): one row per detected discrepancy, with expected and observed values where available.
- `runs/<approach>/<case>.graph.json`: extracted graph.
- `runs/<approach>/<case>.mmd`: inferred Mermaid graph for direct comparison with the source `*.mmd`.
- `runs/<approach>/<case>.raw.json`: raw OCR observations for OCR approaches.
- `runs/<approach>/<case>.errors.json`: exact per-case mismatches against source data.
- `build_viewer.py` packages the images, source Mermaid, inferred Mermaid, and error counts into a self-contained comparison viewer.

The scorer matches nodes by box intersection-over-union (IoU ≥ 0.5), then checks exact node text, type, and box overlap. It matches edges by endpoint topology and checks arrow orientation and relationship text separately. It also compares the multiset of all visible text, including the title and repeated edge labels, with only whitespace normalized. `unknown` never receives credit as a correct label or direction. End-to-end edge recall requires matching topology, arrow, relationship, and both endpoint labels. Blank matrix cells mean the metric has no denominator.
