import unittest

from graph_extract import mermaid, reconcile, score


class GraphExtractTests(unittest.TestCase):
    def test_ocr_vision_disagreement_is_explicit(self):
        ocr = {"image_size": [100, 100], "engine": "test", "observations": [
            {"text": "Alfa", "confidence": 0.95, "bbox": [10, 10, 40, 30]},
            {"text": "relation?", "confidence": 0.9, "bbox": [47, 30, 78, 40]},
        ]}
        vision = {"nodes": [
            {"id": "a", "label": "Alpha", "type": "rectangle", "bbox": [5, 5, 45, 35], "confidence": 0.9},
            {"id": "b", "label": "Beta", "type": "rectangle", "bbox": [80, 5, 99, 35], "confidence": 0.9},
        ], "edges": [
            {"source": "a", "target": "b", "relationship": "relation", "direction": "unknown", "points": [[45, 20], [80, 20]], "confidence": 0.8},
            {"source": "a", "target": "missing", "relationship": "invented", "direction": "source_to_target", "points": [[1, 1], [2, 2]]},
        ]}
        graph = reconcile(ocr, vision)
        self.assertEqual(graph["nodes"][0]["label"], "Alpha")
        self.assertEqual(len(graph["edges"]), 1)
        kinds = {u["kind"] for u in graph["uncertainties"]}
        self.assertIn("node_text_disagreement", kinds)
        self.assertIn("edge_not_visually_established", kinds)
        self.assertIn("direction_unresolved", kinds)
        self.assertIn("---|relation [direction unknown]|", mermaid(graph))

    def test_ground_truth_exact_matching(self):
        graph = {"nodes": [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
                 "edges": [{"source": "a", "target": "b", "relationship": "x", "direction": "source_to_target"}]}
        truth = {"nodes": [{"id": "one", "label": "A"}, {"id": "two", "label": "B"}],
                 "edges": [{"source": "one", "target": "two", "relationship": "x", "direction": "source_to_target"}]}
        result = score(graph, truth)
        self.assertEqual(result["nodes"]["precision"], 1.0)
        self.assertEqual(result["edges"]["recall"], 1.0)


if __name__ == "__main__":
    unittest.main()
