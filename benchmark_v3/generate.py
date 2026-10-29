"""Generate ten complex, legible Finnish-context source graphs and image QA."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from benchmark_v2 import generate as base

base.ROOT=ROOT
base.W=1800
base.H=1100

LADDER=[(250,260),(680,260),(1120,260),(1550,260),(250,830),(680,830),(1120,830),(1550,830)]
GRID=[(270,220),(900,220),(1530,220),(270,550),(900,550),(1530,550),(270,880),(900,880),(1530,880)]
BRANCH=[(900,185),(320,390),(900,390),(1480,390),(320,720),(900,720),(1480,720),(900,955)]
RING=[(900+round(650*math.cos(i*math.pi/4)),550+round(390*math.sin(i*math.pi/4))) for i in range(8)]


def c(slug,title,context,layout,labels,links,shape,font,size,bg,ink,edge,palette,shapes=None,small=False):
    w=270 if shape not in ("circle","diamond") else 235
    nodes=[]
    for i,(label,(x,y)) in enumerate(zip(labels,layout)):
        item=base.n(label,x,y,shape=(shapes[i] if shapes else None),w=w,h=100)
        nodes.append(item)
    edges=[]
    for item in links:
        a,b,label,*flags=item
        flags=flags[0] if flags else {}
        edges.append(base.e(a,b,label,rotate=flags.get("rotate",False),
                            dashed=flags.get("dashed",False),
                            direction=flags.get("direction","source_to_target")))
    return {"id":slug,"title":title,"context":context,"layout":"LR" if layout in (LADDER,RING) else "TB",
            "shape":shape,"font":font,"size":size,"background":bg,"ink":ink,"edge":edge,
            "palette":palette,"nodes":nodes,"edges":edges,"small_edge_labels":small,
            "clear_text_background":True}


CASES=[
 c("paivystyksen_verkko","Päivystyksen hoitoverkko","Terveydenhuolto",LADDER,
   ["Potilaan yhteydenotto","Hoitaja","Päivystävä lääkäri","Erikoissairaanhoito","Puhelinneuvonta","Laboratorio","Kuvantaminen","Jatkohoito"],
   [(0,1,"kirjaa"),(1,2,"arvioi hoidon tarpeen"),(2,3,"lähettää"),(0,4,"ohjaa"),(4,5,"varaa ajan"),(5,6,"välittää näytteet"),(6,7,"toimittaa kuvat"),(1,5,"tilaa kokeet"),(2,6,"pyytää kuvauksen",{"rotate":True}),(5,2,"palauttaa tulokset",{"dashed":True}),(3,7,"suunnittelee",{"direction":"undirected"})],
   "round","segoe",22,"#ffffff","#17324b","#386f95",["#e6f2ff","#e5f6ed","#fff1d8","#eee5f9"]),
 c("ministerioiden_hanke","Ministeriöiden hankekierto","Valtionhallinto",GRID,
   ["Aloite","Valmisteluryhmä","Oikeudellinen arvio","Lausuntopyyntö","Ministeriö","Budjettitarkistus","Valtioneuvosto","Eduskunta","Toimeenpano"],
   [(0,1,"käynnistää"),(1,2,"selvittää"),(1,3,"laatii"),(3,4,"palautuu"),(2,5,"arvioi kulut"),(4,5,"sovittaa"),(4,6,"esittelee"),(5,7,"raportoi"),(6,7,"antaa esityksen"),(7,8,"hyväksyy"),(8,4,"seuranta",{"dashed":True}),(3,5,"kuulee",{"direction":"undirected"})],
   "box","georgia",22,"#ffffff","#222222","#333333",["#f5f5f5"]),
 c("saatutkimus","Säähavaintojen yhdistäminen","Sää ja tutkimus",BRANCH,
   ["Sääasema","Tuulianturi","Sademittari","Lämpöanturi","Raakahavainnot","Laatutarkistus","Malliajo","Ennuste"],
   [(1,0,"mittaa",{"rotate":True}),(2,0,"mittaa",{"rotate":True}),(3,0,"mittaa",{"rotate":True}),(0,4,"kokoaa"),(0,5,"lähettää"),(4,5,"vertaa"),(4,6,"syöttää"),(5,6,"vahvistaa"),(6,7,"tuottaa"),(7,5,"palaute",{"dashed":True}),(1,4,"varatieto",{"direction":"undirected"})],
   "text","verdana",23,"#fbfdff","#193247","#35677d",["#fbfdff"]),
 c("sahkohaorio","Sähköhäiriön tilannekuva","Energia",RING,
   ["Voimala","Kantaverkko","Sähköasema","Jakeluverkko","Kuluttaja","Mittari","Valvomo","Korjausryhmä"],
   [(0,1,"syöttää"),(1,2,"siirtää"),(2,3,"muuntaa"),(3,4,"jakaa"),(4,5,"kuittaa"),(5,6,"hälyttää"),(6,7,"lähettää"),(7,2,"korjaa"),(6,1,"valvoo",{"dashed":True}),(3,6,"vikatieto",{"rotate":True}),(0,4,"varasyöttö",{"direction":"undirected"})],
   "hex","segoe",22,"#17212b","#f3f8fa","#b4d6e5",["#294252","#335063","#2a4555","#355468"]),
 c("junaliikenteen_ohjaus","Junaliikenteen ohjaus","Liikenne",LADDER,
   ["Matkustaja","Aikataulu","Laituri","Juna","Liikenteenohjaus","Vaihtoasema","Häiriöviesti","Määränpää"],
   [(0,1,"tarkistaa"),(1,2,"osoittaa"),(2,3,"ohjaa"),(0,4,"lähettää kyselyn"),(4,5,"vahvistaa vaihdon"),(5,6,"ilmoittaa"),(6,7,"päivittää"),(1,5,"reitittää"),(2,6,"varoitus",{"rotate":True}),(4,2,"muuttaa laiturin",{"dashed":True}),(3,7,"saapuu"),(6,3,"tilanne",{"direction":"undirected"})],
   "circle","arial_bold",21,"#f8fbff","#173452","#2b6eaa",["#dcecff","#e1f5eb","#fff0d8","#eee4fb"]),
 c("rokotusketju","Rokotusketjun seuranta","Kansanterveys",GRID,
   ["Varaus","Asiakas","Hoitaja","Annos","Rokotuspiste","Kirjaus","Seuranta","Rekisteri","Muistutus"],
   [(0,1,"vahvistaa"),(1,2,"saapuu"),(2,3,"tarkistaa"),(3,4,"toimitetaan"),(4,5,"merkitsee"),(5,6,"käynnistää"),(5,7,"siirtää tiedon"),(7,8,"lähettää"),(8,1,"kutsuu uudelleen",{"dashed":True}),(2,5,"kirjaa erän"),(6,8,"tarvittaessa",{"direction":"undirected"})],
   "box","calibri",23,"#fffefa","#273934","#548674",["#e1f3e9","#e9f0ff","#fff1dc","#f0e5f6"],
   shapes=["pill","text","box","diamond","pill","box","text","hex","round"]),
 c("tutkimusjulkaisu","Tutkimusjulkaisun työnkulku","Tutkimus",BRANCH,
   ["Tutkimuskysymys","Aineiston keruu","Eettinen arvio","Mittaus","Tallennus","Analyysi","Vertaisarvio","Julkaisu"],
   [(0,1,"ohjaa"),(0,2,"edellyttää"),(1,3,"tuottaa"),(2,3,"hyväksyy"),(3,4,"arkistoi"),(4,5,"mahdollistaa"),(5,6,"lähettää"),(6,7,"suosittaa"),(6,5,"palauttaa korjattavaksi",{"dashed":True}),(4,7,"avoin aineisto",{"direction":"undirected"})],
   "pill","times",23,"#ffffff","#242424","#333333",["#ffffff"]),
 c("kaukolainaus","Kaukolainauksen palveluverkko","Kirjastot",RING,
   ["Lukija","Varaus","Lähikirjasto","Keskuskirjasto","Kuljetus","Noutopiste","Laina","Palautus"],
   [(0,1,"pyytää"),(1,2,"kohdistaa"),(2,3,"tiedustelee"),(3,4,"lähettää"),(4,5,"toimittaa"),(5,6,"luovuttaa"),(6,7,"palautetaan"),(7,2,"vastaanottaa"),(0,5,"noutoilmoitus",{"dashed":True}),(1,3,"saatavuus",{"rotate":True}),(3,7,"varatieto",{"direction":"undirected"})],
   "text","courier",22,"#fffdf8","#49342c","#8a604e",["#fffdf8"]),
 c("tulvaviestinta","Tulvatilanteen viestintä","Pelastustoimi",GRID,
   ["Sadehavainto","Hätäkeskus","Pelastuslaitos","Kuntalainen","Tilannekeskus","Vesilaitos","Evakuointi","Sairaala","Tiedote"],
   [(0,1,"hälyttää"),(1,2,"välittää"),(0,3,"varoitus"),(3,4,"ilmoittaa"),(2,4,"päivittää"),(4,5,"pyytää arviota"),(4,6,"määrää"),(5,7,"turvaa veden"),(6,7,"ohjaa potilaita"),(7,8,"raportoi"),(8,3,"julkaisee"),(2,6,"lähettää yksiköt",{"dashed":True}),(1,4,"yhteys",{"direction":"undirected"})],
   "box","arial",22,"#16232b","#f3f6f7","#b6d1dc",["#24404e","#2a4754","#304b56"]),
 c("veron_oikaisu","Verotuksen oikaisuprosessi","Verotus",LADDER,
   ["Verovelvollinen","Ilmoitus","Tarkastus","Päätös","Lisäselvitys","Oikaisupyyntö","Käsittely","Lopputulos"],
   [(0,1,"antaa"),(1,2,"siirtää"),(2,3,"ratkaisee"),(0,4,"täydentää"),(4,5,"liitetään"),(5,6,"käynnistää"),(6,7,"vahvistaa"),(2,6,"tarkistaa uudelleen"),(3,5,"voi johtaa"),(6,2,"palauttaa tarkastukseen",{"dashed":True}),(1,4,"liittyy",{"direction":"undirected"})],
   "diamond","georgia",21,"#ffffff","#282828","#333333",["#ffffff"],
   shapes=["text","box","diamond","diamond","text","box","diamond","box"]),
]


def plan_labels(case):
    canvas=Image.new("RGB",(base.W,base.H));draw=ImageDraw.Draw(canvas)
    nodes=[base.shape_box(n) for n in case["nodes"]]
    prior=[]
    title=draw.textbbox((38,32),case["title"],font=base.font("arial_bold",34))
    edge_font=base.font(case["font"],21)
    for i,edge in enumerate(case["edges"]):
        start,end=base.line_ends(case["nodes"][edge["source"]],case["nodes"][edge["target"]])
        dx,dy=end[0]-start[0],end[1]-start[1];length=max(1,math.hypot(dx,dy))
        perp=(-dy/length,dx/length)
        angle=0
        if edge["rotate"]:
            degrees=math.degrees(math.atan2(dy,dx))
            if degrees>90:degrees-=180
            if degrees<-90:degrees+=180
            angle=-degrees
        patch=base.label_patch(edge["label"],edge_font,case["ink"],case["background"],angle)
        candidates=[]
        for t in (.5,.35,.65,.2,.8):
            mx,my=start[0]+dx*t,start[1]+dy*t
            for offset in (-62,62,-105,105,0,-155,155,-210,210):
                x=round(mx+perp[0]*offset);y=round(my+perp[1]*offset)
                bb=(round(x-patch.width/2),round(y-patch.height/2),round(x+patch.width/2),round(y+patch.height/2))
                if bb[0]<20 or bb[1]<85 or bb[2]>base.W-20 or bb[3]>base.H-20:continue
                if base.intersects(bb,title,10):continue
                if any(base.intersects(bb,n,8) for n in nodes):continue
                if any(base.intersects(bb,old,12) for old in prior):continue
                score=abs(t-.5)*100+abs(offset)+(.1 if offset==0 else 0)
                candidates.append((score,(x,y),bb))
        if not candidates:raise ValueError(f'{case["id"]}: no safe label position for edge {i} {edge["label"]}')
        _,xy,bb=min(candidates,key=lambda item:item[0])
        edge["label_xy"]=xy;prior.append(bb)


def main():
    ROOT.mkdir(exist_ok=True)
    manifest=[];qa={}
    for case in CASES:
        plan_labels(case)
        result=base.render(case)
        slug=case["id"]
        (ROOT/(slug+".mmd")).write_text(base.mermaid(case),encoding="utf-8")
        (ROOT/(slug+".source.json")).write_text(json.dumps(case,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        manifest.append({"id":slug,"title":case["title"],"context":case["context"],
                         "style":case["shape"],"font":case["font"],"image":slug+".png","mermaid":slug+".mmd"})
        qa[slug]=result
    (ROOT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"text_qa.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Generated",len(manifest),"complex source graphs with no text clipping or overlap")


if __name__=="__main__":main()
