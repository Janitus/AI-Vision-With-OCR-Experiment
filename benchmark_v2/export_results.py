"""Export inferred Mermaid and a simple image-only comparison viewer."""
import base64
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"inferred"


def read(path):return json.loads(path.read_text(encoding="utf-8"))


def render_graph(graph,path):
    image=Image.new("RGB",(1400,850),"#ffffff")
    draw=ImageDraw.Draw(image)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",22)
    titlefont=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf",31)
    nodes={n["id"]:n for n in graph["nodes"]}
    dims={}
    for n in graph["nodes"]:
        box=draw.textbbox((0,0),n["label"],font=font)
        dims[n["id"]]=(max(130,box[2]-box[0]+40),62)
    def endpoint(node,other):
        x,y=node["center"];ox,oy=other["center"]
        dx,dy=ox-x,oy-y;w,h=dims[node["id"]]
        scale=min((w/2)/abs(dx) if dx else 1e6,(h/2)/abs(dy) if dy else 1e6)
        return (x+dx*scale,y+dy*scale)
    for edge in graph["edges"]:
        a,b=nodes[edge["source"]],nodes[edge["target"]]
        p=endpoint(a,b);q=endpoint(b,a)
        if edge.get("dashed"):
            length=math.dist(p,q)
            for start in range(0,round(length),22):
                stop=min(start+12,length)
                a0=(p[0]+(q[0]-p[0])*start/length,p[1]+(q[1]-p[1])*start/length)
                a1=(p[0]+(q[0]-p[0])*stop/length,p[1]+(q[1]-p[1])*stop/length)
                draw.line((a0,a1),fill="#46627a",width=3)
        else:
            draw.line((p,q),fill="#46627a",width=3)
        if edge["direction"]=="source_to_target":
            ang=math.atan2(q[1]-p[1],q[0]-p[0]);size=15
            left=(q[0]-size*math.cos(ang-0.5),q[1]-size*math.sin(ang-0.5))
            right=(q[0]-size*math.cos(ang+0.5),q[1]-size*math.sin(ang+0.5))
            draw.polygon((q,left,right),fill="#46627a")
    for n in graph["nodes"]:
        x,y=n["center"];w,h=dims[n["id"]]
        shape=n["type"]
        box=(x-w/2,y-h/2,x+w/2,y+h/2)
        if shape=="box":draw.rectangle(box,fill="#e8f3fa",outline="#35536c",width=2)
        elif shape=="text":pass
        elif shape=="circle":draw.ellipse(box,fill="#e8f3fa",outline="#35536c",width=2)
        elif shape=="diamond":draw.polygon([(x,y-h/2),(x+w/2,y),(x,y+h/2),(x-w/2,y)],fill="#e8f3fa",outline="#35536c",width=2)
        elif shape=="hex":draw.polygon([(x-w*.32,y-h/2),(x+w*.32,y-h/2),(x+w/2,y),(x+w*.32,y+h/2),(x-w*.32,y+h/2),(x-w/2,y)],fill="#e8f3fa",outline="#35536c",width=2)
        else:draw.rounded_rectangle(box,radius=31 if shape=="pill" else 13,fill="#e8f3fa",outline="#35536c",width=2)
        draw.text((x,y),n["label"],font=font,fill="#102c40",anchor="mm")
    for edge in graph["edges"]:
        b=edge["label_bbox"]
        if b:
            x=(b[0]+b[2])/2;y=(b[1]+b[3])/2
        else:
            a=nodes[edge["source"]]["center"];z=nodes[edge["target"]]["center"]
            x=(a[0]+z[0])/2;y=(a[1]+z[1])/2-20
        tb=draw.textbbox((x,y),edge["relationship"],font=font,anchor="mm")
        draw.rectangle((tb[0]-7,tb[1]-4,tb[2]+7,tb[3]+4),fill="white")
        draw.text((x,y),edge["relationship"],font=font,fill="#102c40",anchor="mm")
    title=graph.get("title")
    if title:draw.text((38,32),title["text"],font=titlefont,fill="#102c40")
    image.save(path)


def main():
    manifest=read(ROOT/"manifest.json")
    matrix=read(ROOT/"approach_matrix.json")
    entries=[]
    for item in manifest:
        slug=item["id"];graph=read(OUT/(slug+".json"))
        lines=["flowchart LR"]
        for n in graph["nodes"]:
            label=n["label"].replace('"','&quot;')
            shape=n["type"]
            syntax={"box":f'["{label}"]',"round":f'("{label}")',"pill":f'(["{label}"])',
                    "circle":f'(("{label}"))',"diamond":f'{{"{label}"}}',"hex":f'{{{{"{label}"}}}}',
                    "text":f'["{label}"]'}[shape]
            lines.append(f'  {n["id"]}{syntax}')
            if shape=="text":lines.append(f'  style {n["id"]} fill:none,stroke:none')
        for e in graph["edges"]:
            relationship=e["relationship"].replace('|','&#124;')
            join="---" if e["direction"]=="undirected" else "-->"
            lines.append(f'  {e["source"]} {join}|{relationship}| {e["target"]}')
        for i,e in enumerate(graph["edges"]):
            if e.get("dashed"):lines.append(f'  linkStyle {i} stroke-dasharray: 8 5')
        (OUT/(slug+".mmd")).write_text("\n".join(lines)+"\n",encoding="utf-8")
        inferred=OUT/(slug+".png")
        render_graph(graph,inferred)
        entries.append({"title":item["title"],"context":item["context"],"slug":slug,
            "source":"data:image/png;base64,"+base64.b64encode((ROOT/(slug+".png")).read_bytes()).decode(),
            "inferred":"data:image/png;base64,"+base64.b64encode(inferred.read_bytes()).decode(),
            "mermaid":(OUT/(slug+".mmd")).read_text(encoding="utf-8"),
            "uncertainties":graph["uncertainties"]})
    payload=json.dumps({"entries":entries,"matrix":matrix},ensure_ascii=True,separators=(',',':')).replace('</','<\\/')
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Graph benchmark v2</title>
<style>body{font:16px system-ui;margin:24px;background:#f7f9fb;color:#182b3b}main{max-width:1600px;margin:auto}select{font:inherit;padding:6px}section{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}figure{margin:0;background:white;border:1px solid #ccd6df;padding:8px}img{display:block;width:100%;height:auto}figcaption{font-weight:700;padding:5px}table{border-collapse:collapse;background:white;margin-top:22px;width:100%}td,th{border:1px solid #ccd6df;padding:7px;text-align:left}details{margin-top:18px}pre{white-space:pre-wrap}small{color:#4f6170}</style>
<main><h1>Ten Finnish graph fixtures: source and inferred</h1><p><small>Inferred graph uses Codex visual reading plus RapidOCR PP-OCRv6 Finnish. The visual reading was non-blind; the fixture author and reviewer were the same agent. Rendering style is generic. Text and topology are scored separately.</small></p>
<label>Diagram <select id="choose"></select></label><section><figure><figcaption>Source image</figcaption><img id="source" alt="Source graph"></figure><figure><figcaption>Inferred graph</figcaption><img id="inferred" alt="Inferred graph"></figure></section>
<div id="issues"></div><details><summary>Inferred Mermaid source</summary><pre id="mermaid"></pre></details>
<h2>Approach matrix</h2><table id="matrix"></table></main>
<script>const data=__DATA__;const sel=document.querySelector('#choose');data.entries.forEach((e,i)=>{let o=document.createElement('option');o.value=i;o.textContent=`${i+1}. ${e.title} (${e.context})`;sel.append(o)});function show(){let e=data.entries[+sel.value];document.querySelector('#source').src=e.source;document.querySelector('#inferred').src=e.inferred;document.querySelector('#mermaid').textContent=e.mermaid;document.querySelector('#issues').textContent=e.uncertainties.length?`${e.uncertainties.length} uncertainty or unassigned OCR item(s): ${e.uncertainties.map(x=>x.text||x.vision).join(', ')}`:'No OCR/vision conflict or extra OCR item for this diagram.'}sel.onchange=show;show();const cols=['approach','cases','all_visible_text_exact','all_visible_text_precision','extra_ocr_items','node_labels_exact','edge_labels_exact','connections_found','connections_total','arrow_accuracy','fully_correct_edges'];let table=document.querySelector('#matrix');let header=document.createElement('tr');cols.forEach(k=>{let th=document.createElement('th');th.textContent=k;header.append(th)});table.append(header);data.matrix.forEach(row=>{let tr=document.createElement('tr');cols.forEach(k=>{let td=document.createElement('td');td.textContent=row[k]??'—';tr.append(td)});table.append(tr)});</script></html>'''.replace('__DATA__',payload)
    (ROOT/"results_viewer.html").write_text(html,encoding="utf-8")
    print("Exported",len(entries),"inferred Mermaid files, PNGs, and results_viewer.html")


if __name__=="__main__":main()
