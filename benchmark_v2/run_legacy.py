"""Run the previous bundled RapidOCR model as a baseline on the new images."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/".vendor"))
from rapidocr_onnxruntime import RapidOCR


def main():
    engine=RapidOCR()
    outdir=ROOT/"runs"/"legacy_rapid_v3"
    outdir.mkdir(parents=True,exist_ok=True)
    for path in sorted(ROOT.glob("*.png")):
        if path.name=="contact-sheet.png":
            continue
        result,_=engine(str(path))
        observations=[{"text":value,"confidence":float(confidence),"polygon":polygon}
                      for polygon,value,confidence in (result or [])]
        (outdir/f"{path.stem}.json").write_text(json.dumps({"image":path.name,
            "engine":"rapidocr_onnxruntime 1.2.3 bundled ch_PP-OCRv3",
            "observations":observations},ensure_ascii=False,indent=2),encoding="utf-8")
        print(path.stem,len(observations),flush=True)


if __name__=="__main__":
    main()
