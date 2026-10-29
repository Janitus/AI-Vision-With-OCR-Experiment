"""Score a separate session's saved image-only predictions against the hidden fixtures."""
import csv
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/"benchmark_v2"


def load(path):return json.loads(path.read_text(encoding="utf-8"))
def fraction(good,total):return round(good/total,4) if total else None
def clean(s):return " ".join(str(s or "").split())


def shape(s):
    value=clean(s).lower().replace("-","_").replace(" ","_")
    aliases={"rectangle":"box","rect":"box","square":"box","rounded_rectangle":"round",
             "rounded_box":"round","oval":"circle","ellipse":"circle","text_only":"text",
             "unboxed":"text","no_box":"text","hexagon":"hex","capsule":"pill"}
    return aliases.get(value,value)


def compare(slug,pred):
    truth=load(SOURCE/(slug+".source.json"))
    actual_nodes=pred.get("nodes",[]);expected_nodes=truth["nodes"]
    pairs=[]
    for pi,p in enumerate(actual_nodes):
        xy=p.get("center")
        if not isinstance(xy,list) or len(xy)!=2:continue
        for ti,t in enumerate(expected_nodes):
            d=math.dist(xy,[t["x"],t["y"]])
            if d<=130:pairs.append((d,pi,ti))
    used_p=set();used_t=set();mapping={};matches=[]
    for d,pi,ti in sorted(pairs):
        if pi in used_p or ti in used_t:continue
        used_p.add(pi);used_t.add(ti);mapping[actual_nodes[pi].get("id")]=ti
        matches.append((pi,ti,d))
    errors=[];exact_node=exact_shape=0
    for pi,ti,d in matches:
        p=actual_nodes[pi];t=expected_nodes[ti]
        if clean(p.get("label"))==clean(t["label"]):exact_node+=1
        else:errors.append({"kind":"wrong_node_text","expected":t["label"],"observed":p.get("label"),"node":ti})
        es=shape(t.get("shape") or truth["shape"]);ps=shape(p.get("type"))
        if es==ps:exact_shape+=1
        else:errors.append({"kind":"wrong_node_shape","expected":es,"observed":ps,"node":ti})
        if d>35:errors.append({"kind":"node_coordinate_offset","node":ti,"pixels":round(d,1)})
    for ti,t in enumerate(expected_nodes):
        if ti not in used_t:errors.append({"kind":"missing_node","expected":t["label"],"node":ti})
    for pi,p in enumerate(actual_nodes):
        if pi not in used_p:errors.append({"kind":"extra_node","observed":p.get("label"),"predicted_id":p.get("id")})
    title_exact=clean(pred.get("title"))==clean(truth["title"])
    if not title_exact:errors.append({"kind":"wrong_title","expected":truth["title"],"observed":pred.get("title")})

    actual_edges=pred.get("edges",[]);expected_edges=truth["edges"]
    used_edges=set();topology=direction=relation=stroke=full=end_to_end=0
    for pi,p in enumerate(actual_edges):
        a=mapping.get(p.get("source"));b=mapping.get(p.get("target"))
        if a is None or b is None:
            errors.append({"kind":"edge_unmatched_endpoint","predicted_edge":pi});continue
        candidates=[(ti,t) for ti,t in enumerate(expected_edges) if ti not in used_edges and {a,b}=={t["source"],t["target"]}]
        if not candidates:
            errors.append({"kind":"extra_edge","predicted_edge":pi,"endpoints":[a,b]});continue
        ti,t=candidates[0];used_edges.add(ti);topology+=1
        good_direction=p.get("direction")==t["direction"] and (t["direction"]=="undirected" or [a,b]==[t["source"],t["target"]])
        good_relation=clean(p.get("relationship"))==clean(t["label"])
        good_stroke=bool(p.get("dashed",False))==bool(t.get("dashed",False))
        direction+=good_direction;relation+=good_relation;stroke+=good_stroke
        full+=good_direction and good_relation and good_stroke
        end_to_end+=good_direction and good_relation and good_stroke and clean(actual_nodes[next(i for i,n in enumerate(actual_nodes) if n.get("id")==p.get("source"))].get("label"))==clean(expected_nodes[a]["label"]) and clean(actual_nodes[next(i for i,n in enumerate(actual_nodes) if n.get("id")==p.get("target"))].get("label"))==clean(expected_nodes[b]["label"])
        if not good_direction:errors.append({"kind":"wrong_arrow","edge":ti,"expected":[t["source"],t["target"],t["direction"]],"observed":[a,b,p.get("direction")]})
        if not good_relation:errors.append({"kind":"wrong_relationship","edge":ti,"expected":t["label"],"observed":p.get("relationship")})
        if not good_stroke:errors.append({"kind":"wrong_stroke","edge":ti,"expected_dashed":t.get("dashed",False),"observed_dashed":p.get("dashed",False)})
    for ti,t in enumerate(expected_edges):
        if ti not in used_edges:errors.append({"kind":"missing_edge","edge":ti,"expected":[t["source"],t["target"],t["label"]]})
    counts={"truth_nodes":len(expected_nodes),"predicted_nodes":len(actual_nodes),"matched_nodes":len(matches),
            "exact_node_labels":exact_node,"exact_node_shapes":exact_shape,"truth_edges":len(expected_edges),
            "predicted_edges":len(actual_edges),"matched_topology":topology,"correct_arrows":direction,
            "correct_relationships":relation,"correct_strokes":stroke,"fully_correct_edges":full,
            "end_to_end_edges":end_to_end,"title_exact":int(title_exact)}
    metrics={"node_detection_recall":fraction(len(matches),len(expected_nodes)),
             "node_detection_precision":fraction(len(matches),len(actual_nodes)),
             "node_label_error_rate":fraction(len(expected_nodes)-exact_node,len(expected_nodes)),
             "node_shape_error_rate":fraction(len(expected_nodes)-exact_shape,len(expected_nodes)),
             "topology_error_rate":fraction(len(expected_edges)-topology,len(expected_edges)),
             "arrow_error_rate":fraction(len(expected_edges)-direction,len(expected_edges)),
             "relationship_error_rate":fraction(len(expected_edges)-relation,len(expected_edges)),
             "stroke_error_rate":fraction(len(expected_edges)-stroke,len(expected_edges)),
             "full_edge_error_rate":fraction(len(expected_edges)-full,len(expected_edges)),
             "end_to_end_edge_error_rate":fraction(len(expected_edges)-end_to_end,len(expected_edges))}
    return {"counts":counts,"metrics":metrics,"errors":errors,"uncertainties":pred.get("uncertainties",[])}


def main():
    slugs=sorted(p.name.removesuffix(".source.json") for p in SOURCE.glob("*.source.json"))
    results={}
    for i,slug in enumerate(slugs,1):
        path=ROOT/"predictions"/f"case_{i:02}.json"
        if not path.exists():raise SystemExit(f"Missing prediction: {path}")
        results[f"case_{i:02}"]=compare(slug,load(path))
    totals={k:sum(r["counts"][k] for r in results.values()) for k in next(iter(results.values()))["counts"]}
    rates={
        "title_error_rate":fraction(10-totals["title_exact"],10),
        "node_detection_error_rate":fraction(totals["truth_nodes"]-totals["matched_nodes"],totals["truth_nodes"]),
        "node_label_error_rate":fraction(totals["truth_nodes"]-totals["exact_node_labels"],totals["truth_nodes"]),
        "node_shape_error_rate":fraction(totals["truth_nodes"]-totals["exact_node_shapes"],totals["truth_nodes"]),
        "topology_error_rate":fraction(totals["truth_edges"]-totals["matched_topology"],totals["truth_edges"]),
        "arrow_error_rate":fraction(totals["truth_edges"]-totals["correct_arrows"],totals["truth_edges"]),
        "relationship_error_rate":fraction(totals["truth_edges"]-totals["correct_relationships"],totals["truth_edges"]),
        "stroke_error_rate":fraction(totals["truth_edges"]-totals["correct_strokes"],totals["truth_edges"]),
        "full_edge_error_rate":fraction(totals["truth_edges"]-totals["fully_correct_edges"],totals["truth_edges"]),
        "end_to_end_edge_error_rate":fraction(totals["truth_edges"]-totals["end_to_end_edges"],totals["truth_edges"]),
    }
    output={"provenance":"Separate fresh Codex thread; image-only prompt; ground truth not supplied to that thread",
            "thread_id":"01a1874c-07c3-7be3-b748-10c827d5c15e",
            "counts":totals,"error_rates":rates,"cases":results}
    (ROOT/"blind_scores.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    with (ROOT/"blind_error_matrix.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.writer(f);writer.writerow(["approach",*rates]);writer.writerow(["codex_vision_blind",*rates.values()])
    lines=["# Blind Codex vision evaluation", "", "A fresh Codex session received only ten anonymous PNG paths and saved its predictions before this scoring script read the source data. The session was instructed not to inspect source files. Its recorded tool log shows image-file listing, ten `view_image` calls, prediction-file writes, and a final prediction-file listing; it shows no source-data reads. This is a procedural blind test, not a filesystem-enforced access barrier. Session ID: `01a1874c-07c3-7be3-b748-10c827d5c15e`.", "", "| Error type | Errors / expected | Rate |", "|---|---:|---:|"]
    pairs=[("Title",10-totals["title_exact"],10),
           ("Node detection",totals["truth_nodes"]-totals["matched_nodes"],totals["truth_nodes"]),
           ("Node label",totals["truth_nodes"]-totals["exact_node_labels"],totals["truth_nodes"]),
           ("Node shape",totals["truth_nodes"]-totals["exact_node_shapes"],totals["truth_nodes"]),
           ("Connection",totals["truth_edges"]-totals["matched_topology"],totals["truth_edges"]),
           ("Arrow direction",totals["truth_edges"]-totals["correct_arrows"],totals["truth_edges"]),
           ("Relationship label",totals["truth_edges"]-totals["correct_relationships"],totals["truth_edges"]),
           ("Dashed/solid stroke",totals["truth_edges"]-totals["correct_strokes"],totals["truth_edges"]),
           ("Fully correct edge",totals["truth_edges"]-totals["fully_correct_edges"],totals["truth_edges"])]
    for label,n,d in pairs:lines.append(f"| {label} | {n}/{d} | {n/d*100:.1f}% |")
    lines+=["", "## Item-level errors", ""]
    for case,record in results.items():
        lines.append(f"### {case}");lines.append("")
        if not record["errors"]:lines.append("No scored errors.")
        else:
            for error in record["errors"]:lines.append("- "+json.dumps(error,ensure_ascii=False))
        if record["uncertainties"]:lines.append("- Self-reported uncertainties: "+json.dumps(record["uncertainties"],ensure_ascii=False))
        lines.append("")
    lines += ["## Limits", "", "The images are clean synthetic figures and come from the same fixture collection used previously, but this separate thread did not receive that history. The new session's prompt constrained file reads; filesystem access was not technically restricted to image files. The scorer matches nodes by image center within 130 pixels and records larger than 35-pixel coordinate offsets. This test measures literal diagram extraction, not whether the diagram's Finnish-domain statements are true."]
    (ROOT/"BLIND_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"counts":totals,"error_rates":rates},ensure_ascii=False,indent=2))


if __name__=="__main__":main()
