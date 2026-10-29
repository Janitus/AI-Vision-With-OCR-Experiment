"""Create a compact Markdown and CSV overview from the full results matrix."""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT=Path(__file__).resolve().parent


def cell(value: str) -> str:
    return "—" if not value else f"{float(value)*100:.1f}%"


def main() -> None:
    with (ROOT/'results'/'matrix.csv').open(encoding='utf-8-sig',newline='') as stream:
        rows=list(csv.DictReader(stream))
    fields=[('approach','Approach'),('cases_scored','Cases'),
            ('macro.node_label_recall','Exact node labels'),
            ('macro.visible_text_recall','All visible text'),
            ('macro.topology_recall','Connections'),
            ('macro.arrow_accuracy','Arrow direction'),
            ('macro.relationship_exact','Edge labels'),
            ('macro.end_to_end_edge_recall','Fully correct edges')]
    lines=['# Ten-graph benchmark results','',
           'Synthetic Finnish-context graphs; 60 nodes and 70 source edges. All scores are exact except box matching (IoU ≥ 0.5).',
           '', '| '+' | '.join(name for _,name in fields)+' |',
           '| '+' | '.join('---' for _ in fields)+' |']
    for row in rows:
        lines.append('| '+' | '.join(row[key] if key in ('approach','cases_scored') else cell(row[key]) for key,_ in fields)+' |')
    lines += ['', 'Blank cells mean a metric has no denominator, never zero.',
              'The two OCR approaches locate colored boxes and read text but do not reconstruct edges.',
              'Those OCR rows use legacy rapidocr_onnxruntime 1.2.3 with bundled ch_PP-OCRv3 models, not a Finnish OCR configuration.',
              'Codex visual review was performed on the rendered images; the fixture generator was authored in the same session, so it is not a blind independent model evaluation.',
              'The exact Codex model identifier was not recorded, so that row is an unversioned visual review.',
              'The OCR-plus-Codex row keeps vision text unless OCR independently agrees. Its accuracy matches the vision row here; OCR primarily adds disagreement flags.',
              'Source graphs are synthetic tests in Finnish contexts, not factual diagrams of Finnish institutions or services.',
              'Some lines and labels overlap in the rendered images. Source-data scoring counts them even where they are hard to see.',
              '', '## Error counts by approach', '']
    lines += ['| Approach | Error type | Count |','| --- | --- | ---: |']
    error_rows=[]
    for row in rows:
        approach=row['approach']; counts=Counter()
        for path in (ROOT/'runs'/approach).glob('*.errors.json'):
            result=json.loads(path.read_text(encoding='utf-8'))
            counts.update(e['kind'] for e in result['errors'])
            for error in result['errors']:
                error_rows.append({'approach':approach,'case':path.name.removesuffix('.errors.json'),
                                   'kind':error['kind'],'expected':error.get('expected',''),
                                   'observed':error.get('observed',''),
                                   'truth_id':error.get('truth_id',''),
                                   'source':error.get('source',''),'target':error.get('target',''),
                                   'detail_json':json.dumps(error,ensure_ascii=False)})
        for kind,count in sorted(counts.items()):
            lines.append(f'| {approach} | {kind} | {count} |')
    lines += ['', 'See `results/matrix.csv` for every graph × metric and `runs/<approach>/<case>.errors.json` for every mismatch.', '']
    (ROOT/'results'/'summary.md').write_text('\n'.join(lines),encoding='utf-8')
    compact_fields=['approach','cases_scored']+[key for key,_ in fields if key not in ('approach','cases_scored')]
    with (ROOT/'results'/'matrix_compact.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=compact_fields); writer.writeheader()
        for row in rows:
            writer.writerow({key:row[key] for key in compact_fields})
    error_fields=['approach','case','kind','expected','observed','truth_id','source','target','detail_json']
    with (ROOT/'results'/'all_errors.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=error_fields); writer.writeheader();writer.writerows(error_rows)


if __name__=='__main__':
    main()
