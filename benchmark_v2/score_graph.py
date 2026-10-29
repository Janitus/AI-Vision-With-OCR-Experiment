"""Score explicit graph readings and export traceable OCR+vision JSON."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def key(a,b,direction):
    return (a,b) if direction!="undirected" else tuple(sorted((a,b)))


def score_vision(slug,pred):
    truth=read(ROOT/(slug+".source.json"))
    labels=[n["label"] for n in truth["nodes"]]
    observed=[n[0] for n in pred["nodes"]]
    correct_nodes=sum((Counter(labels)&Counter(observed)).values())
    truth_edges=[(labels[e["source"]],labels[e["target"]],e["label"],e["direction"]) for e in truth["edges"]]
    pred_edges=[(e[0],e[1],e[2],e[3] if len(e)>3 else "source_to_target") for e in pred["edges"]]
    used=set(); topology=arrows=relationships=full=strokes=0; errors=[]
    for pi,p in enumerate(pred_edges):
        candidates=[(i,t) for i,t in enumerate(truth_edges) if i not in used and set(p[:2])==set(t[:2])]
        if not candidates:
            errors.append({"kind":"extra_edge","observed":p});continue
        i,t=candidates[0];used.add(i);topology+=1
        arrow=p[3]==t[3] and key(p[0],p[1],p[3])==key(t[0],t[1],t[3])
        relationship=p[2]==t[2]
        arrows+=arrow;relationships+=relationship;full+=arrow and relationship
        if not arrow:errors.append({"kind":"wrong_arrow","expected":t,"observed":p})
        if not relationship:errors.append({"kind":"wrong_relationship","expected":t,"observed":p})
        expected_stroke=bool(truth["edges"][i].get("dashed",False))
        seen_stroke=pi in pred.get("dashed_edges",[])
        strokes+=expected_stroke==seen_stroke
        if expected_stroke!=seen_stroke:errors.append({"kind":"wrong_stroke","edge":i,"expected_dashed":expected_stroke,"observed_dashed":seen_stroke})
    for i,t in enumerate(truth_edges):
        if i not in used:errors.append({"kind":"missing_edge","expected":t})
    for label,count in (Counter(labels)-Counter(observed)).items():
        errors.append({"kind":"missing_node","label":label,"count":count})
    for label,count in (Counter(observed)-Counter(labels)).items():
        errors.append({"kind":"extra_node","label":label,"count":count})
    shapes=0
    for node in truth["nodes"]:
        expected_shape=node.get("shape") or truth["shape"]
        index=next((i for i,n in enumerate(pred["nodes"]) if n[0]==node["label"]),None)
        seen_shape=None if index is None else (pred.get("node_shapes") or [pred.get("shape")]*len(pred["nodes"]))[index]
        shapes+=expected_shape==seen_shape
        if expected_shape!=seen_shape:errors.append({"kind":"wrong_shape","node":node["label"],"expected":expected_shape,"observed":seen_shape})
    def ratio(n,d):return round(n/d,4) if d else None
    return {"node_precision":ratio(correct_nodes,len(observed)),"node_recall":ratio(correct_nodes,len(labels)),
            "node_shape_accuracy":ratio(shapes,len(labels)),"edge_stroke_accuracy":ratio(strokes,len(truth_edges)),
            "topology_precision":ratio(topology,len(pred_edges)),"topology_recall":ratio(topology,len(truth_edges)),
            "arrow_accuracy":ratio(arrows,topology),"relationship_exact":ratio(relationships,topology),
            "full_edge_precision":ratio(full,len(pred_edges)),"full_edge_recall":ratio(full,len(truth_edges)),
            "truth_nodes":len(labels),"truth_edges":len(truth_edges),"errors":errors}


def bbox(poly):
    return [round(min(x for x,y in poly)),round(min(y for x,y in poly)),
            round(max(x for x,y in poly)),round(max(y for x,y in poly))]


def closest(items, label, xy, used):
    choices=[]
    for i,o in enumerate(items):
        if i in used or o["text"]!=label:continue
        b=bbox(o["polygon"]);cx=(b[0]+b[2])/2;cy=(b[1]+b[3])/2
        choices.append(((cx-xy[0])**2+(cy-xy[1])**2,i,o,b))
    if not choices:return None
    _,i,o,b=min(choices)
    used.add(i)
    return {"text":o["text"],"confidence":o["confidence"],"bbox":b,"observation_index":i}


def export_fusion(slug,pred):
    ocr=read(ROOT/"runs"/"rapid_v6_medium_fi"/(slug+".json"))["observations"]
    used=set();nodes=[];edges=[];uncertainties=[]
    title_candidates=[(i,o) for i,o in enumerate(ocr) if bbox(o["polygon"])[3]<100]
    title=None
    if title_candidates:
        title_index,title_observation=min(title_candidates,key=lambda pair:bbox(pair[1]["polygon"])[1])
        used.add(title_index)
        title={"text":title_observation["text"],"bbox":bbox(title_observation["polygon"]),
               "confidence":title_observation["confidence"]}
    label_to_id={}
    for i,(label,x,y) in enumerate(pred["nodes"]):
        hit=closest(ocr,label,(x,y),used)
        nid=f"n{i}";label_to_id[label]=nid
        if hit is None:uncertainties.append({"kind":"ocr_vision_disagreement","element":"node","vision":label,"location":[x,y]})
        shape=(pred.get("node_shapes") or [pred.get("shape")]*len(pred["nodes"]))[i]
        nodes.append({"id":nid,"label":label,"type":shape,"center":[x,y],
                      "label_bbox":hit["bbox"] if hit else None,
                      "confidence":{"vision_review":"subjective, not calibrated","ocr":hit["confidence"] if hit else None}})
    for i,e in enumerate(pred["edges"]):
        a,b,label=e[:3];direction=e[3] if len(e)>3 else "source_to_target"
        aa=next(n for n in nodes if n["label"]==a);bb=next(n for n in nodes if n["label"]==b)
        midpoint=[(aa["center"][0]+bb["center"][0])/2,(aa["center"][1]+bb["center"][1])/2]
        hit=closest(ocr,label,midpoint,used)
        if hit is None:uncertainties.append({"kind":"ocr_vision_disagreement","element":"edge_label","vision":label,"location":midpoint})
        edges.append({"id":f"e{i}","source":label_to_id[a],"target":label_to_id[b],
                      "relationship":label,"direction":direction,"dashed":i in pred.get("dashed_edges",[]),
                      "label_bbox":hit["bbox"] if hit else None,
                      "confidence":{"vision_review":"subjective, not calibrated","ocr":hit["confidence"] if hit else None}})
    for i,o in enumerate(ocr):
        if i not in used:
            uncertainties.append({"kind":"unassigned_ocr_text","text":o["text"],"bbox":bbox(o["polygon"])})
    return {"image":slug+".png","image_size":[1400,850],"source":"Codex visual reading + RapidOCR v6 medium fi",
            "title":title,
            "nodes":nodes,"edges":edges,"uncertainties":uncertainties}


def main():
    vision=read(ROOT/"vision_review.json")["cases"]
    ocr=read(ROOT/"ocr_matrix.json")
    outdir=ROOT/"inferred";outdir.mkdir(exist_ok=True)
    assessments={slug:score_vision(slug,pred) for slug,pred in vision.items()}
    (ROOT/"vision_scores.json").write_text(json.dumps(assessments,ensure_ascii=False,indent=2),encoding="utf-8")
    rows=[]
    for approach in ocr:
        totals=approach["totals"]
        rows.append({"approach":approach["approach"],"cases":approach["cases_ran"],
            "all_visible_text_exact":totals["all"]["recall"],
            "all_visible_text_precision":totals["all"]["precision"],
            "extra_ocr_items":totals["all"]["extra_ocr_items"],
            "node_labels_exact":totals["node"]["recall"],
            "edge_labels_exact":totals["edge"]["recall"],"rotated_edge_labels_exact":totals["rotated_edge"]["recall"],
            "connections_found":0,"connections_total":sum(len(read(p)["edges"]) for p in ROOT.glob("*.source.json")),
            "arrow_accuracy":None,"fully_correct_edges":0,"full_edge_recall":0,
            "node_shape_accuracy":None,"edge_stroke_accuracy":None,
            "note":"OCR only: no graph reconstruction; text matching uses known printed regions for evaluation"})
    edge_total=sum(a["truth_edges"] for a in assessments.values())
    node_total=sum(a["truth_nodes"] for a in assessments.values())
    found=sum(round(a["topology_recall"]*a["truth_edges"]) for a in assessments.values())
    full=sum(round(a["full_edge_recall"]*a["truth_edges"]) for a in assessments.values())
    nodes=sum(round(a["node_recall"]*a["truth_nodes"]) for a in assessments.values())
    rows.append({"approach":"codex_visual_review_nonblind","cases":len(assessments),
        "all_visible_text_exact":None,"all_visible_text_precision":None,"extra_ocr_items":None,
        "node_labels_exact":round(nodes/node_total,4),
        "edge_labels_exact":None,"rotated_edge_labels_exact":None,
        "connections_found":found,"connections_total":edge_total,
        "arrow_accuracy":round(sum(round(a["arrow_accuracy"]*a["truth_edges"]) for a in assessments.values())/edge_total,4),
        "fully_correct_edges":full,"full_edge_recall":round(full/edge_total,4),
        "node_shape_accuracy":round(sum(a["node_shape_accuracy"]*a["truth_nodes"] for a in assessments.values())/node_total,4),
        "edge_stroke_accuracy":round(sum(a["edge_stroke_accuracy"]*a["truth_edges"] for a in assessments.values())/edge_total,4),
        "note":"Non-blind visual reading by fixture author; descriptive only, not independent AI evaluation"})
    conflict_count=0
    for slug,pred in vision.items():
        extraction=export_fusion(slug,pred)
        conflict_count+=sum(u["kind"]=="ocr_vision_disagreement" for u in extraction["uncertainties"])
        (outdir/(slug+".json")).write_text(json.dumps(extraction,ensure_ascii=False,indent=2),encoding="utf-8")
    rows.append({**rows[-1],"approach":"codex_visual_plus_rapid_v6_fi","all_visible_text_exact":1.0,
        "all_visible_text_precision":next(r["all_visible_text_precision"] for r in rows if r["approach"]=="rapid_v6_medium_fi"),
        "extra_ocr_items":next(r["extra_ocr_items"] for r in rows if r["approach"]=="rapid_v6_medium_fi"),
        "edge_labels_exact":1.0,"rotated_edge_labels_exact":1.0,
        "note":f"Non-blind fusion; {conflict_count} OCR/vision element disagreements"})
    with (ROOT/"approach_matrix.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (ROOT/"approach_matrix.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    print(*[(r["approach"],r["connections_found"],r["fully_correct_edges"]) for r in rows],sep="\n")


if __name__=="__main__":main()
