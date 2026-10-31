"""Build the informal, self-contained v5 PDF report."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
from PIL import Image

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/"finnish_diagram_extraction_findings.pdf"
rows=json.loads((ROOT/"approach_matrix.json").read_text(encoding="utf-8"))
paired=json.loads((ROOT/"paired_results.json").read_text(encoding="utf-8"))
audit=json.loads((ROOT/"validation.json").read_text(encoding="utf-8"))
sources=[json.loads(p.read_text(encoding="utf-8")) for p in ROOT.glob("*.source.json")]
truth_nodes=sum(len(s["nodes"]) for s in sources)
truth_edges=sum(len(s["edges"]) for s in sources)
navy="#17324c";blue="#146a8a";grey="#536270";pale="#eaf3f6"
plt.rcParams.update({"font.family":"DejaVu Sans","pdf.fonttype":42})

def page():
    fig=plt.figure(figsize=(11.69,8.27),facecolor="white")
    ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis("off")
    return fig,ax

def text(ax,x,y,value,size=9,weight="normal",color=navy):
    ax.text(x,y,value,transform=ax.transAxes,ha="left",va="top",fontsize=size,fontweight=weight,color=color)

def foot(ax,n):
    ax.plot([.055,.945],[.06,.06],color="#d4dfe5",lw=.8,transform=ax.transAxes)
    text(ax,.055,.045,"Our diagram-reading test | routed-arrow rerun | 31 October 2026",7.5,color=grey)
    text(ax,.925,.045,str(n),7.5,color=grey)

with PdfPages(OUT,metadata={"Title":"Our graph-reading test with routed arrows","Author":"AI Vision With OCR Experiment"}) as pdf:
    fig,ax=page()
    text(ax,.055,.958,"INFORMAL EXPERIMENT NOTES",9,"bold",blue)
    text(ax,.055,.921,"Graph reading with curved and bent arrows",19,"bold")
    text(ax,.055,.869,f"12 clean Finnish-context figures | {truth_nodes} nodes | {truth_edges} edges | {audit['source_items']} visible text regions",9,color=grey)
    ax.add_patch(Rectangle((.055,.765),.89,.078,facecolor=pale,transform=ax.transAxes))
    text(ax,.070,.825,"What changed",10.8,"bold",blue)
    text(ax,.070,.799,"Two route variants of the same rail graph joined the ten corrected figures.",9.2)
    text(ax,.070,.779,"Their curves and detours never pass through unrelated nodes; the three rail images are paired, not independent.",8.8)
    text(ax,.055,.728,"Approach matrix",12,"bold")
    text(ax,.055,.698,"OCR rows score printed text; graph rows score exact graph elements. All rates use 240 source items.",8.5,color=grey)
    xs=(.067,.383,.487,.607,.720,.830)
    labels=("Approach","Task","Events / 240","Exact figures","Node text","Edge text")
    ax.add_patch(Rectangle((.055,.651),.89,.032,facecolor=navy,transform=ax.transAxes))
    for x,label in zip(xs,labels):text(ax,x,.675,label,7.8,"bold","white")
    for i,row in enumerate(rows):
        y=.651-i*.045
        ax.add_patch(Rectangle((.055,y-.045),.89,.045,facecolor="#f7fafb" if i%2==0 else "white",transform=ax.transAxes))
        values=(row["approach"],row["mode"],f"{row['errors']} ({row['error_rate']:.1f}%)",f"{row['perfect_figures']}/12",str(row["node_label_errors"]),str(row["edge_label_errors"]))
        for j,(x,value) in enumerate(zip(xs,values)):text(ax,x,y-.013,value,7.5 if j==0 else 8,"bold" if j==2 else "normal")
    text(ax,.055,.344,"Paired route comparison: scorer events / 21",11.3,"bold")
    text(ax,.055,.315,"These are three renderings of one graph. Lower means fewer strict scorer events.",8.2,color=grey)
    ax.add_patch(Rectangle((.055,.270),.89,.029,facecolor=pale,transform=ax.transAxes))
    for x,label in ((.067,"Approach"),(.490,"Straight"),(.640,"Curved"),(.790,"Right-angle")):
        text(ax,x,.292,label,8,"bold")
    for i,row in enumerate(rows):
        y=.270-i*.028
        vals=[next(p["events"] for p in paired if p["approach"]==row["approach"] and p["route"]==route) for route in ("straight","curved","right_angle")]
        text(ax,.067,y-.008,row["approach"],7.5)
        for x,value in zip((.490,.640,.790),vals):text(ax,x,y-.008,str(value),7.8)
    text(ax,.055,.084,"Exact endpoint, label, arrowhead, and stroke results are in the accompanying CSV and ledger.",8.2,color=grey)
    foot(ax,1);pdf.savefig(fig);plt.close(fig)

    for number,slug,title in ((2,"junaliikenteen_ohjaus","Straight baseline"),(3,"rail_curved","Curved-arrow variant"),(4,"rail_elbow","Right-angle variant")):
        fig,ax=page()
        text(ax,.055,.958,"PAIRED RAIL-ROUTE FIGURES",9,"bold",blue)
        text(ax,.055,.922,title,19,"bold")
        text(ax,.055,.869,"Same labels, endpoints, and arrowheads. Node outlines and label positions also vary.",8.8,color=grey)
        pane=fig.add_axes([.055,.195,.89,.635]);pane.imshow(Image.open(ROOT/f"{slug}.png").convert("RGB"),interpolation="nearest");pane.axis("off")
        text(ax,.055,.145,"Source route control points and a separate, full-size PNG are retained with the benchmark.",8.7)
        text(ax,.055,.116,"Clean synthetic diagrams do not establish a universal error rate or real-world semantic truth.",8.3,color=grey)
        foot(ax,number);pdf.savefig(fig);plt.close(fig)
print(OUT)
