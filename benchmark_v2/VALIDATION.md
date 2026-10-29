# Validation report: ten Finnish graph fixtures

## Scope and method

Ten 1400×850 synthetic PNGs were reviewed for clipped or overlapping text before benchmarking. All have paired Mermaid source and JSON ground truth. OCR ran on each full image. The scorer assigns recognized polygons to known printed text regions by location, then requires exact Unicode text; case and Finnish diacritics matter. This spatial assignment is evaluation only, so its node and edge categories do not mean an OCR engine inferred graph structure.

The graph review was made by Codex from the images in the same conversation that created the fixtures. It is **non-blind** and must not be interpreted as an independent model accuracy estimate. No API keys or remote vision API were used. OCR models were downloaded once and run locally.

## Aggregate matrix

| Approach | Exact text recall | Exact text precision | Exact node labels | Exact edge labels | Rotated labels | Connections | Correct arrows | Fully correct edges | Shape / stroke |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| legacy_rapid_v3 | 73.0% | 74.5% | 75.5% | 70.7% | 90.0% | 0/41 | — | 0/41 | — / — |
| paddle_v5_fi | 100.0% | 95.2% | 100.0% | 100.0% | 100.0% | 0/41 | — | 0/41 | — / — |
| rapid_v6_medium_fi | 100.0% | 97.1% | 100.0% | 100.0% | 100.0% | 0/41 | — | 0/41 | — / — |
| codex_visual_review_nonblind | — | — | 100.0% | — | — | 41/41 | 100.0% | 41/41 | 100.0% / 100.0% |
| codex_visual_plus_rapid_v6_fi | 100.0% | 97.1% | 100.0% | 100.0% | 100.0% | 41/41 | 100.0% | 41/41 | 100.0% / 100.0% |

**Denominators:** 100 visible text items (10 titles, 49 node labels, 41 edge labels); 10 rotated edge labels; 49 nodes; 41 edges. Exact text precision counts false OCR items. A fully correct edge requires the two endpoints, arrow direction, and the printed relationship label all to match. Shape and dashed-stroke accuracy are scored on the non-blind visual reading. OCR-only rows do not attempt graph reconstruction, so their zero connection count is a capability boundary rather than a failed arrow detector.

## Per-diagram exact text

| Diagram | Printed items | Legacy Rapid | Paddle v5 Finnish | Rapid v6 medium Finnish |
|---|---:|---:|---:|---:|
| Hoitopolku | 10 | 7/10 | 10/10 | 10/10 |
| Valmisteluketju | 10 | 6/10 | 10/10 | 10/10 |
| Säähavainnot | 10 | 7/10 | 10/10 | 10/10 |
| Junamatkan vaiheet | 10 | 8/10 | 10/10 | 10/10 |
| Opintopolku | 13 | 12/13 | 13/13 | 13/13 |
| Kirjastokierto | 8 | 8/8 | 8/8 | 8/8 |
| Veropäätöksen käsittely | 8 | 5/8 | 8/8 | 8/8 |
| Pelastustoimen viestit | 10 | 5/10 | 10/10 | 10/10 |
| Sähköverkon osat | 10 | 6/10 | 10/10 | 10/10 |
| Tutkimusaineiston kulku | 11 | 9/11 | 11/11 | 11/11 |

## Disagreements and potential extraction errors

### legacy_rapid_v3

27 expected text items incorrect or missing; 0 extra OCR items. Full polygon coordinates, scores, and expected/observed strings are in `runs/` and `reports/`.

- Hoitopolku · node 2: expected `Lähete`; observed `Lahete`.
- Hoitopolku · edge 1: expected `laatii`; observed `laati`.
- Hoitopolku · edge 2: expected `lähettää`; observed `lahettaa`.
- Valmisteluketju · node 1: expected `Ministeriö`; observed `Ministerio`.
- Valmisteluketju · node 4: expected `Päätös`; observed `Paatos`.
- Valmisteluketju · edge 1: expected `pyytää`; observed `pytaa`.
- Valmisteluketju · edge 3: expected `hyväksyy`; observed `hyvaksyy`.
- Säähavainnot · title 0: expected `Säähavainnot`; observed `Saahavainnot`.
- Säähavainnot · node 0: expected `Sääasema`; observed `Saaasema`.
- Säähavainnot · node 3: expected `Lämpötila`; observed `Lampotila`.
- Junamatkan vaiheet · node 4: expected `Määränpää`; observed `Maaranpaa`.
- Junamatkan vaiheet · edge 0: expected `näytetään`; observed `naytetaan`.
- Opintopolku · node 0: expected `Oppilas`; observed `∅`.
- Veropäätöksen käsittely · title 0: expected `Veropäätöksen käsittely`; observed `Veropaatoksen kasittely`.
- Veropäätöksen käsittely · node 0: expected `Ilmoitus`; observed `IImoitus`.
- Veropäätöksen käsittely · node 2: expected `Päätös`; observed `Paatos`.
- Pelastustoimen viestit · node 0: expected `Hälytys`; observed `Halytys`.
- Pelastustoimen viestit · node 1: expected `Hätäkeskus`; observed `Hatakeskus`.
- Pelastustoimen viestit · edge 0: expected `välittää`; observed `valittaa`.
- Pelastustoimen viestit · edge 1: expected `hälyttää`; observed `halyttaa`.
- Pelastustoimen viestit · edge 2: expected `päivittää`; observed `paivittaa`.
- Sähköverkon osat · title 0: expected `Sähköverkon osat`; observed `Sahkoverkon osat`.
- Sähköverkon osat · node 1: expected `Sähköverkko`; observed `Sahkoverkko`.
- Sähköverkon osat · edge 0: expected `syöttää`; observed `syottaa`.
- Sähköverkon osat · edge 1: expected `siirtää`; observed `siirtaa`.
- Tutkimusaineiston kulku · edge 0: expected `ohjaa`; observed `∅`.
- Tutkimusaineiston kulku · edge 3: expected `siirtää`; observed `siirtaa`.

### paddle_v5_fi

0 expected text items incorrect or missing; 5 extra OCR items. Full polygon coordinates, scores, and expected/observed strings are in `runs/` and `reports/`.

- Hoitopolku · extra OCR `x` at [568, 423, 589, 444].
- Hoitopolku · extra OCR `x` at [838, 423, 860, 445].
- Hoitopolku · extra OCR `5.` at [1119, 425, 1137, 443].
- Säähavainnot · extra OCR `aαmbo` at [1004, 588, 1112, 657].
- Pelastustoimen viestit · extra OCR `•` at [871, 420, 890, 439].

### rapid_v6_medium_fi

0 expected text items incorrect or missing; 3 extra OCR items. Full polygon coordinates, scores, and expected/observed strings are in `runs/` and `reports/`.

- Säähavainnot · extra OCR `7` at [619.0, 444.0, 639.0, 461.0].
- Pelastustoimen viestit · extra OCR `V` at [1143.0, 419.0, 1167.0, 441.0].
- Tutkimusaineiston kulku · extra OCR `00wad` at [558.0, 200.0, 586.0, 221.0].

### Graph review and fusion

0 source-versus-visual-review node, edge, arrow, relationship, shape, or stroke errors. 0 OCR/vision disagreements on assigned graph elements. 3 unassigned OCR items; these are retained in the extracted JSON rather than turned into nodes.

- Säähavainnot · unassigned_ocr_text: `7` at [619, 444, 639, 461].
- Pelastustoimen viestit · unassigned_ocr_text: `V` at [1143, 419, 1167, 441].
- Tutkimusaineiston kulku · unassigned_ocr_text: `00wad` at [558, 200, 586, 221].

## Interpretation and limits

On this clean set, PaddleOCR PP-OCRv5 Finnish and RapidOCR PP-OCRv6 medium Finnish tie at 100/100 exact expected text items. RapidOCR has fewer false positives (3 versus 5), so it is the better observed choice for these images. This does **not** establish a generally best Finnish OCR engine. The fixtures are large, high contrast, and mostly simple chains; the visual review is non-blind. A valid independent vision benchmark needs unseen diagrams and a separately run model. Color, font family, exact edge geometry, and real-world semantic truth are not scored here. The printed relationship string is scored literally; no hidden semantics are inferred.

The original Finnish legislation image is outside this ten-fixture score set. Its smaller labels and crossed edges should be used as a separate stress test before making reliability claims.
