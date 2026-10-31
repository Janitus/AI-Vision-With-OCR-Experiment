# Can OCR and AI vision reliably reconstruct diagrams?

**Share this report as one file:** [Download the self-contained PDF](finnish_diagram_extraction_findings.pdf). It includes the matrix and example diagrams without requiring access to this repository.

These are informal notes from a small experiment, not a research paper. We tested ten clean, synthetic Finnish-context diagrams with varied layouts, shapes, fonts, colors, arrow styles, and edge labels. Together they contain **83 nodes, 113 edges, and 206 printed text regions**. The test asks whether an image can be turned into a complete graph without a human checking it.

**Correction after visual review:** Blind Codex vision matched **4 of 10 source JSON graphs exactly under the scorer**. That is not the same as saying it visibly reconstructed only four images correctly. Several generated source links overlap or pass behind nodes, so the pixels do not uniquely establish every endpoint or separate relationship in the hidden source JSON. Some graph mismatches therefore cannot be attributed to vision. The OCR text results remain separately interpretable; OCR alone did not reconstruct links or arrows.

## Results matrix

| Approach | Output scored | Scorer events / 206 source items | Exact-match figures / 10 | Key result |
|---|---|---:|---:|---|
| RapidOCR PP-OCRv6 medium Finnish | Printed text | **18 (8.7%)** | 4 | 203/206 text regions exact; 15 unmatched OCR boxes |
| PaddleOCR PP-OCRv5 Finnish | Printed text | 59 (28.6%) | 0 | 187/206 text regions exact; 40 unmatched OCR boxes |
| Older RapidOCR baseline | Printed text | 61 (29.6%) | 0 | 145/206 text regions exact; 0 unmatched OCR boxes |
| Blind Codex vision | Complete graph | **26 (12.6%)** | 4 | 83/83 nodes and 105/113 connections found; 101/113 edges fully correct |

Every row uses **206 source items as the denominator**: 10 titles, 83 nodes, and 113 edges. Extra outputs add events to the numerator. The OCR rows score text regions; the vision row scores graph elements against source JSON, including node shape and full edge properties. Their percentages therefore measure **different tasks**. The graph percentage is a source-file mismatch rate, **not a validated visible-error rate**. An 8.7% OCR text error rate does not mean RapidOCR reconstructs graphs better than vision.

| Graph metric against source JSON | Blind vision |
|---|---:|
| Node precision / recall | 100% / 100% |
| Connection precision / recall | 96.3% / 92.9% |
| Fully correct edges | 101/113 |

**Precision** is the share of reported items that match the source; **recall** is the share of source items found. Connection matching checks endpoints. A *fully correct edge* also requires the arrow direction, printed relationship label, and dashed/solid stroke to match. The detailed per-type rates in the full matrix can overlap on the same edge, so they must not be added together.

### What did exact source-graph scoring flag?

These are the **26 non-overlapping scorer entries** in the item-level ledger. Some entries reflect ambiguous source drawings:

| Error | Count | What it means |
|---|---:|---|
| Wrong node shape | 10 | Pill nodes were called rounded rectangles. |
| Source edge not separate | 8 | A source JSON edge was not a separate predicted edge; some overlap other links in the image. |
| Extra endpoint pair | 4 | Predicted endpoints differ from source JSON; some source lines pass behind nodes. |
| Edge label mismatch | 2 | The label assigned to a matched edge differs from source JSON. |
| Direction encoding mismatch | 2 | Opposite source edges overlap; a visually correct arrowhead can still be scored wrong. |

No matched link had the wrong dashed/solid stroke style. The detailed scorer's 8/113 stroke *incomplete* rate counts the eight omitted links, whose stroke could not be checked. The same omitted links also contribute to the per-type arrow and label rates; the ledger table above avoids counting them repeatedly.

## Example: source and blind reconstruction

The source below is the research-publication workflow. Between **Analyysi** and **Vertaisarvio**, the source draws two opposite relationships on one line. The reconstruction shows both arrowheads but omits the second printed relationship, *palauttaa korjattavaksi*. The source also has a long link running behind **Eettinen arvio**, making its intended endpoint ambiguous from the pixels. The PDF marks only the visibly missing relationship label in red; it does not mark the backward arrowhead as an error.

| Source figure | Blind Codex vision reconstruction |
|---|---|
| <img src="benchmark_v3/tutkimusjulkaisu.png" alt="Source research-publication diagram" width="440"> | <img src="benchmark_v3/blind_vision/rendered/case_07.png" alt="Blind vision reconstruction of the research-publication diagram" width="440"> |

See the [interactive side-by-side viewer](benchmark_v3/results_viewer.html) for all ten figures, and the [source image folder](benchmark_v3/) for other styles. GitHub may download the HTML viewer rather than run it; it also works as a local file.

## What the combined approach did

The saved **deterministic OCR evidence union** is not a second graph prediction. It matched each exact-text RapidOCR box to at most one existing vision element, kept unmatched boxes as evidence, and did not add nodes or edges. Its graph accuracy is identical to blind vision **by construction**, so it is omitted from the primary accuracy table. Its separate row remains in the [full machine-readable matrix](benchmark_v3/approach_matrix.csv) for traceability. A historical Codex session that saw both images and OCR is retained in the [full validation report](benchmark_v3/REPORT.md); it was a different experiment.

The images were generated from known graphs and checked for visible **text**, but the original quality check did not verify that every edge and endpoint remained visually identifiable. The blind vision prediction was saved before scoring; the task access audit is [here](benchmark_v3/session_audit.json). We need visually adjudicated source graphs before using the graph scores to estimate review-free reconstruction reliability. The current matrix remains a reproducible comparison to the generated source JSON, with this limitation now explicit.

Full data: [machine-readable matrix](benchmark_v3/approach_matrix.csv) · [item-level error ledger](benchmark_v3/item_error_ledger.json) · [validation report](benchmark_v3/REPORT.md) · [Mermaid sources and graph truth](benchmark_v3/README.md).
