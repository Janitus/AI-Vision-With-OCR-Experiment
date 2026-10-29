"""Create anonymized, isolated inputs for the two fresh vision tasks."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    mapping = {}
    for index, case in enumerate(manifest, 1):
        anon = f"case_{index:02d}"
        mapping[anon] = case["id"]
        for approach in ("blind_vision", "blind_fusion"):
            directory = ROOT / approach / "images"
            directory.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / case["image"], directory / f"{anon}.png")
        ocr_input = ROOT / "blind_fusion" / "ocr"
        ocr_input.mkdir(parents=True, exist_ok=True)
        for engine in ("rapid_v6_medium_fi",):
            source = ROOT / "runs" / engine / f"{case['id']}.json"
            if source.exists():
                data = json.loads(source.read_text(encoding="utf-8"))
                data["image"] = f"{anon}.png"
                (ocr_input / f"{anon}.{engine}.json").write_text(
                    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
    (ROOT / "blind_mapping.json").write_text(
        json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Prepared", len(mapping), "blind images per approach")


if __name__ == "__main__":
    main()
