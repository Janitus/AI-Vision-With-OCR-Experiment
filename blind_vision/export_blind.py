"""Render the fresh session's saved predictions and a source-versus-blind viewer."""
import base64
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"benchmark_v2"))
from export_results import render_graph


def load(path):return json.loads(path.read_text(encoding="utf-8"))


def canonical(s):
    return {"ellipse":"circle","rounded_rectangle":"round","rectangle":"box",
            "text_only":"text","hexagon":"hex"}.get(s,s)


def main():
    out=ROOT/"inferred_blind";out.mkdir(exist_ok=True)
    scores=load(ROOT/"blind_scores.json")["cases"]
    entries=[]
    for i in range(1,11):
        case=f"case_{i:02}";pred=load(ROOT/"predictions"/(case+".json"))
        graph={"title":{"text":pred["title"]},
               "nodes":[{"id":n["id"],"label":n["label"],"type":canonical(n["type"]),"center":n["center"]} for n in pred["nodes"]],
               "edges":[{"source":e["source"],"target":e["target"],"relationship":e["relationship"],
                         "direction":e["direction"],"dashed":e.get("dashed",False),"label_bbox":None} for e in pred["edges"]]}
        render_graph(graph,out/(case+".png"))
        lines=["flowchart LR"]
        for n in graph["nodes"]:
            label=n["label"].replace('"','&quot;')
            syntax={"box":f'["{label}"]',"round":f'("{label}")',"pill":f'(["{label}"])',
                    "circle":f'(("{label}"))',"diamond":f'{{"{label}"}}',"hex":f'{{{{"{label}"}}}}',
                    "text":f'["{label}"]'}[n["type"]]
            lines.append(f'  {n["id"]}{syntax}')
            if n["type"]=="text":lines.append(f'  style {n["id"]} fill:none,stroke:none')
        for e in graph["edges"]:
            direction=e["direction"]
            link="-->" if direction=="source_to_target" else "---"
            label=e["relationship"]+(" [direction unknown]" if direction=="unknown" else "")
            lines.append(f'  {e["source"]} {link}|{label}| {e["target"]}')
        for j,e in enumerate(graph["edges"]):
            if e["dashed"]:lines.append(f'  linkStyle {j} stroke-dasharray: 8 5')
        (out/(case+".mmd")).write_text("\n".join(lines)+"\n",encoding="utf-8")
        entries.append({"id":case,"title":pred["title"],
            "source":"data:image/png;base64,"+base64.b64encode((ROOT/"images"/(case+".png")).read_bytes()).decode(),
            "inferred":"data:image/png;base64,"+base64.b64encode((out/(case+".png")).read_bytes()).decode(),
            "errors":scores[case]["errors"],"uncertainties":pred.get("uncertainties",[]),
            "mermaid":"\n".join(lines)})
    payload=json.dumps(entries,ensure_ascii=True,separators=(',',':')).replace('</','<\\/')
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Blind Codex graph extraction</title><style>body{font:16px system-ui;margin:24px;background:#f7f9fb;color:#182b3b}main{max-width:1600px;margin:auto}select{font:inherit;padding:6px}section{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}figure{margin:0;background:white;border:1px solid #ccd6df;padding:8px}img{display:block;width:100%;height:auto}figcaption{font-weight:700;padding:5px}pre{white-space:pre-wrap}small{color:#4f6170}</style><main><h1>Blind Codex vision: source and inferred graphs</h1><p><small>The predictions were saved by a fresh session before source comparison. Generic rendering reflects its node-shape classifications and arrow directions; it does not attempt to copy colors or fonts.</small></p><label>Diagram <select id="choose"></select></label><section><figure><figcaption>Source image</figcaption><img id="source" alt="Source graph"></figure><figure><figcaption>Blind inference</figcaption><img id="inferred" alt="Blind inferred graph"></figure></section><h2>Errors and uncertainties</h2><pre id="errors"></pre><details><summary>Predicted Mermaid</summary><pre id="mermaid"></pre></details></main><script>const entries=__DATA__;const s=document.querySelector('#choose');entries.forEach((e,i)=>{let o=document.createElement('option');o.value=i;o.textContent=`${e.id}: ${e.title}`;s.append(o)});function show(){let e=entries[+s.value];document.querySelector('#source').src=e.source;document.querySelector('#inferred').src=e.inferred;document.querySelector('#errors').textContent=JSON.stringify({errors:e.errors,uncertainties:e.uncertainties},null,2);document.querySelector('#mermaid').textContent=e.mermaid}s.onchange=show;show()</script></html>'''.replace('__DATA__',payload)
    (ROOT/"blind_viewer.html").write_text(html,encoding="utf-8")
    print("Exported blind viewer and 10 inferred Mermaid/PNG pairs")


if __name__=="__main__":main()
