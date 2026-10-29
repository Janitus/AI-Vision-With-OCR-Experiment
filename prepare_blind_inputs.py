"""Recreate anonymous image and OCR inputs without copying ground truth beside them."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "benchmark_v2"


def main():
    source_files = sorted(SOURCE.glob("*.source.json"))
    if len(source_files) != 10:
        raise SystemExit(f"Expected ten source cases, found {len(source_files)}")
    for i, source in enumerate(source_files, 1):
        slug = source.name.removesuffix(".source.json")
        case = f"case_{i:02}"
        image = SOURCE / f"{slug}.png"
        ocr = SOURCE / "runs" / "rapid_v6_medium_fi" / f"{slug}.json"
        if not image.is_file() or not ocr.is_file():
            raise SystemExit(f"Missing image or OCR output for {slug}")
        for folder in (ROOT / "blind_vision" / "images", ROOT / "blind_fusion" / "images"):
            folder.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(image, folder / f"{case}.png")
        observations = json.loads(ocr.read_text(encoding="utf-8"))
        observations["image"] = f"{case}.png"
        target = ROOT / "blind_fusion" / "ocr" / f"{case}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(observations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Prepared ten anonymous image-only and OCR-assisted input pairs")


if __name__ == "__main__":
    main()
