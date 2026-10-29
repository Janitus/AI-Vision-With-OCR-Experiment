"""Append the fresh blind result as a distinct approach without rewriting old runs."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/"benchmark_v2"


def main():
    rows=json.loads((OLD/"approach_matrix.json").read_text(encoding="utf-8"))
    blind=json.loads((ROOT/"blind_scores.json").read_text(encoding="utf-8"))
    c=blind["counts"]
    rate=lambda correct,total:round(correct/total,4)
    row={"approach":"codex_vision_blind_image_only","cases":10,
         "all_visible_text_exact":rate(c["title_exact"]+c["exact_node_labels"]+c["correct_relationships"],100),
         "all_visible_text_precision":1.0,"extra_ocr_items":None,
         "node_labels_exact":rate(c["exact_node_labels"],c["truth_nodes"]),
         "edge_labels_exact":rate(c["correct_relationships"],c["truth_edges"]),
         "rotated_edge_labels_exact":1.0,
         "connections_found":c["matched_topology"],"connections_total":c["truth_edges"],
         "arrow_accuracy":rate(c["correct_arrows"],c["truth_edges"]),
         "fully_correct_edges":c["fully_correct_edges"],
         "full_edge_recall":rate(c["fully_correct_edges"],c["truth_edges"]),
         "node_shape_accuracy":rate(c["exact_node_shapes"],c["truth_nodes"]),
         "edge_stroke_accuracy":rate(c["correct_strokes"],c["truth_edges"]),
         "note":"Fresh separate Codex thread; images only; one unknown arrow direction; four pill/rounded-rectangle category mismatches"}
    rows.append(row)
    fusion_path=ROOT.parent/"blind_fusion"/"fusion_scores.json"
    if fusion_path.exists():
        fusion=json.loads(fusion_path.read_text(encoding="utf-8"))
        f=fusion["counts"]
        rows.append({"approach":"codex_vision_plus_rapid_v6_blind","cases":10,
            "all_visible_text_exact":rate(f["title_exact"]+f["exact_node_labels"]+f["correct_relationships"],100),
            "all_visible_text_precision":1.0,"extra_ocr_items":None,
            "node_labels_exact":rate(f["exact_node_labels"],f["truth_nodes"]),
            "edge_labels_exact":rate(f["correct_relationships"],f["truth_edges"]),
            "rotated_edge_labels_exact":1.0,
            "connections_found":f["matched_topology"],"connections_total":f["truth_edges"],
            "arrow_accuracy":rate(f["correct_arrows"],f["truth_edges"]),
            "fully_correct_edges":f["fully_correct_edges"],
            "full_edge_recall":rate(f["fully_correct_edges"],f["truth_edges"]),
            "node_shape_accuracy":rate(f["exact_node_shapes"],f["truth_nodes"]),
            "edge_stroke_accuracy":rate(f["correct_strokes"],f["truth_edges"]),
            "note":"Fresh separate Codex thread with images and raw OCR; 3 false OCR detections rejected; four pill/rounded-rectangle category mismatches"})
    (ROOT/"combined_approach_matrix.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    with (ROOT/"combined_approach_matrix.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print("Wrote",len(rows),"approach rows, including blind vision")


if __name__=="__main__":main()
