"""Run Finnish PP-OCRv6 on every reviewed fixture and save unedited OCR observations."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / ".vendor_rapidocr"))
from rapidocr import RapidOCR
from rapidocr.utils.typings import ModelType, OCRVersion


def main():
    params = {
        "Global.model_root_dir": str(ROOT.parent / "benchmark_v2" / "models" / "rapid"),
        "Global.use_cls": False,
        "Global.text_score": 0.0,
        "Global.log_level": "error",
        "Det.lang_type": "fi",
        "Det.model_type": ModelType.MEDIUM,
        "Det.ocr_version": OCRVersion.PPOCRV6,
        "Rec.lang_type": "fi",
        "Rec.model_type": ModelType.MEDIUM,
        "Rec.ocr_version": OCRVersion.PPOCRV6,
    }
    engine = RapidOCR(params=params)
    outdir = ROOT / "runs" / "rapid_v6_medium_fi"
    outdir.mkdir(parents=True, exist_ok=True)
    for path in sorted(ROOT.glob("*.png")):
        if path.name == "contact-sheet.png":
            continue
        result = engine(str(path))
        observations = []
        for box, value, confidence in zip(result.boxes if result.boxes is not None else [],
                                           result.txts or [], result.scores or []):
            observations.append({"text": value, "confidence": float(confidence),
                                 "polygon": box.tolist()})
        (outdir / f"{path.stem}.json").write_text(json.dumps({"image": path.name,
            "engine": "RapidOCR 3.10.0 PP-OCRv6 medium fi", "observations": observations},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(path.stem, len(observations), flush=True)


if __name__ == "__main__":
    main()
