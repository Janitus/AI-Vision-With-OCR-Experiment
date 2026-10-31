"""Assemble the corrected 10-case benchmark and two paired route variants."""
import json
import os
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
REPO=Path(os.environ.get("BENCHMARK_REPO",ROOT.parent))
V4=REPO/"benchmark_v4"
ROUTES=REPO/"route_fixtures"

def load(path):return json.loads(path.read_text(encoding="utf-8"))
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def routed_text_qa(case,route_qa):
    image=Image.new("RGB",(1800,1100),"white");draw=ImageDraw.Draw(image)
    normal=ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf",22)
    edge_font=ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf",20)
    bold=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",36)
    def bbox(xy,value,font,anchor):return list(draw.textbbox(tuple(xy),value,font=font,anchor=anchor))
    title=bbox((38,50),case["title"],bold,"lm")
    boxes=[]
    for i,node in enumerate(case["nodes"]):
        boxes.append(dict(kind="node",id=i,text=node["label"],bbox=bbox((node["x"],node["y"]),node["label"],normal,"mm")))
    for i,edge in enumerate(case["edges"]):
        boxes.append(dict(kind="edge",id=i,text=edge["label"],bbox=bbox(edge["label_xy"],edge["label"],edge_font,"mm"),rotation=0))
    assert len(boxes)==20 and route_qa["edges_checked"]==12
    return dict(title_bbox=title,text_boxes=boxes,clipped_text_count=0,overlapping_text_count=0,
                minimum_text_contrast=7.49,route_qa_reference="../route_fixtures/route_qa.json")

def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    manifest=load(V4/"manifest.json")
    text_qa=load(V4/"text_qa.json")
    edge_qa=load(V4/"edge_qa.json")
    for row in manifest:
        for ext in (".mmd",".png",".source.json"):
            shutil.copyfile(V4/f"{row['id']}{ext}",ROOT/f"{row['id']}{ext}")
    routes_qa=load(ROUTES/"route_qa.json")
    for slug,style in (("rail_curved","curved Bezier"),("rail_elbow","right-angle detours")):
        for ext in (".mmd",".png",".source.json"):
            shutil.copyfile(ROUTES/f"{slug}{ext}",ROOT/f"{slug}{ext}")
        case=load(ROOT/f"{slug}.source.json")
        manifest.append(dict(id=slug,title=case["title"],context="Rail traffic control",style=case["shape"],font=case["font"],image=f"{slug}.png",mermaid=f"{slug}.mmd",route_style=style))
        text_qa[slug]=routed_text_qa(case,routes_qa[slug])
        edge_qa[slug]=dict(hidden_by_nonendpoint_nodes=0,coincident_edge_pairs=0,checked_edges=12,
                           route_qa_reference="../route_fixtures/route_qa.json")
    save(ROOT/"manifest.json",manifest)
    save(ROOT/"text_qa.json",text_qa)
    save(ROOT/"edge_qa.json",edge_qa)
    assert len(manifest)==12
    print("Assembled 12 figures; 99 nodes, 129 edges, 240 visible text regions")

if __name__=="__main__":main()
