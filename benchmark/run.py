"""Run available OCR and reviewed-vision approaches, then write a score matrix."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import cv2
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / ".vendor"))
sys.path.insert(0, str(ROOT.parent))
from rapidocr_onnxruntime import RapidOCR
from graph_extract import reconcile
from benchmark.evaluate import evaluate, load


def dump(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def boxes(image_path: Path) -> list[list[int]]:
    image = cv2.imread(str(image_path))
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv,(0,25,60),(179,255,255))
    contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    found=[]
    for contour in contours:
        if cv2.contourArea(contour) < 3000:
            continue
        x,y,w,h=cv2.boundingRect(contour)
        if 100 <= w <= 300 and 50 <= h <= 120:
            found.append([x,y,x+w,y+h])
    return sorted(found,key=lambda b:(b[1],b[0]))


def recognize(engine: RapidOCR, image) -> list[dict]:
    result,_=engine(image)
    found=[]
    for poly,text,confidence in result or []:
        found.append({"polygon":poly,"text":text,"confidence":float(confidence),
                      "bbox":[int(min(p[0] for p in poly)),int(min(p[1] for p in poly)),
                              int(max(p[0] for p in poly)),int(max(p[1] for p in poly))]})
    return found


def inside(box: list[int], o: dict) -> bool:
    a=o["bbox"]
    x,y=(a[0]+a[2])/2,(a[1]+a[3])/2
    return box[0]+3 <= x <= box[2]-3 and box[1]+3 <= y <= box[3]-3


def ocr_full(engine: RapidOCR, image: Path) -> tuple[dict,dict]:
    observations=recognize(engine,str(image))
    found=[]
    for i,box in enumerate(boxes(image)):
        parts=sorted([o for o in observations if inside(box,o)],key=lambda o:(o["bbox"][1],o["bbox"][0]))
        found.append({"id":f"box{i}","label":" ".join(o["text"] for o in parts),
                      "type":"colored_rectangle","bbox":box,
                      "confidence":min([o["confidence"] for o in parts],default=0.0)})
    return {"nodes":found,"edges":[],"source":"rapidocr_full",
            "visible_text":[o["text"] for o in observations]},{"image_size":[1200,700],"engine":"rapidocr_full","observations":observations}


def ocr_crops(engine: RapidOCR, image: Path) -> tuple[dict,dict]:
    original=Image.open(image).convert("RGB")
    found=[]; observations=[]
    for i,box in enumerate(boxes(image)):
        x1,y1,x2,y2=box
        crop=original.crop((x1+5,y1+5,x2-5,y2-5)).resize(((x2-x1-10)*2,(y2-y1-10)*2))
        detected=recognize(engine,cv2.cvtColor(__import__('numpy').array(crop),cv2.COLOR_RGB2BGR))
        for o in detected:
            o["bbox"]=[round(x1+5+o["bbox"][0]/2),round(y1+5+o["bbox"][1]/2),
                       round(x1+5+o["bbox"][2]/2),round(y1+5+o["bbox"][3]/2)]
            observations.append(o)
        parts=sorted(detected,key=lambda o:(o["bbox"][1],o["bbox"][0]))
        found.append({"id":f"box{i}","label":" ".join(o["text"] for o in parts),
                      "type":"colored_rectangle","bbox":box,
                      "confidence":min([o["confidence"] for o in parts],default=0.0)})
    return {"nodes":found,"edges":[],"source":"rapidocr_crops",
            "visible_text":[o["text"] for o in observations]},{"image_size":[1200,700],"engine":"rapidocr_crops","observations":observations}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',nargs='*',help='Optional case IDs')
    args=parser.parse_args()
    manifest=load(ROOT/'manifest.json')
    if args.only:
        manifest=[case for case in manifest if case['id'] in args.only]
    engine=RapidOCR()
    approaches=['rapidocr_full','rapidocr_crops','codex_vision','codex_plus_rapidocr']
    records={a:{} for a in approaches}
    for case in manifest:
        name=case['id']; image=ROOT/case['image']; truth=load(ROOT/case['truth'])
        full,full_ocr=ocr_full(engine,image)
        crops,crops_ocr=ocr_crops(engine,image)
        for approach,pred,raw in [('rapidocr_full',full,full_ocr),('rapidocr_crops',crops,crops_ocr)]:
            dump(ROOT/'runs'/approach/f'{name}.graph.json',pred)
            dump(ROOT/'runs'/approach/f'{name}.raw.json',raw)
            result=evaluate(pred,truth)
            dump(ROOT/'runs'/approach/f'{name}.errors.json',result)
            records[approach][name]=result['metrics']
        reviewed=ROOT/'reviewed'/f'{name}.json'
        if reviewed.exists():
            vision=load(reviewed)
            fusion=reconcile(full_ocr,vision)
            fusion["visible_text"]=[vision["rendered_title"]]+[n["label"] for n in fusion["nodes"]]+[
                e["relationship"] for e in fusion["edges"] if e["relationship"]!="unknown"]
            for approach,pred in [('codex_vision',vision),('codex_plus_rapidocr',fusion)]:
                dump(ROOT/'runs'/approach/f'{name}.graph.json',pred)
                result=evaluate(pred,truth)
                dump(ROOT/'runs'/approach/f'{name}.errors.json',result)
                records[approach][name]=result['metrics']
        print(f'{name}: {len(truth["nodes"])} nodes, {len(truth["edges"])} edges')
    metrics=['node_precision','node_recall','node_text_exact','node_label_recall','node_cer','node_type_exact',
             'mean_bbox_iou','visible_text_precision','visible_text_recall','topology_precision',
             'topology_recall','arrow_accuracy','relationship_exact','full_edge_precision','full_edge_recall',
             'end_to_end_edge_precision','end_to_end_edge_recall']
    columns=['approach','cases_scored']+[f'{case["id"]}.{metric}' for case in manifest for metric in metrics]+[f'macro.{metric}' for metric in metrics]
    ROOT.joinpath('results').mkdir(exist_ok=True)
    with (ROOT/'results'/'matrix.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        for approach in approaches:
            row={'approach':approach,'cases_scored':len(records[approach])}
            for case in manifest:
                for metric in metrics:
                    row[f'{case["id"]}.{metric}']=records[approach].get(case['id'],{}).get(metric)
            for metric in metrics:
                values=[r[metric] for r in records[approach].values() if r[metric] is not None]
                row[f'macro.{metric}']=round(sum(values)/len(values),4) if values else None
            writer.writerow(row)
    dump(ROOT/'results'/'summary.json',{'approaches':records,'metrics':metrics,
         'note':'Blank matrix cells mean the approach was not run or has no defined denominator; never interpret blanks as zero.'})


if __name__=='__main__':
    main()
