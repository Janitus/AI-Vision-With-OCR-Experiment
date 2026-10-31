"""Check blind agents' self-reported file access against assigned folders."""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
reports={}
for approach,agent,subdirs in (("blind_vision","vision",("images","predictions")),
                               ("blind_fusion","fusion",("images","ocr","predictions"))):
    log=(ROOT/approach/"access_log.txt").read_text(encoding="utf-8")
    root=(Path.home()/".codex"/"visualizations"/"2026"/"10"/"29"/"01a186fe-f58d-76a0-9d80-e94fc3032f66"/"blind_v5"/agent)
    prefixes=[str(root/d).lower() for d in subdirs]+[str(root/"access_log.txt").lower()]
    paths=[]
    for line in log.splitlines():
        match=re.search(r"[A-Za-z]:\\[^|]+",line)
        if match:
            path=match.group(0).strip().lower()
            paths.append(path)
            if not any(path==p or path.startswith(p+"\\") for p in prefixes):
                raise ValueError(f"Unexpected self-reported access in {approach}: {path}")
    predictions=list((ROOT/approach/"predictions").glob("case_*.json"))
    if len(predictions)!=12:
        raise ValueError(f"Expected 12 predictions, got {len(predictions)} for {approach}")
    reports[approach]={"prediction_count":len(predictions),"reported_path_count":len(paths),
                       "all_reported_paths_within_assigned_inputs_or_outputs":True,
                       "limitation":"self-reported access log; no filesystem-enforced isolation"}
(ROOT/"session_audit.json").write_text(json.dumps(reports,indent=2)+"\n",encoding="utf-8")
print(reports)
