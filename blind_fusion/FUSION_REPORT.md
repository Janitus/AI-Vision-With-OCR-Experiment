# Blind vision-only versus blind OCR + vision

Two separate fresh Codex sessions processed the same ten anonymous images. The fusion session also received raw RapidOCR PP-OCRv6 medium Finnish observations (text, confidence, coordinates), without ground truth. Both sessions saved predictions before this comparison. The fusion session's recorded tool calls show only its image copies, OCR files, and prediction folder; no ground-truth reads. Lower error rates are better.

| Error type | Vision only | OCR + vision | Change |
|---|---:|---:|---:|
| title error rate | 0.0% | 0.0% | +0.0 pp |
| node detection error rate | 0.0% | 0.0% | +0.0 pp |
| node label error rate | 0.0% | 0.0% | +0.0 pp |
| node shape error rate | 8.2% | 8.2% | +0.0 pp |
| topology error rate | 0.0% | 0.0% | +0.0 pp |
| arrow error rate | 2.4% | 0.0% | -2.4 pp |
| relationship error rate | 0.0% | 0.0% | +0.0 pp |
| stroke error rate | 0.0% | 0.0% | +0.0 pp |
| full edge error rate | 2.4% | 0.0% | -2.4 pp |

Fusion session recorded 3 OCR disagreements or rejected OCR detections.

## Per-case errors

### case_01

No scored errors.

### case_02

- {"kind": "wrong_node_shape", "expected": "pill", "observed": "round", "node": 0}
- {"kind": "wrong_node_shape", "expected": "pill", "observed": "round", "node": 1}
- {"kind": "wrong_node_shape", "expected": "pill", "observed": "round", "node": 2}
- {"kind": "wrong_node_shape", "expected": "pill", "observed": "round", "node": 3}

### case_03

No scored errors.

### case_04

No scored errors.

### case_05

No scored errors.
- OCR disagreements: ["V: OCR detected the arrowhead between Tilannekuva and Johto as text."]

### case_06

No scored errors.
- OCR disagreements: ["7: OCR detected an arrowhead near Sääasema as a digit."]

### case_07

No scored errors.

### case_08

No scored errors.

### case_09

No scored errors.
- Uncertainties: ["Analyysi–Julkaisu dashed line has no visible arrowhead; its direction is undirected."]
- OCR disagreements: ["00wad: OCR detected part of the dashed Aineisto–Keruu connector as text."]

### case_10

No scored errors.

## Interpretation

This is an image-only versus OCR-assisted comparison on ten clean synthetic diagrams. It is procedurally blind: the fresh fusion session was told to read only the anonymized images and OCR observations. Workspace permissions did not technically prevent other file reads. OCR can corroborate printed text, but it cannot by itself establish a missing arrowhead or distinguish nearly identical rounded-box categories. The improved arrow result is a different visual judgment in a fresh session; this single comparison cannot show that OCR caused it. These ten examples are too small to estimate general error rates precisely.
