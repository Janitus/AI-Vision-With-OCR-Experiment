# Second set of Finnish-context source graphs

This folder contains ten **synthetic** Mermaid graphs and 1400 × 850 PNG previews. They cover healthcare, ministries, weather, rail travel, education, libraries, taxation, rescue services, energy, and research. The diagrams use boxes, rounded boxes, circles, pills, diamonds, hexagons, and unboxed labels; both color and monochrome styles; several fonts; and some edge labels rotated along their arrows.

The PNG previews are drawn directly from the same specifications as the `.mmd` files. They are **not** screenshots of Mermaid's renderer. The Mermaid files encode the same nodes, relationships, arrow directions, node shapes, colors, and font families, but Mermaid's automatic layout can differ from the PNG preview.
Edge-label rotation and exact coordinates are recorded in each `.source.json` file and applied to the PNG preview; those details are not represented in the `.mmd` flowchart text.

`text_qa.json` records every text box. The generator rejects clipped text, overlaps between edge labels and nodes or other text, and text/background contrast below 4.5:1. All ten current previews passed. The source data is synthetic and does not assert real Finnish institutional relationships.

## Generate and review

```powershell
python benchmark_v2/generate.py
python benchmark_v2/build_preview.py --out benchmark-v2-preview.html
```

`manifest.json` lists the diagrams. Each case has `<id>.mmd`, `<id>.png`, and `<id>.source.json`.

## Reproduce the benchmark

The completed results are in `VALIDATION.md`, `approach_matrix.csv`, and `results_viewer.html`. Each `runs/<approach>/<id>.json` file retains the raw OCR text, confidence, and polygon. `reports/<approach>_<id>.json` records exact expected/observed text and unmatched OCR. `vision_review.json` retains the non-blind visual graph reading; `inferred/<id>.json`, `.mmd`, and `.png` contain the fused graph and reconstruction.

Use Python 3.13 on Windows with these workspace-local installs (no API key):

```powershell
python -m pip install --target .vendor_rapidocr "rapidocr>=3.10,<4" onnxruntime
python -m pip install --target .vendor_paddle "paddlepaddle>=3,<4" "paddleocr>=3,<4"
python -m pip install --target .vendor rapidocr_onnxruntime==1.2.3
```

The RapidOCR script downloads PP-OCRv6 medium detection and recognition models automatically into `benchmark_v2/models/rapid` when Python can verify the model host. On this Windows host, Python's certificate bundle rejected ModelScope, so the two files were downloaded with Windows `curl.exe` and checked against the model registry hashes:

```powershell
New-Item -ItemType Directory -Force benchmark_v2/models/rapid | Out-Null
curl.exe -fL -o benchmark_v2/models/rapid/PP-OCRv6_det_medium.onnx https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv6/det/PP-OCRv6_det_medium.onnx
curl.exe -fL -o benchmark_v2/models/rapid/PP-OCRv6_rec_medium.onnx https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv6/rec/PP-OCRv6_rec_medium.onnx
Get-FileHash benchmark_v2/models/rapid/*.onnx -Algorithm SHA256
```

Expected SHA-256: detection `92078b7355007ccfffcd4c8cd441a3afd4538904d06881b29a155e1e679907c2`; recognition `eef444829dbbe18d7fea59a3f6eb75647518d2b3a9568d27c92e42940204894b`. PaddleOCR downloads its official PP-OCRv5 server detector and Latin mobile recognizer into `benchmark_v2/models/paddle`.

```powershell
$env:SSLKEYLOGFILE = ''
python benchmark_v2/run_legacy.py
python benchmark_v2/run_paddle.py
python benchmark_v2/run_rapid.py
python benchmark_v2/score_ocr.py
python benchmark_v2/score_graph.py
python benchmark_v2/export_results.py
python benchmark_v2/build_report.py
```

The OCR comparisons are reproducible from the image pixels. The graph reading is an inspectable, **non-blind** Codex visual annotation made in the fixture-authoring conversation. It is not a reproducible call to a separate vision API and cannot validate general visual-model accuracy. No credentials were used.
