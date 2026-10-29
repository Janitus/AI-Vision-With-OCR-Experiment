# Blind Codex vision evaluation

A fresh Codex session received only ten anonymous PNG paths and saved its predictions before this scoring script read the source data. The session was instructed not to inspect source files. Its recorded tool log shows image-file listing, ten `view_image` calls, prediction-file writes, and a final prediction-file listing; it shows no source-data reads. This is a procedural blind test, not a filesystem-enforced access barrier. Session ID: `01a1874c-07c3-7be3-b748-10c827d5c15e`.

| Error type | Errors / expected | Rate |
|---|---:|---:|
| Title | 0/10 | 0.0% |
| Node detection | 0/49 | 0.0% |
| Node label | 0/49 | 0.0% |
| Node shape | 4/49 | 8.2% |
| Connection | 0/41 | 0.0% |
| Arrow direction | 1/41 | 2.4% |
| Relationship label | 0/41 | 0.0% |
| Dashed/solid stroke | 0/41 | 0.0% |
| Fully correct edge | 1/41 | 2.4% |

## Item-level errors

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

### case_06

No scored errors.

### case_07

No scored errors.

### case_08

No scored errors.

### case_09

- {"kind": "wrong_arrow", "edge": 4, "expected": [3, 4, "undirected"], "observed": [3, 4, "unknown"]}
- Self-reported uncertainties: ["Analyysi–Julkaisu dashed line has no visible arrowhead; direction is unknown."]

### case_10

No scored errors.

## Limits

The images are clean synthetic figures and come from the same fixture collection used previously, but this separate thread did not receive that history. The new session's prompt constrained file reads; filesystem access was not technically restricted to image files. The scorer matches nodes by image center within 130 pixels and records larger than 35-pixel coordinate offsets. This test measures literal diagram extraction, not whether the diagram's Finnish-domain statements are true.
