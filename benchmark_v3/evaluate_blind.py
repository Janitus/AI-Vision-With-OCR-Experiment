"""Score a separate session's saved image-only predictions against the hidden fixtures."""
import csv
import json
import math
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT


def load(path):return json.loads(path.read_text(encoding="utf-8"))
def fraction(good,total):return round(good/total,4) if total else None
def clean(s):return " ".join(str(s or "").split())


def shape(s):
    value=clean(s).lower().replace("-","_").replace(" ","_")
    aliases={"rectangle":"box","rect":"box","square":"box","rounded_rectangle":"round",
             "rounded_box":"round","oval":"circle","ellipse":"circle","text_only":"text",
             "unboxed":"text","no_box":"text","plain":"text","hexagon":"hex","capsule":"pill"}
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
            if d<=155:pairs.append((d,pi,ti))
    used_p=set();used_t=set();mapping={};matches=[]
    for d,pi,ti in sorted(pairs):
        if pi in used_p or ti in used_t:continue
        used_p.add(pi);used_t.add(ti);mapping[actual_nodes[pi].get("id")]=ti
        matches.append((pi,ti,d))
    errors=[];exact_node=exact_shape=full_node=0
    for pi,ti,d in matches:
        p=actual_nodes[pi];t=expected_nodes[ti]
        good_label=clean(p.get("label"))==clean(t["label"])
        if good_label:exact_node+=1
        else:errors.append({"kind":"wrong_node_text","expected":t["label"],"observed":p.get("label"),"node":ti})
        es=shape(t.get("shape") or truth["shape"]);ps=shape(p.get("type"))
        good_shape=es==ps
        if good_shape:exact_shape+=1
        else:errors.append({"kind":"wrong_node_shape","expected":es,"observed":ps,"node":ti})
        full_node+=good_label and good_shape
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
        # Parallel or opposite edges must be paired by their printed labels and arrows.
        ti,t=min(candidates,key=lambda pair:(
            clean(p.get("relationship"))!=clean(pair[1]["label"]),
            not (p.get("direction")==pair[1]["direction"] and
                 (pair[1]["direction"]=="undirected" or [a,b]==[pair[1]["source"],pair[1]["target"]]))))
        used_edges.add(ti);topology+=1
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
            "exact_node_labels":exact_node,"exact_node_shapes":exact_shape,
            "fully_correct_nodes":full_node,"truth_edges":len(expected_edges),
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


def evaluate(approach):
    mapping=load(ROOT/"blind_mapping.json")
    results={}
    for case,slug in mapping.items():
        path=ROOT/approach/"predictions"/f"{case}.json"
        if not path.exists():raise SystemExit(f"Missing prediction: {path}")
        results[case]=compare(slug,load(path))
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
    output={"approach":approach,"counts":totals,"error_rates":rates,"cases":results,
            "node_precision":fraction(totals["matched_nodes"],totals["predicted_nodes"]),
            "node_recall":fraction(totals["matched_nodes"],totals["truth_nodes"]),
            "edge_precision":fraction(totals["matched_topology"],totals["predicted_edges"]),
            "edge_recall":fraction(totals["matched_topology"],totals["truth_edges"]),
            "unknown_directions":sum(1 for case in mapping for e in load(ROOT/approach/"predictions"/f"{case}.json").get("edges",[]) if clean(e.get("direction")).lower()=="unknown"),
            "unknown_relationships":sum(1 for case in mapping for e in load(ROOT/approach/"predictions"/f"{case}.json").get("edges",[]) if clean(e.get("relationship")).lower()=="unknown")}
    (ROOT/approach/"scores.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"counts":totals,"error_rates":rates},ensure_ascii=False,indent=2))


if __name__=="__main__":evaluate(sys.argv[1])
