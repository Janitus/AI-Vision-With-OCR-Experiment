"""Codex visual readings made from the rendered PNGs, without loading truth JSON.

Positions are visual locations (top/bottom, left/middle/right). An unknown edge
label records an unreadable line; missing edges remain visible in evaluation.
"""
from __future__ import annotations

import json
import math
from pathlib import Path


HERE=Path(__file__).resolve().parent
CENTERS={"TL":(180,135),"TM":(600,135),"TR":(1020,135),
         "BL":(180,520),"BM":(600,520),"BR":(1020,520)}
LABELS={
 "terveydenhuolto":{"TL":"Tulokset","TM":"Lähete","TR":"Laboratorio","BL":"Terveysasema","BM":"Potilas","BR":"Erikoissairaanhoito"},
 "ministeriot":{"TL":"Ministeriö","TM":"Eduskunta","TR":"Asetus","BL":"Valtioneuvosto","BM":"Virasto","BR":"Lausunto"},
 "pelastustoimi":{"TL":"Hälytys","TM":"Johtokeskus","TR":"Hätäkeskus","BL":"Ensihoito","BM":"Pelastuslaitos","BR":"Tilannekuva"},
 "rautatieliikenne":{"TL":"Lippu","TM":"Liikenteenohjaus","TR":"Aikataulu","BL":"Juna","BM":"Matkustaja","BR":"Asema"},
 "koulutus":{"TL":"Opettaja","TM":"Oppilas","TR":"Opetussuunnitelma","BL":"Arviointi","BM":"Kurssi","BR":"Koulu"},
 "ymparisto":{"TL":"Näyte","TM":"Vesistö","TR":"Mittausasema","BL":"Analyysi","BM":"Kunta","BR":"Raportti"},
 "verotus":{"TL":"Ilmoitus","TM":"Maksu","TR":"Päätös","BL":"Verovelvollinen","BM":"Oikaisu","BR":"Verohallinto"},
 "kirjastot":{"TL":"Kirjasto","TM":"Asiakas","TR":"Laina","BL":"Palautus","BM":"Varaus","BR":"Teos"},
 "energia":{"TL":"Voimala","TM":"Ennuste","TR":"Kuluttaja","BL":"Sähköverkko","BM":"Mittari","BR":"Varasto"},
 "kuntapalvelut":{"TL":"Palvelupiste","TM":"Hakemus","TR":"Asiakirja","BL":"Päätös","BM":"Kuntalainen","BR":"Arkisto"},
}
# Each tuple is visible source, target, literal edge text, direction.
EDGES={
 "terveydenhuolto":[("TL","TM","lähettää","source_to_target"),("BR","BM","tutkii","source_to_target"),
    ("BM","BL","lähettää","source_to_target"),("BL","TM","kirjaa","source_to_target"),
    ("TR","BL","tutkii","source_to_target"),("TL","BR","tutkii","source_to_target")],
 "ministeriot":[("TM","TL","antaa","source_to_target"),("TM","TR","lausuu","source_to_target"),
    ("BL","TM","valmistelee","source_to_target"),("BL","TR","ohjaa","source_to_target"),
    ("TL","BR","ohjaa","source_to_target"),("BM","TR","valmistelee","source_to_target"),
    ("BM","BR","antaa","source_to_target")],
 "pelastustoimi":[("TL","TR","unknown","unknown"),("TL","BL","päivittää","source_to_target"),
    ("BL","TM","päivittää","source_to_target"),("TR","BL","hälyttää","source_to_target"),
    ("BM","BL","johtaa","source_to_target"),("BM","TR","tukee","source_to_target"),
    ("TR","BR","välittää","source_to_target")],
 "rautatieliikenne":[("TL","TM","unknown","unknown"),("TM","TR","yhdistää","source_to_target"),
    ("BL","BM","vahvistaa","source_to_target"),("BM","BR","unknown","source_to_target"),
    ("BM","TM","ohjaa","source_to_target"),("TR","BL","yhdistää","source_to_target"),
    ("BR","TL","ohjaa","source_to_target")],
 "koulutus":[("TM","TL","unknown","source_to_target"),("TR","TM","opettaa","source_to_target"),
    ("TL","BL","suorittaa","source_to_target"),("TL","BM","kuvaa","source_to_target"),
    ("TM","BM","ohjaa","source_to_target"),("TM","BR","opettaa","source_to_target"),
    ("TR","BM","opettaa","source_to_target")],
 "ymparisto":[("TM","TL","unknown","unknown"),("TM","TR","kerää","source_to_target"),
    ("BL","TL","raportoi","source_to_target"),("TL","BR","seuraa","source_to_target"),
    ("TR","BR","mittaa","source_to_target"),("BL","BR","mittaa","source_to_target"),
    ("BR","BM","mittaa","source_to_target")],
 "verotus":[("TM","TL","määrää","source_to_target"),("TM","TR","unknown","source_to_target"),
    ("BL","BM","tarkistaa","source_to_target"),("BM","BR","unknown","source_to_target"),
    ("BL","TM","maksaa","source_to_target"),("BL","TR","lähettää","source_to_target"),
    ("BR","TL","lähettää","source_to_target")],
 "kirjastot":[("TL","TR","unknown","source_to_target"),("TR","TM","luetteloi","source_to_target"),
    ("TL","BL","lainaa","source_to_target"),("TL","BM","välittää","source_to_target"),
    ("TM","BL","välittää","source_to_target"),("BM","BL","unknown","source_to_target"),
    ("BR","BM","unknown","unknown")],
 "energia":[("TL","TM","tasaa","source_to_target"),("BL","BM","siirtää","source_to_target"),
    ("TM","BM","ohjaa","source_to_target"),("TR","BM","tasaa","source_to_target"),
    ("BR","TM","tasaa","source_to_target"),("BR","TL","tuottaa","source_to_target"),
    ("TL","BR","ohjaa","source_to_target")],
 "kuntapalvelut":[("TL","TR","unknown","unknown"),("BL","TM","käsittelee","source_to_target"),
    ("TR","BL","lähettää","source_to_target"),("TM","BR","vahvistaa","source_to_target"),
    ("BM","TR","vahvistaa","source_to_target"),("BM","BL","lähettää","source_to_target"),
    ("TR","BR","jättää","source_to_target")],
}


def points(a: str,b: str) -> list[list[int]]:
    ax,ay=CENTERS[a]; bx,by=CENTERS[b]
    dx,dy=bx-ax,by-ay
    t=min(103/max(abs(dx),1),41/max(abs(dy),1))
    return [[round(ax+dx*t),round(ay+dy*t)],[round(bx-dx*t),round(by-dy*t)]]


def main() -> None:
    for case,labels in LABELS.items():
        nodes=[]
        for pos,label in labels.items():
            x,y=CENTERS[pos]
            nodes.append({"id":pos,"label":label,"type":"rounded_rectangle",
                          "bbox":[x-103,y-41,x+103,y+41],"confidence":0.9})
        edges=[]; uncertainties=[]
        for a,b,rel,direction in EDGES[case]:
            edges.append({"source":a,"target":b,"relationship":rel,"direction":direction,
                          "points":points(a,b),"confidence":0.75 if rel!="unknown" else 0.45})
            if rel=="unknown" or direction=="unknown":
                uncertainties.append({"kind":"unreadable_or_obscured_edge","source":a,"target":b,
                                      "detail":"Visible segment, but label or arrowhead is obscured."})
        title={"terveydenhuolto":"Terveydenhuolto","ministeriot":"Ministeriöt","pelastustoimi":"Pelastustoimi",
               "rautatieliikenne":"Rautatieliikenne","koulutus":"Koulutus","ymparisto":"Ympäristö",
               "verotus":"Verotus","kirjastot":"Kirjastot","energia":"Energia","kuntapalvelut":"Kuntapalvelut"}[case]
        rendered_title=title+" · synteettinen testikaavio"
        output={"source":"codex_visual_review","image":case+".png","nodes":nodes,"edges":edges,
                "rendered_title":rendered_title,
                "visible_text":[rendered_title]+list(labels.values())+[e["relationship"] for e in edges if e["relationship"]!="unknown"],
                "uncertainties":uncertainties,
                "note":"Read from the rendered image. The fixture generator was authored in the same session, so this is not a blind independent model evaluation."}
        (HERE/(case+".json")).write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Wrote {len(LABELS)} visual reviews")


if __name__=="__main__":
    main()
