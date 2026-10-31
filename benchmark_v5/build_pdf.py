"""Build the three-page informal report: results, source, reconstruction."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Ellipse, Rectangle
from PIL import Image

BENCH=Path(__file__).resolve().parent
OUT=BENCH.parent/"finnish_diagram_extraction_findings.pdf"
rows=json.loads((BENCH/"approach_matrix.json").read_text(encoding="utf-8"))
by_name={r["approach"]:r for r in rows}
navy="#17324c";blue="#146a8a";grey="#536270";pale="#eaf3f6";red="#c82333"
plt.rcParams.update({"font.family":"DejaVu Sans","pdf.fonttype":42})

def page():
    fig=plt.figure(figsize=(11.69,8.27),facecolor="white")
    ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis("off")
    return fig,ax

def txt(ax,x,y,value,size=9,weight="normal",color=navy):
    ax.text(x,y,value,transform=ax.transAxes,ha="left",va="top",fontsize=size,
            fontweight=weight,color=color)

def foot(ax,n):
    ax.plot([.055,.945],[.06,.06],color="#d4dfe5",lw=.8,transform=ax.transAxes)
    txt(ax,.055,.045,"Our small graph-reading test | 31 October 2026",7.5,color=grey)
    txt(ax,.925,.045,str(n),7.5,color=grey)

with PdfPages(OUT,metadata={"Title":"Our graph-reading test",
                            "Author":"AI Vision With OCR Experiment"}) as pdf:
    fig,ax=page()
    txt(ax,.055,.958,"INFORMAL EXPERIMENT NOTES",9,"bold",blue)
    txt(ax,.055,.922,"Our graph-reading test",19,"bold")
    txt(ax,.055,.870,"12 clean, synthetic Finnish-context images | 99 nodes | 129 edges | 240 printed text regions",9.3,color=grey)
    ax.add_patch(Rectangle((.055,.763),.89,.080,facecolor=pale,edgecolor="none",transform=ax.transAxes))
    txt(ax,.071,.827,"How to read the scores",11,"bold",blue)
    txt(ax,.071,.802,"Every row uses the same 240 source items; extra OCR boxes add error events.",9.5)
    txt(ax,.071,.779,"OCR checks printed text. Vision checks reconstructed nodes, labels, arrows, and strokes.",9.5)
    txt(ax,.055,.723,"Approach matrix",12.5,"bold")
    txt(ax,.055,.697,"The two tasks differ, so their percentages are not a direct ranking of graph accuracy.",8.5,color=grey)
    xs=[.070,.387,.490,.607,.710,.818]
    headers=["Approach","Task","Events / 240","Exact figures","Node text","Edge text"]
    ax.add_patch(Rectangle((.055,.647),.89,.032,facecolor=navy,transform=ax.transAxes))
    for x,h in zip(xs,headers):txt(ax,x,.671,h,8.0,"bold","white")
    for i,r in enumerate(rows):
        y=.647-i*.045
        ax.add_patch(Rectangle((.055,y-.045),.89,.045,facecolor="#f7fafb" if i%2==0 else "white",transform=ax.transAxes))
        vals=[r["approach"],r["mode"],f"{r['errors']} ({r['error_rate']:.1f}%)",
              f"{r['perfect_figures']}/12",str(r["node_label_errors"]),str(r["edge_label_errors"])]
        for j,(x,v) in enumerate(zip(xs,vals)):
            txt(ax,x,y-.013,v,7.5 if j==0 else 8.0,"bold" if j==2 else "normal")
    txt(ax,.055,.339,"What did the error events mean?",11.5,"bold")
    error_rows=[
        ("RapidOCR", "2 edge-text misses or misreads; 15 unmatched text boxes"),
        ("PaddleOCR", "19 edge-text misses or misreads; 38 unmatched text boxes"),
        ("Old OCR", "9 title, 23 node-text, and 42 edge-text errors"),
        ("Blind vision", "18 node-shape errors; 1 wrong arrow; 1 wrong stroke"),
        ("Blind vision + OCR", "8 node-shape errors; 3 wrong arrows; 1 wrong stroke"),
        ("Deterministic OCR union", "Vision graph unchanged: 18 shape, 1 arrow, 1 stroke"),
    ]
    for i,(label,detail) in enumerate(error_rows):
        y=.307-i*.040
        ax.add_patch(Rectangle((.055,y-.035),.89,.035,facecolor=pale if i%2==0 else "white",transform=ax.transAxes))
        txt(ax,.070,y-.008,label,8.3,"bold")
        txt(ax,.280,y-.008,detail,8.2)
    foot(ax,1);pdf.savefig(fig);plt.close(fig)

    examples=[
        (2,BENCH/"paivystyksen_verkko.png","Source diagram",
         "Reference: this link has no arrowhead.","Erikoissairaanhoito to Jatkohoito is printed as an arrowless link.",765),
        (3,BENCH/"blind_vision"/"rendered"/"case_01.png","Blind vision reconstruction",
         "Error: the reconstruction adds an arrowhead.","The connection and label are correct; the extra arrow changes its direction.",785),
    ]
    for number,image_path,title,callout,detail,arrow_y in examples:
        fig,ax=page()
        txt(ax,.055,.958,"ONE DIAGRAM, TWO READINGS",9,"bold",blue)
        txt(ax,.055,.922,title,19,"bold")
        txt(ax,.055,.870,"Päivystyksen hoitoverkko | emergency-care network",9,color=grey)
        pane=fig.add_axes([.055,.205,.89,.620])
        pane.imshow(Image.open(image_path).convert("RGB"),interpolation="nearest")
        pane.add_patch(Ellipse((1550,arrow_y),width=95,height=70,fill=False,
                               edgecolor=red,linewidth=3.2))
        pane.axis("off")
        txt(ax,.055,.163,callout,10.2,"bold",red)
        txt(ax,.055,.130,detail,8.9)
        foot(ax,number);pdf.savefig(fig);plt.close(fig)

print(OUT)
