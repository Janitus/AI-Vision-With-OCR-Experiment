"""Generate ten synthetic Finnish-context Mermaid graphs and rendered PNG fixtures.

The fixtures test extraction, not the factual accuracy of the relationships.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
CONTEXTS = [
    ("terveydenhuolto", "Terveydenhuolto", ["Potilas", "Terveysasema", "Lähete", "Laboratorio", "Erikoissairaanhoito", "Tulokset"], ["lähettää", "tutkii", "kirjaa", "välittää", "konsultoi"]),
    ("ministeriot", "Ministeriöt", ["Eduskunta", "Valtioneuvosto", "Ministeriö", "Virasto", "Asetus", "Lausunto"], ["ohjaa", "valmistelee", "antaa", "lausuu", "käsittelee"]),
    ("pelastustoimi", "Pelastustoimi", ["Hälytys", "Hätäkeskus", "Pelastuslaitos", "Ensihoito", "Johtokeskus", "Tilannekuva"], ["hälyttää", "välittää", "johtaa", "päivittää", "tukee"]),
    ("rautatieliikenne", "Rautatieliikenne", ["Matkustaja", "Asema", "Juna", "Aikataulu", "Lippu", "Liikenteenohjaus"], ["käyttää", "näyttää", "ohjaa", "vahvistaa", "yhdistää"]),
    ("koulutus", "Koulutus", ["Oppilas", "Koulu", "Opettaja", "Opetussuunnitelma", "Kurssi", "Arviointi"], ["opettaa", "ohjaa", "arvioi", "kuvaa", "suorittaa"]),
    ("ymparisto", "Ympäristö", ["Vesistö", "Mittausasema", "Näyte", "Analyysi", "Raportti", "Kunta"], ["kerää", "mittaa", "analysoi", "raportoi", "seuraa"]),
    ("verotus", "Verotus", ["Verovelvollinen", "Ilmoitus", "Verohallinto", "Päätös", "Maksu", "Oikaisu"], ["lähettää", "käsittelee", "määrää", "maksaa", "tarkistaa"]),
    ("kirjastot", "Kirjastot", ["Asiakas", "Kirjasto", "Teos", "Varaus", "Laina", "Palautus"], ["varaa", "lainaa", "luetteloi", "palauttaa", "välittää"]),
    ("energia", "Energia", ["Voimala", "Sähköverkko", "Mittari", "Kuluttaja", "Ennuste", "Varasto"], ["tuottaa", "siirtää", "mittaa", "ohjaa", "tasaa"]),
    ("kuntapalvelut", "Kuntapalvelut", ["Kuntalainen", "Hakemus", "Palvelupiste", "Päätös", "Asiakirja", "Arkisto"], ["jättää", "käsittelee", "vahvistaa", "tallentaa", "lähettää"]),
]
POSITIONS = [(180, 135), (600, 135), (1020, 135), (180, 520), (600, 520), (1020, 520)]
BOX_W, BOX_H = 206, 82
PALETTE = [(220, 246, 190), (201, 229, 251), (255, 225, 178),
           (232, 212, 246), (255, 239, 155), (205, 240, 230)]


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)


def edge_ends(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[float, float], tuple[float, float]]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = min((BOX_W / 2) / max(abs(dx), 1), (BOX_H / 2) / max(abs(dy), 1))
    u = min((BOX_W / 2) / max(abs(dx), 1), (BOX_H / 2) / max(abs(dy), 1))
    return (a[0] + dx * t, a[1] + dy * t), (b[0] - dx * u, b[1] - dy * u)


def render(spec: dict, path: Path) -> None:
    image = Image.new("RGB", (1200, 700), "white")
    draw = ImageDraw.Draw(image)
    label_font, title_font, edge_font = font(22), font(28), font(19)
    draw.text((26, 22), f"{spec['title']} · synteettinen testikaavio", fill=(25, 32, 43), font=title_font)
    by_id = {n["id"]: n for n in spec["nodes"]}
    for e in spec["edges"]:
        start, end = edge_ends(tuple(by_id[e["source"]]["center"]), tuple(by_id[e["target"]]["center"]))
        draw.line((*start, *end), fill=(24, 34, 45), width=4)
        if e["direction"] == "source_to_target":
            angle = math.atan2(end[1] - start[1], end[0] - start[0])
            size = 17
            left = (end[0] - size * math.cos(angle - .46), end[1] - size * math.sin(angle - .46))
            right = (end[0] - size * math.cos(angle + .46), end[1] - size * math.sin(angle + .46))
            draw.polygon([end, left, right], fill=(24, 34, 45))
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        e["points"] = [[round(start[0]), round(start[1])], [round(end[0]), round(end[1])]]
        # Offset parallel/crossing labels slightly; source data does not encode this layout.
        shift = e.get("label_shift", 0)
        if abs(end[0] - start[0]) > abs(end[1] - start[1]):
            my += -23 + shift
        else:
            mx += 17 + shift
        bb = draw.textbbox((mx, my), e["relationship"], font=edge_font, anchor="mm")
        draw.rectangle((bb[0]-5, bb[1]-3, bb[2]+5, bb[3]+3), fill="white")
        draw.text((mx, my), e["relationship"], fill=(28, 34, 43), font=edge_font, anchor="mm")
    for i, n in enumerate(spec["nodes"]):
        x, y = n["center"]
        x1, y1, x2, y2 = x-BOX_W//2, y-BOX_H//2, x+BOX_W//2, y+BOX_H//2
        n["bbox"] = [x1, y1, x2, y2]
        draw.rounded_rectangle((x1, y1, x2, y2), radius=7, fill=PALETTE[i], outline=(54, 64, 76), width=3)
        label = n["label"]
        if len(label) > 17 and " " in label:
            cut = label.rfind(" ", 0, 18)
            lines = [label[:cut], label[cut+1:]]
        else:
            lines = [label]
        line_height = 26
        top = y - line_height * len(lines)/2 + line_height/2
        for j, line in enumerate(lines):
            draw.text((x, top + j*line_height), line, fill=(20, 28, 37), font=label_font, anchor="mm")
    image.save(path)


def build_case(index: int, context: tuple) -> dict:
    slug, title, labels, relationships = context
    rng = random.Random(20261029 + index * 971)
    shuffled_positions = rng.sample(POSITIONS, len(labels))
    nodes = [{"id":f"n{i+1}", "label":label, "type":"rounded_rectangle", "center":list(shuffled_positions[i]), "confidence":1.0}
             for i, label in enumerate(labels)]
    # A random spanning tree gives every box at least one visible connection.
    order = rng.sample(range(len(nodes)), len(nodes))
    pairs = set()
    for i in range(1, len(order)):
        a, b = order[i], rng.choice(order[:i])
        pairs.add(tuple(sorted((a,b))))
    while len(pairs) < 7:
        a, b = rng.sample(range(len(nodes)), 2)
        pairs.add(tuple(sorted((a,b))))
    edges = []
    for i, (a, b) in enumerate(sorted(pairs)):
        if rng.random() < .5:
            a, b = b, a
        edges.append({"source":nodes[a]["id"], "target":nodes[b]["id"],
                      "relationship":relationships[(i+index) % len(relationships)],
                      "direction":"undirected" if i == 6 and index % 3 == 0 else "source_to_target",
                      "confidence":1.0})
    return {"id":slug,"title":title,"rendered_title":f"{title} · synteettinen testikaavio",
            "synthetic":True,"nodes":nodes,"edges":edges}


def mermaid(spec: dict) -> str:
    lines = ["flowchart TB", f"  %% Synthetic Finland-themed benchmark: {spec['title']}"]
    lines += [f'  {n["id"]}["{n["label"]}"]' for n in spec["nodes"]]
    for e in spec["edges"]:
        arrow = "-->" if e["direction"] == "source_to_target" else "---"
        lines.append(f'  {e["source"]} {arrow}|{e["relationship"]}| {e["target"]}')
    return "\n".join(lines) + "\n"


def main() -> None:
    ROOT.mkdir(exist_ok=True)
    manifest = []
    for index, context in enumerate(CONTEXTS):
        spec = build_case(index, context)
        render(spec, ROOT / f"{spec['id']}.png")
        (ROOT / f"{spec['id']}.mmd").write_text(mermaid(spec), encoding="utf-8")
        (ROOT / f"{spec['id']}.truth.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        manifest.append({"id":spec["id"],"context":spec["title"],"image":f"{spec['id']}.png",
                         "source":f"{spec['id']}.mmd","truth":f"{spec['id']}.truth.json"})
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"Generated {len(manifest)} cases")


if __name__ == "__main__":
    main()
