"""Render saved blind predictions and a side-by-side, offline comparison viewer."""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = "C:/Windows/Fonts/segoeui.ttf"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def arrow(draw, tip, start, color):
    angle = math.atan2(tip[1]-start[1], tip[0]-start[0])
    size = 14
    draw.polygon([tip,
        (tip[0]-size*math.cos(angle-.5),tip[1]-size*math.sin(angle-.5)),
        (tip[0]-size*math.cos(angle+.5),tip[1]-size*math.sin(angle+.5))],fill=color)


def render(graph,path):
    image=Image.new("RGB",(1800,1100),"#ffffff")
    draw=ImageDraw.Draw(image)
    font=ImageFont.truetype(FONT,21)
    titlefont=ImageFont.truetype(FONT_BOLD,34)
    nodes={str(n["id"]):n for n in graph.get("nodes",[]) if isinstance(n.get("center"),list) and len(n["center"])==2}
    dims={}
    for key,n in nodes.items():
        text=str(n.get("label") or "unknown")
        bbox=draw.textbbox((0,0),text,font=font)
        dims[key]=(max(160,bbox[2]-bbox[0]+34),72)
    def point(a,b):
        x,y=a["center"];ox,oy=b["center"]
        dx,dy=ox-x,oy-y
        w,h=dims[str(a["id"])]
        t=min(w/2/abs(dx) if dx else 1e6,h/2/abs(dy) if dy else 1e6)
        return (x+dx*t,y+dy*t)
    drawn_edges=[]
    for e in graph.get("edges",[]):
        a=nodes.get(str(e.get("source")));b=nodes.get(str(e.get("target")))
        if not a or not b or a is b:continue
        p,q=point(a,b),point(b,a)
        color="#bf681c" if e.get("direction")=="unknown" else "#47738c"
        length=math.dist(p,q)
        if e.get("dashed") and length>0:
            for s in range(0,int(length),24):
                t=min(s+13,length)
                draw.line([(p[0]+(q[0]-p[0])*s/length,p[1]+(q[1]-p[1])*s/length),
                           (p[0]+(q[0]-p[0])*t/length,p[1]+(q[1]-p[1])*t/length)],fill=color,width=3)
        else:draw.line([p,q],fill=color,width=3)
        direction=e.get("direction")
        if direction in ("source_to_target","both"):arrow(draw,q,p,color)
        if direction in ("target_to_source","both"):arrow(draw,p,q,color)
        drawn_edges.append((e,p,q))
    for key,n in nodes.items():
        x,y=n["center"];w,h=dims[key]
        box=(x-w/2,y-h/2,x+w/2,y+h/2)
        kind=str(n.get("type") or "unknown").lower().replace("-","_")
        if kind in ("text","text_only","unboxed","no_box","plain"):
            draw.rectangle(box,fill="white")
        elif kind in ("round","rounded_rectangle","rounded_box","pill","capsule"):
            draw.rounded_rectangle(box,radius=h/2 if kind in ("pill","capsule") else 20,fill="#e9f2f8",outline="#294b60",width=2)
        elif kind in ("circle","ellipse","oval"):
            draw.ellipse(box,fill="#e9f2f8",outline="#294b60",width=2)
        elif kind=="diamond":
            draw.polygon([(x,y-h/2),(x+w/2,y),(x,y+h/2),(x-w/2,y)],fill="#e9f2f8")
            draw.line([(x,y-h/2),(x+w/2,y),(x,y+h/2),(x-w/2,y),(x,y-h/2)],fill="#294b60",width=2)
        else:draw.rectangle(box,fill="#e9f2f8",outline="#294b60",width=2)
        draw.text((x,y),str(n.get("label") or "unknown"),font=font,fill="#173247",anchor="mm")
    for e,p,q in drawn_edges:
        label=str(e.get("relationship") or "unknown")
        if e.get("direction")=="unknown":label+=" [?]"
        x=(p[0]+q[0])/2;y=(p[1]+q[1])/2-18
        box=draw.textbbox((x,y),label,font=font,anchor="mm")
        draw.rectangle((box[0]-7,box[1]-4,box[2]+7,box[3]+4),fill="white")
        draw.text((x,y),label,font=font,fill="#173247",anchor="mm")
    draw.text((38,30),str(graph.get("title") or "unknown"),font=titlefont,fill="#173247")
    image.save(path)


def mermaid(graph):
    lines=["flowchart LR"]
    for n in graph.get("nodes",[]):
        node_id=str(n["id"])
        label=str(n.get("label") or "unknown").replace('"','&quot;')
        shape=str(n.get("type") or "box").lower()
        bracket={"round":f'("{label}")',"rounded_rectangle":f'("{label}")',
                 "pill":f'(["{label}"])',"circle":f'(("{label}"))',
                 "diamond":f'{{"{label}"}}',"hex":f'{{{{"{label}"}}}}'}.get(shape,f'["{label}"]')
        lines.append(f"  {node_id}{bracket}")
        if shape in ("text","text_only","unboxed","plain"):lines.append(f"  style {node_id} fill:none,stroke:none")
    for index,e in enumerate(graph.get("edges",[])):
        direction=e.get("direction")
        stroke="---" if direction in ("undirected","unknown") else ("<-->" if direction=="both" else "-->")
        if direction=="target_to_source":a,b=e.get("target"),e.get("source")
        else:a,b=e.get("source"),e.get("target")
        label=str(e.get("relationship") or "unknown").replace("|","&#124;")
        if direction=="unknown":label+=" [direction unknown]"
        lines.append(f"  {a} {stroke}|{label}| {b}")
        if e.get("dashed"):lines.append(f"  linkStyle {index} stroke-dasharray: 8 5")
    return "\n".join(lines)+"\n"


def main():
    mapping=load(ROOT/"blind_mapping.json")
    entries=[]
    for case,slug in mapping.items():
        item={"case":case,"slug":slug,"title":load(ROOT/f"{slug}.source.json")["title"],"source":f"{slug}.png"}
        for approach in ("blind_vision","blind_fusion"):
            graph=load(ROOT/approach/"predictions"/f"{case}.json")
            out=ROOT/approach/"rendered";out.mkdir(exist_ok=True)
            render(graph,out/f"{case}.png")
            (out/f"{case}.mmd").write_text(mermaid(graph),encoding="utf-8")
            item[approach]=f"{approach}/rendered/{case}.png"
            item[approach+"_uncertainties"]=graph.get("uncertainties",[])
        entries.append(item)
    data=json.dumps(entries,ensure_ascii=True).replace("</","<\\/")
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Blind graph benchmark v3</title>
<style>body{font:16px system-ui;background:#f5f7fa;color:#172d3c;margin:20px}main{max-width:1900px;margin:auto}select{font:inherit;padding:8px}section{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:16px}figure{margin:0;background:white;border:1px solid #b9c5cd;padding:7px}img{width:100%;height:auto;display:block}figcaption{font-weight:700;padding:5px}pre{white-space:pre-wrap}a{color:#145889}</style>
<main><h1>Finnish graph extraction: ten blind cases</h1><p>Source image, blind Codex vision, and blind Codex vision with raw RapidOCR. Select a case to inspect literal text and connections. Prediction renderings use a neutral style; orange lines marked [?] mean the prediction gave an unknown direction. Consult the saved JSON for coordinates, confidence, and uncertainties.</p><label>Case <select id="choose"></select></label><section><figure><figcaption>Source</figcaption><img id="source"></figure><figure><figcaption>Vision only</figcaption><img id="vision"></figure><figure><figcaption>Vision + OCR</figcaption><img id="fusion"></figure></section><p id="issues"></p><p><a href="REPORT.md">Validation report</a> · <a href="matrix_viewer.html">Readable approach matrix</a> · <a href="approach_matrix.csv" download>Full CSV</a> · <a href="item_error_ledger.json">Item-level errors</a></p></main>
<script>const cases=__DATA__,sel=document.querySelector('#choose');cases.forEach((e,i)=>{let o=document.createElement('option');o.value=i;o.textContent=`${i+1}. ${e.title}`;sel.append(o)});function show(){let e=cases[+sel.value];document.querySelector('#source').src=e.source;document.querySelector('#vision').src=e.blind_vision;document.querySelector('#fusion').src=e.blind_fusion;document.querySelector('#issues').textContent=`Vision uncertainties: ${e.blind_vision_uncertainties.length}; fusion uncertainties: ${e.blind_fusion_uncertainties.length}.`;}sel.onchange=show;show();</script></html>'''.replace("__DATA__",data)
    (ROOT/"results_viewer.html").write_text(page,encoding="utf-8")
    print("Exported",len(entries),"side-by-side cases")


if __name__=="__main__":main()
