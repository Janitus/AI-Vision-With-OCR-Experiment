"""Render blind OCR+vision predictions beside the vision-only predictions."""
import base64
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"benchmark_v2"))
sys.path.insert(0,str(ROOT.parent/"blind_vision"))
from export_results import render_graph
from export_blind import canonical


def load(path):return json.loads(path.read_text(encoding="utf-8"))


def main():
    out=ROOT/"inferred_fusion";out.mkdir(exist_ok=True)
    scores=load(ROOT/"fusion_scores.json")["cases"]
    entries=[]
    for i in range(1,11):
        name=f"case_{i:02}";pred=load(ROOT/"predictions"/(name+".json"))
        graph={"title":{"text":pred["title"]},
               "nodes":[{"id":n["id"],"label":n["label"],"type":canonical(n["type"]),"center":n["center"]} for n in pred["nodes"]],
               "edges":[{"source":e["source"],"target":e["target"],"relationship":e["relationship"],
                         "direction":e["direction"],"dashed":e.get("dashed",False),"label_bbox":None} for e in pred["edges"]]}
        image=out/(name+".png");render_graph(graph,image)
        lines=["flowchart LR"]
        for n in graph["nodes"]:
            label=n["label"].replace('"','&quot;')
            syntax={"box":f'["{label}"]',"round":f'("{label}")',"pill":f'(["{label}"])',
                    "circle":f'(("{label}"))',"diamond":f'{{"{label}"}}',"hex":f'{{{{"{label}"}}}}',
                    "text":f'["{label}"]'}[n["type"]]
            lines.append(f'  {n["id"]}{syntax}')
            if n["type"]=="text":lines.append(f'  style {n["id"]} fill:none,stroke:none')
        for e in graph["edges"]:
            link="-->" if e["direction"]=="source_to_target" else "---"
            label=e["relationship"]+(" [direction unknown]" if e["direction"]=="unknown" else "")
            lines.append(f'  {e["source"]} {link}|{label}| {e["target"]}')
        for j,e in enumerate(graph["edges"]):
            if e["dashed"]:lines.append(f'  linkStyle {j} stroke-dasharray: 8 5')
        (out/(name+".mmd")).write_text("\n".join(lines)+"\n",encoding="utf-8")
        src=ROOT/"images"/(name+".png")
        vision=ROOT.parent/"blind_vision"/"inferred_blind"/(name+".png")
        encoded=lambda p:"data:image/png;base64,"+base64.b64encode(p.read_bytes()).decode()
        entries.append({"id":name,"title":pred["title"],"source":encoded(src),"vision":encoded(vision),
                        "fusion":encoded(image),"errors":scores[name]["errors"],
                        "uncertainties":pred.get("uncertainties",[]),"ocr_disagreements":pred.get("ocr_disagreements",[])})
    payload=json.dumps(entries,ensure_ascii=True,separators=(',',':')).replace('</','<\\/')
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Blind graph approach comparison</title><style>body{font:16px system-ui;margin:24px;background:#f7f9fb;color:#182b3b}main{max-width:1800px;margin:auto}select{font:inherit;padding:6px}section{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px}figure{margin:0;background:white;border:1px solid #ccd6df;padding:6px}img{display:block;width:100%;height:auto}figcaption{font-weight:700;padding:5px}pre{white-space:pre-wrap}small{color:#4f6170}</style><main><h1>Blind graph extraction: vision alone and OCR-assisted</h1><p><small>Two fresh sessions saw the same ten images. The second also saw raw RapidOCR text and coordinates. Reconstructed images use generic styling; compare graph content and arrowheads rather than colors or exact layout.</small></p><label>Diagram <select id="choose"></select></label><section><figure><figcaption>Source</figcaption><img id="source" alt="Source graph"></figure><figure><figcaption>Blind vision only</figcaption><img id="vision" alt="Blind vision graph"></figure><figure><figcaption>Blind vision + OCR</figcaption><img id="fusion" alt="Blind OCR-assisted graph"></figure></section><h2>OCR-assisted audit</h2><pre id="audit"></pre></main><script>const entries=__DATA__;const s=document.querySelector('#choose');entries.forEach((e,i)=>{let o=document.createElement('option');o.value=i;o.textContent=`${e.id}: ${e.title}`;s.append(o)});function show(){let e=entries[+s.value];for(let k of ['source','vision','fusion'])document.querySelector('#'+k).src=e[k];document.querySelector('#audit').textContent=JSON.stringify({errors:e.errors,uncertainties:e.uncertainties,rejected_ocr:e.ocr_disagreements},null,2)}s.onchange=show;show()</script></html>'''.replace('__DATA__',payload)
    (ROOT/"comparison_viewer.html").write_text(html,encoding="utf-8")
    print("Exported 10 fused Mermaid/PNG pairs and comparison_viewer.html")


if __name__=="__main__":main()
