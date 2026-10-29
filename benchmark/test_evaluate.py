import unittest

from benchmark.evaluate import evaluate


class EvaluateTests(unittest.TestCase):
    def setUp(self):
        self.truth={"title":"Testi","rendered_title":"Testi · synteettinen testikaavio",
                    "nodes":[{"id":"n1","label":"Lähete","type":"rounded_rectangle","bbox":[0,0,100,50]},
                             {"id":"n2","label":"Päätös","type":"rounded_rectangle","bbox":[200,0,300,50]}],
                    "edges":[{"source":"n1","target":"n2","relationship":"lähettää","direction":"source_to_target"}]}

    def test_wrong_text_arrow_and_relationship_are_separate(self):
        pred={"nodes":[{"id":"a","label":"Lahete","type":"rounded_rectangle","bbox":[0,0,100,50]},
                       {"id":"b","label":"Päätös","type":"rounded_rectangle","bbox":[200,0,300,50]}],
              "edges":[{"source":"b","target":"a","relationship":"lähetti","direction":"source_to_target"}],
              "visible_text":["Testi · synteettinen testikaavio","Lahete","Päätös","lähetti"]}
        result=evaluate(pred,self.truth)
        kinds={e["kind"] for e in result["errors"]}
        self.assertTrue({"wrong_node_text","wrong_arrow","wrong_relationship",
                         "missing_visible_text","extra_or_wrong_visible_text"} <= kinds)
        self.assertEqual(result["metrics"]["topology_recall"],1.0)
        self.assertEqual(result["metrics"]["end_to_end_edge_recall"],0.0)

    def test_missing_edge(self):
        pred={"nodes":self.truth["nodes"],"edges":[],"visible_text":[]}
        result=evaluate(pred,self.truth)
        self.assertEqual(result["metrics"]["full_edge_recall"],0.0)
        self.assertTrue(any(e["kind"]=="missing_edge" for e in result["errors"]))


if __name__=="__main__":
    unittest.main()
