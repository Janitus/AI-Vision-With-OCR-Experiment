# Conservative graph extraction

**Current findings:** [short report](BENCHMARK_SUMMARY.md) · [combined approach matrix](blind_vision/combined_approach_matrix.csv) · [blind OCR + vision comparison](blind_fusion/FUSION_REPORT.md) · [side-by-side viewer](blind_fusion/comparison_viewer.html).

The ten-case original evaluation is in [benchmark/README.md](benchmark/README.md). The varied second set, its sources, rendered images, OCR observations, and validation are in [benchmark_v2/README.md](benchmark_v2/README.md). Two separate fresh Codex sessions produced [image-only](blind_vision/BLIND_REPORT.md) and [OCR-assisted](blind_fusion/FUSION_REPORT.md) graph predictions before they were scored against source data.

On these ten clean synthetic diagrams, RapidOCR PP-OCRv6 medium Finnish read all 100 expected text items with three false positives. Blind Codex vision recovered 40/41 fully correct edges; a separate OCR-assisted session recovered 41/41 and rejected the three false OCR detections. The arrow improvement cannot be attributed to OCR alone because OCR does not provide arrow direction. Both sessions called four pill shapes rounded rectangles. See the reports for denominators, uncertainty handling, and test limits.

The anonymous blind input folders are excluded from Git because they duplicate the tracked fixture images and OCR observations. Recreate them with `python prepare_blind_inputs.py` before rerunning the blind workflow. The saved predictions and score reports are tracked.

## Optional local pipeline

`graph_extract.py` runs PaddleOCR at four image rotations, asks a **local** Ollama vision model to trace boxes and arrows, compares the two results, and writes graph JSON, Mermaid, and a validation report. It does not use an API key or any hosted LLM endpoint. Local models may need to be downloaded during setup. PaddleOCR defaults to `lang="fi"` and `PP-OCRv5` for Finnish text; override with `--ocr-lang` and `--ocr-version` when evaluating another route.

## Setup

Use a Python environment supported by your PaddlePaddle installation. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull llava
ollama serve
```

`ollama serve` occupies its terminal. Open another PowerShell terminal in this folder, activate the same environment, and run:

```powershell
python graph_extract.py input.png --model llava --out output
```

See the [PaddleOCR installation guide](https://www.paddleocr.ai/main/en/quick_start.html) if the PaddlePaddle wheel for your Python/platform needs a different install command. The code uses the PaddleOCR 3.x `predict` result fields (`rec_texts`, `rec_scores`, `rec_polys`). The [Ollama LLaVA page](https://ollama.com/library/llava) documents the local vision model used by default.

To replay reviewed observations without running either engine:

```powershell
python graph_extract.py input.png --ocr-json sample/ocr.json --vision-json sample/vision_raw.json --out sample/output
```

The supplied image is copied to `input.png`. `sample/vision_raw.json` is a **manual visual review**, not an LLM response; `sample/ocr.json` explicitly says OCR was not run. The generated sample graph is therefore a provisional reading of the image. Run the full command above for an actual OCR and vision comparison.

## Outputs

| File | Contents |
|---|---|
| `ocr.json` | Individual OCR observations, confidence, polygon, original-image coordinates, and rotation. |
| `vision_raw.json` | Unmodified local model response, or supplied reviewed response. |
| `graph.json` | Reconciled nodes and edges with confidence, evidence, coordinates, and uncertainties. |
| `graph.mmd` | Mermaid reconstruction of the emitted graph. |
| `validation.json` | Counts, uncertainty list, and optional ground-truth metrics. |

The vision model must supply a traced line with at least two points and valid endpoint node IDs before an edge is emitted. `unknown` is used for unresolved relationship text or arrow direction. OCR and vision text disagreements are kept in `uncertainties`; a vision-only reading is capped at lower confidence. Node type describes a visible shape/color, not an inferred legal or conceptual class. Confidence values are heuristic evidence scores, not calibrated probabilities.

For supplied graph truth, use `--ground-truth truth.json` (same `nodes`/`edges` schema), `truth.mmd` (the emitted Mermaid subset), or a simple `truth.dot`. Node metrics require exact labels; edge metrics require exact endpoint labels, relationship text, and direction. A missing or empty truth set gives a `null` precision/recall denominator. This scorer intentionally does not treat a synonymous relationship as correct.

## Limits

- A model can still hallucinate a plausible line or label. Review the source image and all `vision_only` elements before using the graph as fact.
- Small labels and crossing lines are particularly hard. The sample omits two crossing diagonal edges whose endpoints are unclear.
- Mermaid output renders uncertain directions as undirected lines with a `[direction unknown]` label; inspect `graph.json` for the original value.
- The sample has no independent ground truth, so it reports uncertainties but no precision/recall.
