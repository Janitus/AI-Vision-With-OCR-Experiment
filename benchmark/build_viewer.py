"""Package source and inferred benchmark graphs into one self-contained viewer."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path


ROOT=Path(__file__).resolve().parent
APPROACHES=('codex_vision','codex_plus_rapidocr','rapidocr_full','rapidocr_crops')


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    cases={}
    for case in manifest:
        name=case['id']
        image='data:image/png;base64,'+base64.b64encode((ROOT/case['image']).read_bytes()).decode('ascii')
        approaches={}
        for approach in APPROACHES:
            base=ROOT/'runs'/approach
            graph=json.loads((base/f'{name}.graph.json').read_text(encoding='utf-8'))
            result=json.loads((base/f'{name}.errors.json').read_text(encoding='utf-8'))
            mmd=(base/f'{name}.mmd').read_text(encoding='utf-8')
            approaches[approach]={'graph':graph,'errors':result['errors'],'mmd':mmd}
        cases[name]={'title':case['context'],'image':image,
                     'sourceMmd':(ROOT/case['source']).read_text(encoding='utf-8'),
                     'approaches':approaches}
    template=(ROOT/'viewer-template.html').read_text(encoding='utf-8')
    payload=json.dumps({'cases':cases},ensure_ascii=True,separators=(',',':')).replace('</','<\\/')
    output=template.replace('__DATA_JSON__',payload)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(output,encoding='utf-8')
    print(f'{args.out} ({args.out.stat().st_size} bytes)')


if __name__=='__main__':
    main()
