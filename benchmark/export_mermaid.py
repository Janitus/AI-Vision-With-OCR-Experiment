"""Export every inferred benchmark graph as Mermaid source."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from graph_extract import mermaid


def main() -> None:
    count=0
    for path in (ROOT/'runs').glob('*/*.graph.json'):
        graph=json.loads(path.read_text(encoding='utf-8'))
        path.with_suffix('').with_suffix('.mmd').write_text(mermaid(graph),encoding='utf-8')
        count+=1
    print(f'Exported {count} inferred Mermaid graphs')


if __name__=='__main__':
    main()
