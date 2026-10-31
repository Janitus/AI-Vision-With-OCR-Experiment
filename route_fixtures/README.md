# Paired routed-arrow fixtures

These two Finnish rail-control figures keep the same eight nodes, twelve edges, printed labels, and arrow directions as `benchmark_v4/junaliikenteen_ohjaus`. One reroutes every edge as a cubic Bézier curve; the other uses right-angle detours. The original v4 figure is the straight-route baseline. The graph labels, endpoints, and arrow directions are paired, while node appearance and label placement also change. Compare route effects cautiously.

Each figure has a PNG, Mermaid graph definition, and source JSON. The JSON preserves every line or cubic control point and label position. Mermaid represents topology and printed relationships but cannot reproduce the exact custom paths. The source JSON is the geometry ground truth.

`generate.py` samples every path, rejects any edge that enters a seven-pixel-expanded box around a node other than its source or target, rejects shared straight route segments longer than 20 pixels, checks that paths terminate on their endpoint node boundaries, checks title/node/edge-label clipping and overlap, and requires every edge label to be within 50 pixels of its route. `route_qa.json` records the results. Both PNGs were inspected visually at full size.

Open [the side-by-side viewer](viewer.html) to compare straight, curved, and right-angle routes. These fixtures were scored in [benchmark v5](../benchmark_v5/REPORT.md).

To regenerate from the repository root:

```powershell
python route_fixtures/generate.py
```
