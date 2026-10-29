"""Build a self-contained source-graph viewer without running the benchmark."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path


ROOT=Path(__file__).resolve().parent


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    cases=[]
    for entry in manifest:
        source=json.loads((ROOT/(entry['id']+'.source.json')).read_text(encoding='utf-8'))
        cases.append({**entry,
                      'image':'data:image/png;base64,'+base64.b64encode((ROOT/entry['image']).read_bytes()).decode('ascii'),
                      'mermaid':(ROOT/entry['mermaid']).read_text(encoding='utf-8'),
                      'nodes':len(source['nodes']),'edges':len(source['edges'])})
    template=(ROOT/'preview_template.html').read_text(encoding='utf-8')
    payload=json.dumps(cases,ensure_ascii=True,separators=(',',':')).replace('</','<\\/')
    output=template.replace('__DATA_JSON__',payload)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(output,encoding='utf-8')
    print(f'Wrote {len(cases)} diagrams to {args.out} ({args.out.stat().st_size} bytes)')


if __name__=='__main__':
    main()
