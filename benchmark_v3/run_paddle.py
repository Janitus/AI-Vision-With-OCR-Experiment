"""Run PaddleOCR PP-OCRv5 Finnish on the approved ten images."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ["PADDLE_PDX_CACHE_HOME"] = str(ROOT.parent / "benchmark_v2" / "models" / "paddle")
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ.pop("SSLKEYLOGFILE", None)
sys.path.insert(0, str(ROOT.parent / ".vendor_paddle"))
from paddleocr import PaddleOCR


def main():
    engine = PaddleOCR(lang="fi", ocr_version="PP-OCRv5", use_doc_orientation_classify=False,
                       use_doc_unwarping=False, use_textline_orientation=False,
                       text_rec_score_thresh=0.0, enable_mkldnn=False)
    outdir = ROOT / "runs" / "paddle_v5_fi"
    outdir.mkdir(parents=True, exist_ok=True)
    for path in sorted(ROOT.glob("*.png")):
        if path.name == "contact-sheet.png":
            continue
        result = engine.predict(str(path))[0]
        data = result.json["res"]
        observations=[]
        for polygon, value, confidence in zip(data["rec_polys"], data["rec_texts"], data["rec_scores"]):
            observations.append({"text":value,"confidence":float(confidence),
                                 "polygon":polygon.tolist() if hasattr(polygon,"tolist") else polygon})
        (outdir/f"{path.stem}.json").write_text(json.dumps({"image":path.name,
             "engine":"PaddleOCR 3.7 PP-OCRv5 fi", "observations":observations},
             ensure_ascii=False,indent=2),encoding="utf-8")
        print(path.stem,len(observations),flush=True)


if __name__=="__main__":
    main()
