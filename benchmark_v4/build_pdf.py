"""One-file informal report for the corrected benchmark."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
BENCH=ROOT/"benchmark_v4"
OUT=ROOT/"finnish_diagram_extraction_findings.pdf"
OUT.parent.mkdir(parents=True,exist_ok=True)
rows=json.loads((BENCH/"approach_matrix.json").read_text(encoding="utf-8"))
NAVY="#17324c";BLUE="#146a8a";GREY="#536270";PALE="#eaf3f6";LINE="#d4dfe5"
plt.rcParams.update({"font.family":"DejaVu Sans","pdf.fonttype":42})

def page():
    fig=plt.figure(figsize=(11.69,8.27),facecolor="white")
    ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis("off")
    return fig,ax

def txt(ax,x,y,s,size=10,weight="normal",color=NAVY):
    ax.text(x,y,s,fontsize=size,fontweight=weight,color=color,va="top",ha="left",transform=ax.transAxes)

def foot(ax,n):
    ax.plot([.055,.945],[.06,.06],color=LINE,lw=.8,transform=ax.transAxes)
    txt(ax,.055,.045,"Our small graph-reading test | corrected rerun | 31 October 2026",7.5,color=GREY)
    txt(ax,.925,.045,str(n),7.5,color=GREY)

with PdfPages(OUT,metadata={"Title":"Our graph-reading test - corrected rerun","Author":"AI Vision With OCR Experiment"}) as pdf:
    fig,ax=page()
    txt(ax,.055,.958,"INFORMAL EXPERIMENT NOTES",9,"bold",BLUE)
    txt(ax,.055,.922,"Our graph-reading test: corrected rerun",19,"bold")
    txt(ax,.055,.870,"10 clean, synthetic Finnish-context figures | 83 nodes | 105 edges | 198 printed text regions",9.3,color=GREY)
    ax.add_patch(Rectangle((.055,.763),.89,.080,facecolor=PALE,edgecolor="none",transform=ax.transAxes))
    txt(ax,.071,.827,"Why we reran it",11,"bold",BLUE)
    txt(ax,.071,.802,"Eight old source edges were hidden or coincident, making some v3 graph 'errors' visually uncheckable.",9.5)
    txt(ax,.071,.779,"The new source images pass text visibility and basic edge-geometry checks.",9.5)
    txt(ax,.055,.723,"Approach matrix",12.5,"bold")
    txt(ax,.055,.697,"Same 198 source items in every row; OCR rows test text, graph rows test reconstructed elements.",8.5,color=GREY)
    xs=[.070,.387,.490,.607,.710,.818]
    headers=["Approach","Task","Events / 198","Exact figures","Node text","Edge text"]
    ax.add_patch(Rectangle((.055,.647),.89,.032,facecolor=NAVY,transform=ax.transAxes))
    for x,h in zip(xs,headers):txt(ax,x,.671,h,8.0,"bold","white")
    for i,r in enumerate(rows):
        y=.647-i*.045
        ax.add_patch(Rectangle((.055,y-.045),.89,.045,facecolor="#f7fafb" if i%2==0 else "white",transform=ax.transAxes))
        vals=[r["approach"],r["mode"],f"{r['errors']} ({r['error_rate']:.1f}%)",f"{r['perfect_figures']}/10",str(r["node_label_errors"]),str(r["edge_label_errors"])]
        for j,(x,v) in enumerate(zip(xs,vals)):txt(ax,x,y-.013,v,7.6 if j==0 else 8.2,"bold" if j==2 else "normal")
    txt(ax,.055,.339,"What did the error events mean?",11.5,"bold")
    error_rows=[
      ("RapidOCR", "2 edge-label misreads/misses + 14 unmatched text boxes"),
      ("PaddleOCR", "19 edge-label misreads/misses + 38 unmatched text boxes"),
      ("Old OCR", "7 title + 17 node + 36 edge text errors"),
      ("Blind vision", "16 strict shape-category mismatches; no text or edge-record mismatch"),
      ("Blind OCR + vision", "8 strict shape-category mismatches; 8 arrowless links left semantically unknown"),
    ]
    for i,(a,b) in enumerate(error_rows):
        y=.307-i*.040
        ax.add_patch(Rectangle((.055,y-.035),.89,.035,facecolor=PALE if i%2==0 else "white",transform=ax.transAxes))
        txt(ax,.070,y-.008,a,8.3,"bold");txt(ax,.280,y-.008,b,8.2)
    txt(ax,.055,.086,"All 105 visible edge records matched in both fresh blind runs under the corrected visual rubric.",8.5,"bold")
    foot(ax,1);pdf.savefig(fig);plt.close(fig)

    source=Image.open(BENCH/"tutkimusjulkaisu.png").convert("RGB")
    pred=Image.open(BENCH/"blind_vision"/"rendered"/"case_07.png").convert("RGB")
    for n,img,label in [(2,source,"Corrected source figure"),(3,pred,"Blind vision reconstruction")]:
        fig,ax=page()
        txt(ax,.055,.958,"EXAMPLE FROM THE CORRECTED SET",9,"bold",BLUE)
        txt(ax,.055,.922,label,19,"bold")
        txt(ax,.055,.870,"Research-publication workflow; the reconstruction was saved before scoring.",9,color=GREY)
        pane=fig.add_axes([.055,.205,.89,.620]);pane.imshow(img,interpolation="nearest");pane.axis("off")
        if n==2:
            txt(ax,.055,.165,"The v3 version contained an overlapping extra link. This v4 source shows only visually checkable edges.",9.0)
        else:
            txt(ax,.055,.165,"Graph text and edges match this source; strict shape coding differs for its rounded nodes.",9.0)
        txt(ax,.055,.129,"The earlier v3 error counts are superseded. This clean synthetic set cannot establish a universal error rate.",8.5,color=GREY)
        foot(ax,n);pdf.savefig(fig);plt.close(fig)

print(OUT)
