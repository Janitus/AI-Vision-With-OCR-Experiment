# Complex Finnish graph benchmark (v3)

Ten synthetic Finnish-context graphs increase the fixture set from v2's 49 nodes and 41 edges to 83 nodes and 113 edges. Each case has a `.mmd` graph definition, `.source.json` truth and coordinates, and a rendered `.png`. The Mermaid source defines the graph; `generate.py` draws the pixel image so text position and visibility can be checked deterministically.

## Reproduce local figures and OCR

From the repository root on Windows, use Python 3.13 with Pillow and the optional OCR environments described in [benchmark_v2/README.md](../benchmark_v2/README.md). The runners import packages from `.vendor_rapidocr`, `.vendor_paddle`, and `.vendor`; these directories and downloaded model caches are ignored by Git. No API key is used.

```powershell
python benchmark_v3/generate.py
python benchmark_v3/run_rapid.py
python benchmark_v3/run_paddle.py
python benchmark_v3/run_legacy.py
python benchmark_v3/score_ocr.py
```

The v3 OCR runners reuse the locally cached models in `benchmark_v2/models`. RapidOCR is PP-OCRv6 medium with Finnish detection/recognition settings; PaddleOCR is PP-OCRv5 with `lang="fi"` (Latin mobile recognition model). `run_legacy.py` is the old bundled ch_PP-OCRv3 baseline. Each runner writes unmodified OCR text, confidence, and polygons under `runs/<approach>`.

## Blind vision protocol

`python benchmark_v3/prepare_blind_inputs.py` recreates anonymous copies of source images and RapidOCR observations in ignored input folders. Two fresh Codex tasks inspect either just those images or the images with OCR. They must save all ten predictions under `blind_vision/predictions` or `blind_fusion/predictions` before scoring. This is procedural blinding with audited tool use, not filesystem isolation. The saved results can be rescored with:

The blind fusion task used the raw **RapidOCR 3.10 PP-OCRv6 medium Finnish** observations. Codex compared OCR with the image and wrote the graph; no automated fusion algorithm was run. PaddleOCR PP-OCRv5 Finnish and the old RapidOCR baseline were OCR-only comparison rows.

```powershell
python benchmark_v3/evaluate_blind.py blind_vision
python benchmark_v3/evaluate_blind.py blind_fusion
python benchmark_v3/summarize.py
python benchmark_v3/export_viewer.py
```

The [readable approach matrix](matrix_viewer.html), [full CSV](approach_matrix.csv), [validation report](REPORT.md), [item-level ledger](item_error_ledger.json), and [side-by-side viewer](results_viewer.html) are tracked. In the matrix, `—` means a modality cannot produce that measurement, such as an arrow direction from OCR text alone. Per-type error rates use expected ground-truth elements as denominator and count missing elements as errors. The headline total counts missing, wrong, and extra outputs per 206 fixed source items; extra predictions never increase that denominator. Full-edge correctness requires matching endpoints, literal label, arrow direction, and dashed/solid style.
