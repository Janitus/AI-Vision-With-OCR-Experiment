"""Create ten varied, legible Finnish-language Mermaid graph fixtures.

The PNG previews are drawn from the same specifications as the Mermaid files.
No OCR or graph inference is run here; this is the review-before-benchmark stage.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
W, H = 1400, 850
FONTS = {
    "arial": "C:/Windows/Fonts/arial.ttf",
    "arial_bold": "C:/Windows/Fonts/arialbd.ttf",
    "georgia": "C:/Windows/Fonts/georgia.ttf",
    "times": "C:/Windows/Fonts/times.ttf",
    "courier": "C:/Windows/Fonts/cour.ttf",
    "segoe": "C:/Windows/Fonts/segoeui.ttf",
    "verdana": "C:/Windows/Fonts/verdana.ttf",
    "calibri": "C:/Windows/Fonts/calibri.ttf",
}


def n(label, x, y, shape=None, color=None, w=None, h=None):
    return {"label": label, "x": x, "y": y, "shape": shape, "color": color, "w": w, "h": h}


def e(a, b, label, *, xy=None, rotate=False, direction="source_to_target", dashed=False):
    return {"source": a, "target": b, "label": label, "label_xy": xy,
            "rotate": rotate, "direction": direction, "dashed": dashed}


CASES = [
    {"id":"terveyspolku","title":"Hoitopolku","context":"Terveydenhuolto","layout":"LR","shape":"round","font":"segoe","size":23,
     "background":"#ffffff","ink":"#18324a","edge":"#256b95","palette":["#d7efff","#d8f4df","#fff0cd","#eadfff","#ffdce3"],
     "nodes":[n("Potilas",145,435,w=205),n("Terveysasema",420,435,w=215),n("Lähete",695,435,w=205),n("Laboratorio",970,435,w=215),n("Tulokset",1245,435,w=205)],
     "edges":[e(0,1,"ottaa vastaan",xy=(282,353)),e(1,2,"laatii",xy=(558,353)),e(2,3,"lähettää",xy=(833,353)),e(3,4,"palauttaa",xy=(1108,353))]},
    {"id":"ministerioprosessi","title":"Valmisteluketju","context":"Ministeriöt","layout":"TB","shape":"box","font":"georgia","size":23,
     "background":"#ffffff","ink":"#202020","edge":"#333333","palette":["#f5f5f5"]*5,
     "nodes":[n("Aloite",700,140,w=255),n("Ministeriö",700,300,w=255),n("Lausunto",700,460,w=255),n("Valtioneuvosto",700,620,w=255),n("Päätös",700,780,w=255)],
     "edges":[e(0,1,"saapuu",xy=(940,220)),e(1,2,"pyytää",xy=(940,380)),e(2,3,"palautuu",xy=(940,540)),e(3,4,"hyväksyy",xy=(940,700))]},
    {"id":"saahavainnot","title":"Säähavainnot","context":"Sää ja ympäristö","layout":"TB","shape":"text","font":"verdana","size":25,
     "background":"#fcfdff","ink":"#13242e","edge":"#285a6d","palette":["#fcfdff"]*5,
     "nodes":[n("Sääasema",700,410,w=210,h=72),n("Tuuli",230,180,w=160,h=72),n("Sade",1170,180,w=160,h=72),n("Lämpötila",230,690,w=190,h=72),n("Paine",1170,690,w=160,h=72)],
     "edges":[e(1,0,"mittaa",xy=(435,270),rotate=True),e(2,0,"mittaa",xy=(965,270),rotate=True),
              e(3,0,"mittaa",xy=(438,593),rotate=True),e(4,0,"mittaa",xy=(962,593),rotate=True)]},
    {"id":"junamatka","title":"Junamatkan vaiheet","context":"Liikenne","layout":"LR","shape":"circle","font":"arial_bold","size":21,
     "background":"#f7fbff","ink":"#17304d","edge":"#1765ab","palette":["#d8e9ff","#e0f5e4","#fff1d5","#efdffc","#d7f3f1"],
     "nodes":[n("Lippu",175,220,w=170,h=120),n("Asema",590,220,w=170,h=120),n("Juna",1020,420,w=170,h=120),n("Vaihto",590,655,w=170,h=120),n("Määränpää",175,655,w=170,h=120)],
     "edges":[e(0,1,"näytetään",xy=(382,160)),e(1,2,"nousta",xy=(805,258),rotate=True),
              e(2,3,"jatkaa",xy=(810,568),rotate=True),e(3,4,"saapuu",xy=(380,713))]},
    {"id":"koulupolku","title":"Opintopolku","context":"Koulutus","layout":"TB","shape":"text","font":"times","size":27,
     "background":"#ffffff","ink":"#1c1c1c","edge":"#222222","palette":["#ffffff"]*6,
     "nodes":[n("Oppilas",700,130,w=200,h=72),n("Kurssi A",300,375,w=205,h=72),n("Kurssi B",1100,375,w=205,h=72),
              n("Arviointi A",300,645,w=230,h=72),n("Arviointi B",1100,645,w=230,h=72),n("Todistus",700,760,w=200,h=72)],
     "edges":[e(0,1,"valitsee",xy=(480,245),rotate=True),e(0,2,"valitsee",xy=(920,245),rotate=True),
              e(1,3,"arvioidaan",xy=(530,510)),e(2,4,"arvioidaan",xy=(870,510)),
              e(3,5,"koostaa",xy=(420,745)),e(4,5,"koostaa",xy=(980,745))]},
    {"id":"kirjastokierto","title":"Kirjastokierto","context":"Kirjastot","layout":"LR","shape":"pill","font":"calibri","size":25,
     "background":"#fffefa","ink":"#3a2b28","edge":"#8d5e47","palette":["#f8e4cc","#e3efff","#f8dfdf","#e6f3dd"],
     "nodes":[n("Teos",175,430,w=225),n("Varaus",525,430,w=225),n("Laina",875,430,w=225),n("Palautus",1225,430,w=225)],
     "edges":[e(0,1,"varataan",xy=(350,340)),e(1,2,"nouto",xy=(700,340)),e(2,3,"palautetaan",xy=(1050,340))]},
    {"id":"veropaatos","title":"Veropäätöksen käsittely","context":"Verotus","layout":"TB","shape":"diamond","font":"arial","size":22,
     "background":"#ffffff","ink":"#202020","edge":"#202020","palette":["#ffffff"]*4,
     "nodes":[n("Ilmoitus",700,160,w=220,h=105),n("Tarkistus",700,365,w=220,h=105),n("Päätös",700,570,w=220,h=105),n("Oikaisu",700,775,w=220,h=105)],
     "edges":[e(0,1,"vastaanottaa",xy=(990,262)),e(1,2,"arvioi",xy=(990,467)),e(2,3,"voi johtaa",xy=(990,672))]},
    {"id":"pelastusviesti","title":"Pelastustoimen viestit","context":"Pelastustoimi","layout":"LR","shape":"box","font":"courier","size":22,
     "background":"#17242f","ink":"#f5f7fa","edge":"#b7d8ef","palette":["#233b4d","#284557","#244150","#294356","#25404f"],
     "nodes":[n("Hälytys",140,430,w=200),n("Hätäkeskus",420,430,w=220),n("Pelastuslaitos",710,430,w=245),
              n("Tilannekuva",1000,430,w=220),n("Johto",1260,430,w=190)],
     "edges":[e(0,1,"välittää",xy=(280,338)),e(1,2,"hälyttää",xy=(565,338)),
              e(2,3,"päivittää",xy=(855,338)),e(3,4,"tiedottaa",xy=(1130,338))]},
    {"id":"sahkoverkko","title":"Sähköverkon osat","context":"Energia","layout":"LR","shape":"hex","font":"segoe","size":22,
     "background":"#fbfcf7","ink":"#29402b","edge":"#477a4e","palette":["#e6f4d9","#f6efc9","#d9ecf4","#e8dff3","#f7e2d5"],
     "nodes":[n("Voimala",165,430,w=215),n("Sähköverkko",430,430,w=215),n("Mittari",695,430,w=215),
              n("Kuluttaja",960,430,w=215),n("Raportti",1225,430,w=215)],
     "edges":[e(0,1,"syöttää",xy=(298,338)),e(1,2,"siirtää",xy=(563,338)),
              e(2,3,"mittaa",xy=(828,338)),e(3,4,"ilmoittaa",xy=(1093,338))]},
    {"id":"tutkimusverkko","title":"Tutkimusaineiston kulku","context":"Tutkimus","layout":"TB","shape":"mixed","font":"georgia","size":23,
     "background":"#ffffff","ink":"#21313e","edge":"#304b62","palette":["#e8f0f7","#ffffff","#e8f0f7","#ffffff","#e8f0f7"],
     "nodes":[n("Aineisto",700,145,shape="box",w=240),n("Keruu",260,370,shape="text",w=190,h=70),
              n("Tallennus",1140,370,shape="box",w=240),n("Analyysi",260,660,shape="text",w=200,h=70),
              n("Julkaisu",1140,660,shape="box",w=240)],
     "edges":[e(0,1,"ohjaa",xy=(470,240),rotate=True,dashed=True),e(0,2,"tallentaa",xy=(930,240),rotate=True),
              e(1,3,"tuottaa",xy=(445,520),dashed=True),e(2,4,"siirtää",xy=(955,520)),
              e(3,4,"avaa",xy=(700,710),direction="undirected",dashed=True)]},
]


def rgb(value: str) -> tuple[int,int,int]:
    return tuple(int(value[i:i+2],16) for i in (1,3,5))


def contrast(a: str,b: str) -> float:
    def luminance(color: str) -> float:
        channels=[]
        for value in rgb(color):
            value=value/255
            channels.append(value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4)
        return .2126*channels[0]+.7152*channels[1]+.0722*channels[2]
    x,y=sorted((luminance(a),luminance(b)),reverse=True)
    return (x+.05)/(y+.05)


def font(name: str,size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONTS[name],size)


def shape_box(node: dict) -> tuple[int,int,int,int]:
    w=node.get("w") or 215; h=node.get("h") or 88
    return (round(node["x"]-w/2),round(node["y"]-h/2),round(node["x"]+w/2),round(node["y"]+h/2))


def text_lines(draw: ImageDraw.ImageDraw,text: str,font_obj,max_width: int) -> list[str]:
    words=text.split(); lines=[]; current=""
    for word in words:
        candidate=(current+" "+word).strip()
        if current and draw.textlength(candidate,font=font_obj)>max_width:
            lines.append(current);current=word
        else: current=candidate
    if current: lines.append(current)
    return lines


def label_patch(text: str,font_obj,ink: str,bg: str,angle: float=0):
    scratch=Image.new("RGBA",(1,1)); d=ImageDraw.Draw(scratch)
    bb=d.textbbox((0,0),text,font=font_obj)
    width=bb[2]-bb[0]+22; height=bb[3]-bb[1]+16
    patch=Image.new("RGBA",(width,height),rgb(bg)+(255,)); p=ImageDraw.Draw(patch)
    p.text((11-bb[0],8-bb[1]),text,font=font_obj,fill=rgb(ink)+(255,))
    if angle:
        patch=patch.rotate(angle,expand=True,resample=Image.Resampling.BICUBIC)
    return patch


def line_ends(src: dict,dst: dict) -> tuple[tuple[float,float],tuple[float,float]]:
    ax,ay=src["x"],src["y"]; bx,by=dst["x"],dst["y"]
    dx,dy=bx-ax,by-ay
    aw,ah=(src.get("w") or 215)/2,(src.get("h") or 88)/2
    bw,bh=(dst.get("w") or 215)/2,(dst.get("h") or 88)/2
    ta=min(aw/max(abs(dx),1),ah/max(abs(dy),1))
    tb=min(bw/max(abs(dx),1),bh/max(abs(dy),1))
    return (ax+dx*ta,ay+dy*ta),(bx-dx*tb,by-dy*tb)


def intersects(a,b,margin=0):
    return a[0]<b[2]+margin and a[2]>b[0]-margin and a[1]<b[3]+margin and a[3]>b[1]-margin


def render(case: dict) -> dict:
    image=Image.new("RGB",(W,H),rgb(case["background"])); draw=ImageDraw.Draw(image)
    ink=case["ink"]; edge_color=case["edge"]
    node_font=font(case["font"],case["size"])
    edge_font=font(case["font"],21)
    title_font=font("arial_bold",34)
    draw.text((38,32),case["title"],font=title_font,fill=ink)
    node_boxes=[shape_box(n) for n in case["nodes"]]
    label_boxes=[]; defects=[]; contrasts=[contrast(case["background"],ink)]
    for index,edge in enumerate(case["edges"]):
        start,end=line_ends(case["nodes"][edge["source"]],case["nodes"][edge["target"]])
        edge["points"]=[[round(start[0]),round(start[1])],[round(end[0]),round(end[1])]]
        if edge["dashed"]:
            length=math.dist(start,end); steps=max(1,int(length/19))
            ux,uy=(end[0]-start[0])/length,(end[1]-start[1])/length
            for j in range(0,steps,2):
                a=(start[0]+j*19*ux,start[1]+j*19*uy)
                b=(start[0]+min((j+1)*19,length)*ux,start[1]+min((j+1)*19,length)*uy)
                draw.line((*a,*b),fill=edge_color,width=4)
        else:
            draw.line((*start,*end),fill=edge_color,width=4)
        if edge["direction"]=="source_to_target":
            angle=math.atan2(end[1]-start[1],end[0]-start[0]); s=19
            wing1=(end[0]-s*math.cos(angle-.48),end[1]-s*math.sin(angle-.48))
            wing2=(end[0]-s*math.cos(angle+.48),end[1]-s*math.sin(angle+.48))
            draw.polygon([end,wing1,wing2],fill=edge_color)
    for i,node in enumerate(case["nodes"]):
        box=node_boxes[i]; shape=node.get("shape") or case["shape"]
        fill=node.get("color") or case["palette"][i%len(case["palette"])]
        contrasts.append(contrast(fill,ink))
        if shape=="mixed": shape="box"
        if shape=="box": draw.rectangle(box,fill=fill,outline=ink,width=3)
        elif shape=="round": draw.rounded_rectangle(box,radius=20,fill=fill,outline=ink,width=3)
        elif shape=="pill": draw.rounded_rectangle(box,radius=(box[3]-box[1])//2,fill=fill,outline=ink,width=3)
        elif shape=="circle": draw.ellipse(box,fill=fill,outline=ink,width=3)
        elif shape=="diamond":
            x1,y1,x2,y2=box; draw.polygon([((x1+x2)/2,y1),(x2,(y1+y2)/2),((x1+x2)/2,y2),(x1,(y1+y2)/2)],fill=fill)
            draw.line([((x1+x2)/2,y1),(x2,(y1+y2)/2),((x1+x2)/2,y2),(x1,(y1+y2)/2),((x1+x2)/2,y1)],fill=ink,width=3)
        elif shape=="hex":
            x1,y1,x2,y2=box; inset=(x2-x1)*.17
            poly=[(x1+inset,y1),(x2-inset,y1),(x2,(y1+y2)/2),(x2-inset,y2),(x1+inset,y2),(x1,(y1+y2)/2)]
            draw.polygon(poly,fill=fill);draw.line(poly+[poly[0]],fill=ink,width=3)
        elif shape=="text":
            if case.get("clear_text_background",False):
                draw.rectangle(box,fill=case["background"])
        else: raise ValueError(shape)
        # Word wrapping uses measured font width, and text must fit the visible shape.
        usable=(box[2]-box[0])*(.65 if shape in ("diamond","hex","circle") else .83)
        size=case["size"]
        while True:
            f=font(case["font"],size)
            lines=text_lines(draw,node["label"],f,int(usable))
            width=max(draw.textlength(line,font=f) for line in lines)
            height=len(lines)*(size+5)
            if width<=usable and height<=box[3]-box[1]-12: break
            size-=1
            if size<17: raise ValueError(f'{case["id"]}: node text cannot fit: {node["label"]}')
        top=node["y"]-height/2
        for j,line in enumerate(lines):
            cy=top+(j+.5)*(size+5)
            bb=draw.textbbox((node["x"],cy),line,font=f,anchor="mm")
            label_boxes.append({"kind":"node","id":i,"bbox":bb,"text":line})
            draw.text((node["x"],cy),line,font=f,fill=ink,anchor="mm")
    for i,edge in enumerate(case["edges"]):
        start,end=edge["points"]
        angle=0.0
        if edge["rotate"]:
            degrees=math.degrees(math.atan2(end[1]-start[1],end[0]-start[0]))
            if degrees>90: degrees-=180
            if degrees<-90: degrees+=180
            angle=-degrees
        patch=label_patch(edge["label"],edge_font,ink,case["background"],angle)
        cx,cy=edge["label_xy"]
        x=round(cx-patch.width/2);y=round(cy-patch.height/2)
        bb=(x,y,x+patch.width,y+patch.height)
        if not (18<=x and 18<=y and bb[2]<=W-18 and bb[3]<=H-18):
            defects.append(f'edge {i} label outside canvas: {edge["label"]}')
        for j,nb in enumerate(node_boxes):
            if intersects(bb,nb,4): defects.append(f'edge {i} label overlaps node {j}: {edge["label"]}')
        for old in label_boxes:
            if intersects(bb,old["bbox"],4): defects.append(f'edge {i} label overlaps {old["kind"]} text: {edge["label"]}')
        label_boxes.append({"kind":"edge","id":i,"bbox":bb,"text":edge["label"],"rotation":round(angle,1)})
        image.paste(patch,(x,y),patch)
    title_box=draw.textbbox((38,32),case["title"],font=title_font)
    if title_box[2]>W-25: defects.append("title outside canvas")
    for old in label_boxes:
        if intersects(title_box,old["bbox"],6): defects.append(f'title overlaps {old["kind"]} text')
    if defects: raise ValueError(case["id"]+": "+"; ".join(defects))
    if min(contrasts)<4.5: raise ValueError(f'{case["id"]}: insufficient text contrast {min(contrasts):.2f}')
    image.save(ROOT/(case["id"]+".png"))
    return {"title_bbox":title_box,"text_boxes":label_boxes,"node_boxes":node_boxes,
            "clipped_text_count":0,"overlapping_text_count":0,
            "minimum_text_contrast":round(min(contrasts),2)}


def mermaid(case: dict) -> str:
    font_name={"arial":"Arial","arial_bold":"Arial","georgia":"Georgia","times":"Times New Roman",
               "courier":"Courier New","segoe":"Segoe UI","verdana":"Verdana","calibri":"Calibri"}[case["font"]]
    theme={"theme":"base","themeVariables":{"fontFamily":font_name,"primaryColor":case["background"],
           "lineColor":case["edge"],"textColor":case["ink"]}}
    lines=["%%{init: "+json.dumps(theme,ensure_ascii=False)+"}%%",f'flowchart {case["layout"]}',
           f'  %% Synthetic Finnish-context graph: {case["context"]}']
    for i,node in enumerate(case["nodes"]):
        shape=node.get("shape") or case["shape"]
        label=node["label"].replace('"','&quot;')
        syntax={"box":f'["{label}"]',"round":f'("{label}")',"pill":f'(["{label}"])',
                "circle":f'(("{label}"))',"diamond":f'{{"{label}"}}',
                "hex":f'{{{{"{label}"}}}}',"text":f'["{label}"]'}[shape]
        lines.append(f'  n{i+1}{syntax}')
        fill=node.get("color") or case["palette"][i%len(case["palette"])]
        if shape=="text":
            style=f'fill:transparent,stroke:transparent,color:{case["ink"]},font-family:{font_name}'
        else:
            style=f'fill:{fill},stroke:{case["ink"]},color:{case["ink"]},font-family:{font_name}'
        lines.append(f'  style n{i+1} {style}')
    for edge in case["edges"]:
        arrow='---' if edge["direction"]=='undirected' else '-->'
        lines.append(f'  n{edge["source"]+1} {arrow}|{edge["label"]}| n{edge["target"]+1}')
    for i,edge in enumerate(case["edges"]):
        if edge["dashed"]:
            lines.append(f'  linkStyle {i} stroke-dasharray: 8 5')
    return "\n".join(lines)+"\n"


def main() -> None:
    ROOT.mkdir(exist_ok=True)
    manifest=[]; qa={}
    for case in CASES:
        result=render(case)
        slug=case["id"]
        (ROOT/(slug+".mmd")).write_text(mermaid(case),encoding="utf-8")
        (ROOT/(slug+".source.json")).write_text(json.dumps(case,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        manifest.append({"id":slug,"title":case["title"],"context":case["context"],
                         "style":case["shape"],"font":case["font"],"image":slug+".png","mermaid":slug+".mmd"})
        qa[slug]=result
    (ROOT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"text_qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f'Generated {len(manifest)} source graphs; text clipping and overlap checks passed')


if __name__=="__main__":
    main()
