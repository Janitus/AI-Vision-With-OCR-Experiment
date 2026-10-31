# Twelve-diagram benchmark with routed arrows

Ten corrected v4 diagrams plus two route variants contain 99 nodes and 129 edges. The rail straight, curved, and right-angle cases have the same graph labels and topology. Exact custom route coordinates live in source JSON; Mermaid encodes topology.

Source QA: 0 clipped text regions; 0 overlapping text regions; 0 edges hidden by a non-endpoint node; 0 coincident edge pairs. Minimum text contrast 7.49:1. The two routed images were inspected visually and passed 24 sampled route-to-node checks.

## Approach matrix

| Approach | Task | Total scorer events / 240 | Exact figures | Title | Node text | Edge text | Shape | Arrow | Extra text |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RapidOCR PP-OCRv6 Finnish | OCR text | 17/240 (7.1%) | 7/12 | 0 | 0 | 2 | — | — | 15 |
| PaddleOCR PP-OCRv5 Finnish | OCR text | 57/240 (23.8%) | 3/12 | 0 | 0 | 19 | — | — | 38 |
| Older RapidOCR baseline | OCR text | 74/240 (30.8%) | 0/12 | 9 | 23 | 42 | — | — | 0 |
| Blind Codex vision | Graph | 20/240 (8.3%) | 7/12 | 0 | 0 | 0 | 18 | 1 | — |
| Blind Codex + RapidOCR | Graph | 12/240 (5.0%) | 8/12 | 0 | 0 | 0 | 8 | 3 | — |
| Vision + deterministic OCR evidence | Graph | 20/240 (8.3%) | 7/12 | 0 | 0 | 0 | 18 | 1 | — |

OCR rows score exact printed text at source locations plus unmatched OCR boxes. Graph rows score titles, nodes (label and shape), and complete visible edges (endpoints, printed relationship, arrowhead, stroke). All rows use 240 source items, but OCR and graph rows measure different tasks. Precision/recall in the CSV is correct reported items / all reported items and correct source items / all source items. A total rate can exceed 100% when there are many extras.

An arrowless link predicted with unknown semantic direction is accepted as visually faithful and logged separately. The independent fusion run saw images and RapidOCR PP-OCRv6 medium Finnish observations. The deterministic OCR union attaches evidence without changing vision nodes or edges, so identical graph scores are expected.

## Paired rail-route comparison

| Approach | Straight events / 21 | Curved events / 21 | Right-angle events / 21 |
|---|---:|---:|---:|
| RapidOCR PP-OCRv6 Finnish | 1 | 0 | 1 |
| PaddleOCR PP-OCRv5 Finnish | 5 | 0 | 0 |
| Older RapidOCR baseline | 8 | 7 | 7 |
| Blind Codex vision | 8 | 0 | 0 |
| Blind Codex + RapidOCR | 9 | 1 | 1 |
| Vision + deterministic OCR evidence | 8 | 0 | 0 |

The three rail images share one topology, so 12 images are not 12 independent graph samples. The straight figure uses oval nodes while the routed variants use pill nodes; line and label placement also differ. This is a paired topology comparison, not an isolated route-shape test. One paired set and independently prompted vision/fusion agents cannot establish a general curve penalty or OCR causal gain.

## Reproducibility and limits

Fresh blind agents received anonymous images only, or images plus raw RapidOCR, and saved all predictions before scoring. Their access logs are self-reports; filesystem access was not sealed. The diagrams are clean and synthetic. Relationship scoring checks what is printed, not real-world semantic truth. Source JSON, Mermaid, PNGs, OCR observations, predictions, matrix CSV, paired CSV, and item-level ledger are retained separately.
