"""Coordinate based, exact text audit for the ten synthetic graph images."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def distance(a, b):
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j-1] + (ca != cb)))
        previous = current
    return previous[-1]


def norm(s):
    return " ".join(s.split())


def center(box):
    return ((box[0] + box[2])/2, (box[1] + box[3])/2)


def observations(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    result = []
    for item in data["observations"]:
        polygon = item.get("polygon") or item.get("box")
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        result.append({**item, "bbox": [min(xs), min(ys), max(xs), max(ys)]})
    return result


def score_one(qa, obs, title):
    expected = [{"kind":"title", "id":0, "text":title, "bbox":qa["title_bbox"]}]
    expected.extend(qa["text_boxes"])
    used = set()
    details = []
    # Assign each observed box to the nearest expected printed text region.
    # The 25 px margin permits detector boxes wider than font raster bounds.
    for item in expected:
        x1,y1,x2,y2 = item["bbox"]
        matches = []
        for oi, ob in enumerate(obs):
            if oi in used:
                continue
            cx,cy = center(ob["bbox"])
            if x1-25 <= cx <= x2+25 and y1-25 <= cy <= y2+25:
                matches.append((oi, ob))
        matches.sort(key=lambda pair: (center(pair[1]["bbox"])[1], center(pair[1]["bbox"])[0]))
        for oi,_ in matches:
            used.add(oi)
        seen = norm(" ".join(ob["text"] for _, ob in matches))
        wanted = norm(item["text"])
        details.append({"kind":item["kind"], "id":item["id"], "expected":wanted,
                        "observed":seen, "exact":seen==wanted,
                        "character_edits":distance(wanted, seen),
                        "bbox":item["bbox"],
                        "rotation":item.get("rotation",0),
                        "ocr_indices":[oi for oi,_ in matches]})
    unmatched = [dict(index=i,text=ob["text"],bbox=ob["bbox"])
                 for i,ob in enumerate(obs) if i not in used]
    by_kind = {}
    for kind in ("title","node","edge"):
        subset = [d for d in details if d["kind"]==kind]
        by_kind[kind] = {"exact":sum(d["exact"] for d in subset),
                         "total":len(subset),
                         "recall":round(sum(d["exact"] for d in subset)/len(subset),4) if subset else None,
                         "cer":round(sum(d["character_edits"] for d in subset)/sum(len(d["expected"]) for d in subset),4) if subset else None}
    rotated = [d for d in details if d["kind"]=="edge" and d["rotation"]]
    by_kind["rotated_edge"] = {"exact":sum(d["exact"] for d in rotated),
                               "total":len(rotated),
                               "recall":round(sum(d["exact"] for d in rotated)/len(rotated),4) if rotated else None}
    by_kind["all"] = {"exact":sum(d["exact"] for d in details),
                      "total":len(details),
                      "recall":round(sum(d["exact"] for d in details)/len(details),4),
                      "cer":round(sum(d["character_edits"] for d in details)/sum(len(d["expected"]) for d in details),4)}
    nonempty=sum(bool(d["observed"]) for d in details)
    extras=sum(bool(o["text"].strip()) for o in unmatched)
    by_kind["all"]["observed_items"]=nonempty+extras
    by_kind["all"]["extra_ocr_items"]=extras
    by_kind["all"]["precision"]=round(by_kind["all"]["exact"]/(nonempty+extras),4) if nonempty+extras else None
    return {"metrics":by_kind,"details":details,"unmatched_ocr":unmatched}


def main():
    qa = json.loads((ROOT/"text_qa.json").read_text(encoding="utf-8"))
    matrix = []
    reports = ROOT/"reports"
    reports.mkdir(exist_ok=True)
    for run in sorted((ROOT/"runs").iterdir()):
        if not run.is_dir():
            continue
        totals = {kind:{"exact":0,"total":0} for kind in ("title","node","edge","rotated_edge","all")}
        totals["all"].update({"observed_items":0,"extra_ocr_items":0})
        cases = {}
        for source in sorted(ROOT.glob("*.source.json")):
            slug=source.name.removesuffix(".source.json")
            raw=run/(slug+".json")
            if not raw.exists():
                continue
            truth=json.loads(source.read_text(encoding="utf-8"))
            report=score_one(qa[slug],observations(raw),truth["title"])
            cases[slug]=report["metrics"]
            (reports/(run.name+"_"+slug+".json")).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
            for kind,metric in report["metrics"].items():
                totals[kind]["exact"]+=metric["exact"]
                totals[kind]["total"]+=metric["total"]
            totals["all"]["observed_items"]+=report["metrics"]["all"]["observed_items"]
            totals["all"]["extra_ocr_items"]+=report["metrics"]["all"]["extra_ocr_items"]
        if not cases:
            continue
        for metric in totals.values():
            metric["recall"]=round(metric["exact"]/metric["total"],4) if metric["total"] else None
        totals["all"]["precision"]=round(totals["all"]["exact"]/totals["all"]["observed_items"],4) if totals["all"]["observed_items"] else None
        matrix.append({"approach":run.name,"cases_ran":len(cases),"totals":totals,"cases":cases})
    (ROOT/"ocr_matrix.json").write_text(json.dumps(matrix,ensure_ascii=False,indent=2),encoding="utf-8")
    for row in matrix:
        print(row["approach"],row["cases_ran"],row["totals"])


if __name__=="__main__":
    main()
