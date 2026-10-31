"""Draw two paired Finnish graph figures with routed arrows and geometric QA.

Both figures retain the same nodes, labels, and edge topology as the reviewed
v4 rail case. Only the edge route changes: cubic Bezier versus orthogonal.
The exact route is retained in source JSON; Mermaid records graph topology.
"""
from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
REPO=Path(os.environ.get("ROUTE_FIXTURE_REPO",ROOT.parent))
BASE=REPO/"benchmark_v4"/"junaliikenteen_ohjaus.source.json"
W,H=1800,1100
SCALE=2
FONT=Path("C:/Windows/Fonts/segoeui.ttf")
BOLD=Path("C:/Windows/Fonts/segoeuib.ttf")

# Commands are ["M" or "L", x, y] and ["C", c1x, c1y, c2x, c2y, x, y].
CURVED=[
  [["M",385,260],["C",430,150,500,150,545,260]],
  [["M",815,260],["C",865,145,940,145,985,260]],
  [["M",1255,260],["C",1300,150,1370,150,1415,260]],
  [["M",250,310],["C",100,420,100,680,250,780]],
  [["M",385,830],["C",430,970,500,970,545,830]],
  [["M",815,830],["C",860,970,940,970,985,830]],
  [["M",1255,830],["C",1300,970,1370,970,1415,830]],
  [["M",680,310],["C",780,430,780,650,680,780]],
  [["M",1120,310],["C",1020,430,1020,650,1120,780]],
  [["M",385,830],["C",470,570,860,390,985,260]],
  [["M",1550,310],["C",1695,420,1695,660,1550,780]],
  [["M",1255,830],["C",1420,680,1380,420,1550,310]],
]
ELBOW=[
  [["M",385,260],["L",420,260],["L",420,145],["L",510,145],["L",510,260],["L",545,260]],
  [["M",815,260],["L",850,260],["L",850,125],["L",950,125],["L",950,260],["L",985,260]],
  [["M",1255,260],["L",1290,260],["L",1290,145],["L",1380,145],["L",1380,260],["L",1415,260]],
  [["M",250,310],["L",250,390],["L",80,390],["L",80,700],["L",250,700],["L",250,780]],
  [["M",385,830],["L",420,830],["L",420,965],["L",510,965],["L",510,830],["L",545,830]],
  [["M",815,830],["L",850,830],["L",850,965],["L",950,965],["L",950,830],["L",985,830]],
  [["M",1255,830],["L",1290,830],["L",1290,965],["L",1380,965],["L",1380,830],["L",1415,830]],
  [["M",680,310],["L",680,380],["L",810,380],["L",810,690],["L",680,690],["L",680,780]],
  [["M",1120,310],["L",1120,380],["L",990,380],["L",990,690],["L",1120,690],["L",1120,780]],
  [["M",300,780],["L",300,610],["L",920,610],["L",920,350],["L",1002.5,350],["L",1002.5,260]],
  [["M",1550,310],["L",1550,380],["L",1730,380],["L",1730,700],["L",1550,700],["L",1550,780]],
  [["M",1170,780],["L",1170,540],["L",1500,540],["L",1500,310]],
]
LABEL_CURVED=[(465,160),(900,155),(1335,160),(100,545),(465,958),(900,958),(1335,958),(790,515),(1010,515),(500,615),(1700,555),(1435,510)]
LABEL_ELBOW=[(465,125),(900,125),(1335,125),(110,545),(465,985),(900,985),(1335,985),(820,530),(980,530),(680,585),(1690,550),(1435,515)]


def points(commands):
    result=[]
    at=None
    for command in commands:
        kind=command[0]
        if kind=="M":
            at=(command[1],command[2]);result.append(at)
        elif kind=="L":
            end=(command[1],command[2]);length=math.dist(at,end)
            result.extend((at[0]+(end[0]-at[0])*t/length,at[1]+(end[1]-at[1])*t/length) for t in range(2,int(length)+1,2))
            result.append(end);at=end
        elif kind=="C":
            c1=(command[1],command[2]);c2=(command[3],command[4]);end=(command[5],command[6])
            for n in range(1,201):
                t=n/200;u=1-t
                result.append((u*u*u*at[0]+3*u*u*t*c1[0]+3*u*t*t*c2[0]+t*t*t*end[0],
                               u*u*u*at[1]+3*u*u*t*c1[1]+3*u*t*t*c2[1]+t*t*t*end[1]))
            at=end
        else:raise ValueError(kind)
    return result


def node_box(node):
    x,y=node["x"],node["y"]
    return (x-node["w"]/2,y-node["h"]/2,x+node["w"]/2,y+node["h"]/2)


def snap_to_boundary(node,point):
    """Place a route endpoint on the nearest boundary of its own node."""
    x1,y1,x2,y2=node_box(node);x,y=point
    choices=[(x1,min(max(y,y1),y2)),(x2,min(max(y,y1),y2)),
             (min(max(x,x1),x2),y1),(min(max(x,x1),x2),y2)]
    return min(choices,key=lambda p:math.dist(p,point))


def text_rect(draw,center,value,font,padding=6):
    box=draw.textbbox(center,value,font=font,anchor="mm")
    return (box[0]-padding,box[1]-padding,box[2]+padding,box[3]+padding)


def intersects(a,b):
    return a[0]<b[2] and a[2]>b[0] and a[1]<b[3] and a[3]>b[1]


def shared_straight_pixels(first,second):
    """Length of coincident horizontal/vertical path segments."""
    if any(command[0]=="C" for command in first+second):return 0
    def segments(route):
        return [((a[-2],a[-1]),(b[-2],b[-1])) for a,b in zip(route,route[1:])]
    longest=0
    for (ax,ay),(bx,by) in segments(first):
        for (cx,cy),(dx,dy) in segments(second):
            if ay==by==cy==dy:
                longest=max(longest,max(0,min(max(ax,bx),max(cx,dx))-max(min(ax,bx),min(cx,dx))))
            if ax==bx==cx==dx:
                longest=max(longest,max(0,min(max(ay,by),max(cy,dy))-max(min(ay,by),min(cy,dy))))
    return longest


def check(case,paths,labels):
    assert len(paths)==len(labels)==len(case["edges"])
    for i,route in enumerate(paths):
        for j in range(i):
            shared=shared_straight_pixels(route,paths[j])
            if shared>20:
                raise ValueError(f"Edges {j} and {i} share {shared:.1f}px of route")
    image=Image.new("RGB",(W,H),"white");draw=ImageDraw.Draw(image)
    label_font=ImageFont.truetype(str(FONT),20)
    node_font=ImageFont.truetype(str(FONT),22)
    title_font=ImageFont.truetype(str(BOLD),36)
    title_box=draw.textbbox((38,50),case["title"],font=title_font,anchor="lm")
    if title_box[0]<10 or title_box[1]<10 or title_box[2]>W-10 or title_box[3]>100:
        raise ValueError("Title is clipped")
    text_boxes=[title_box]
    node_boxes=[node_box(n) for n in case["nodes"]]
    for node,box in zip(case["nodes"],node_boxes):
        label_box=text_rect(draw,(node["x"],node["y"]),node["label"],node_font)
        if not (box[0]+8<label_box[0] and label_box[2]<box[2]-8 and
                box[1]+8<label_box[1] and label_box[3]<box[3]-8):
            raise ValueError(f"Node label does not fit: {node['label']}")
        text_boxes.append(label_box)
    label_distances=[]
    for index,(edge,route,xy) in enumerate(zip(case["edges"],paths,labels)):
        sampled=points(route)
        for node_index,box in enumerate(node_boxes):
            if node_index in (edge["source"],edge["target"]):continue
            padded=(box[0]-7,box[1]-7,box[2]+7,box[3]+7)
            if any(padded[0]<x<padded[2] and padded[1]<y<padded[3] for x,y in sampled):
                raise ValueError(f"Edge {index} crosses unrelated node {node_index}")
        for endpoint,node_index in ((sampled[0],edge["source"]),(sampled[-1],edge["target"])):
            box=node_boxes[node_index]
            if not (box[0]-2<=endpoint[0]<=box[2]+2 and box[1]-2<=endpoint[1]<=box[3]+2):
                raise ValueError(f"Edge {index} does not meet endpoint node {node_index}")
        rect=text_rect(draw,xy,edge["label"],label_font)
        label_distance=min(math.dist(xy,p) for p in sampled)
        if label_distance>50:
            raise ValueError(f"Edge label {index} is too far from its route: {label_distance:.1f}px")
        label_distances.append(round(label_distance,1))
        if rect[0]<10 or rect[1]<100 or rect[2]>W-10 or rect[3]>H-10:
            raise ValueError(f"Edge label {index} clipped")
        if any(intersects(rect,box) for box in node_boxes):
            raise ValueError(f"Edge label {index} overlaps a node")
        if any(intersects(rect,box) for box in text_boxes):
            raise ValueError(f"Edge label {index} overlaps another label")
        text_boxes.append(rect)
    return {"edges_checked":len(paths),"unrelated_node_obstructions":0,"clipped_labels":0,
            "overlapping_labels":0,"coincident_straight_segments":0,"label_path_distances_px":label_distances,
            "label_boxes":[list(map(float,box)) for box in text_boxes]}


def draw_arrow(draw,path,color):
    tip=path[-1];before=path[-8]
    angle=math.atan2(tip[1]-before[1],tip[0]-before[0]);size=18
    polygon=[tip,(tip[0]-size*math.cos(angle-.45),tip[1]-size*math.sin(angle-.45)),
             (tip[0]-size*math.cos(angle+.45),tip[1]-size*math.sin(angle+.45))]
    draw.polygon([(round(x*SCALE),round(y*SCALE)) for x,y in polygon],fill=color)


def draw_case(case,paths,labels,path):
    background="#ffffff";edge_color="#386f95";ink="#17324b"
    image=Image.new("RGB",(W*SCALE,H*SCALE),background);draw=ImageDraw.Draw(image)
    font=ImageFont.truetype(str(FONT),22*SCALE)
    edge_font=ImageFont.truetype(str(FONT),20*SCALE)
    title_font=ImageFont.truetype(str(BOLD),36*SCALE)
    for edge,route in zip(case["edges"],paths):
        line=points(route)
        scaled=[(round(x*SCALE),round(y*SCALE)) for x,y in line]
        if edge.get("dashed"):
            for j in range(0,len(scaled)-1,7):
                draw.line(scaled[j:j+4],fill=edge_color,width=3*SCALE,joint="curve")
        else:draw.line(scaled,fill=edge_color,width=3*SCALE,joint="curve")
        if edge["direction"]=="source_to_target":draw_arrow(draw,line,edge_color)
        elif edge["direction"]=="both":
            draw_arrow(draw,line,edge_color);draw_arrow(draw,list(reversed(line)),edge_color)
    colors=["#e6f2ff","#e5f6ed","#fff1d8","#eee5f9"]
    for i,node in enumerate(case["nodes"]):
        box=node_box(node)
        draw.rounded_rectangle(tuple(round(v*SCALE) for v in box),radius=48*SCALE,
                               fill=colors[i%len(colors)],outline=ink,width=2*SCALE)
        draw.text((node["x"]*SCALE,node["y"]*SCALE),node["label"],font=font,fill=ink,anchor="mm")
    for edge,xy in zip(case["edges"],labels):
        center=(xy[0]*SCALE,xy[1]*SCALE)
        box=draw.textbbox(center,edge["label"],font=edge_font,anchor="mm")
        draw.rounded_rectangle((box[0]-8*SCALE,box[1]-4*SCALE,box[2]+8*SCALE,box[3]+4*SCALE),
                               radius=5*SCALE,fill=background)
        draw.text(center,edge["label"],font=edge_font,fill=ink,anchor="mm")
    draw.text((38*SCALE,50*SCALE),case["title"],font=title_font,fill=ink,anchor="lm")
    image.resize((W,H),Image.Resampling.LANCZOS).save(path)


def mermaid(case,variant):
    lines=[f"%% Paired route fixture: {variant}; exact paths are in .source.json","flowchart LR"]
    for i,node in enumerate(case["nodes"]):
        label=node["label"].replace('"','&quot;')
        lines.append(f'  n{i}(["{label}"])')
    for edge in case["edges"]:
        a,b=edge["source"],edge["target"]
        arrow="---" if edge["direction"]=="undirected" else "-->"
        label=edge["label"].replace("|","&#124;")
        lines.append(f"  n{a} {arrow}|{label}| n{b}")
    return "\n".join(lines)+"\n"


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    original=json.loads(BASE.read_text(encoding="utf-8"))
    qa={};manifest=[]
    for slug,kind,paths,labels in (("rail_curved","cubic Bezier",CURVED,LABEL_CURVED),
                                   ("rail_elbow","orthogonal detours",ELBOW,LABEL_ELBOW)):
        case=copy.deepcopy(original)
        case["id"]=slug
        case["route_style"]=kind
        paths=copy.deepcopy(paths)
        for edge,route in zip(case["edges"],paths):
            x,y=snap_to_boundary(case["nodes"][edge["source"]],route[0][1:3])
            route[0][1:3]=[x,y]
            x,y=snap_to_boundary(case["nodes"][edge["target"]],route[-1][-2:])
            route[-1][-2:]=[x,y]
        case["edges"]=[{**edge,"route":route,"label_xy":list(xy)} for edge,route,xy in zip(case["edges"],paths,labels)]
        qa[slug]=check(case,paths,labels)
        draw_case(case,paths,labels,ROOT/f"{slug}.png")
        (ROOT/f"{slug}.source.json").write_text(json.dumps(case,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        (ROOT/f"{slug}.mmd").write_text(mermaid(case,kind),encoding="utf-8")
        manifest.append({"id":slug,"title":case["title"],"route_style":kind,"image":f"{slug}.png",
                         "source_json":f"{slug}.source.json","mermaid":f"{slug}.mmd"})
    (ROOT/"route_qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Generated",len(manifest),"paired fixtures; checked",sum(q["edges_checked"] for q in qa.values()),"edge routes")


if __name__=="__main__":main()
