import unittest

from gapfinder.data import generate, load_scenario
from gapfinder.discover import discover, proposed_kb
from gapfinder.gate import gate, review


class GapFinderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = load_scenario()
        cls.d = generate(cls.s)
        cls.found = discover(cls.d["history"], cls.d["kb"])
        cls.after = proposed_kb(cls.d["kb"], cls.found)

    def test_generation_is_repeatable(self):
        self.assertEqual(generate(self.s)["pilot"], self.d["pilot"])

    def test_finds_every_missing_step_and_nothing_else(self):
        for t in self.s["topics"]:
            expected = set(t["true_steps"]) - set(t["article_steps"] or [])
            got = {m["step"] for m in self.found[t["id"]]["missing"]}
            self.assertEqual(got, expected, t["id"])

    def test_flags_the_outdated_step(self):
        self.assertEqual([o["step"] for o in self.found["vpn"]["outdated"]], ["old_vpn_client"])
        for t in self.s["topics"]:
            if t["id"] != "vpn":
                self.assertEqual(self.found[t["id"]]["outdated"], [], t["id"])

    def test_one_off_steps_stay_out_of_the_article(self):
        for t in self.s["topics"]:
            for v in t["variant_steps"]:
                if v not in t["true_steps"]:
                    self.assertNotIn(v, self.after[t["id"]] or [], t["id"])

    def test_approved_updates_make_every_article_accurate(self):
        for t in self.s["topics"]:
            self.assertEqual(set(self.after[t["id"]]), set(t["true_steps"]), t["id"])

    def test_provider_gaps_are_found_mostly_in_provider_notes(self):
        for t in self.s["topics"]:
            if t.get("missing_from") == "provider":
                for m in self.found[t["id"]]["missing"]:
                    self.assertEqual(m["lives_in"], "provider notes", t["id"])
            elif t.get("missing_from") == "internal":
                for m in self.found[t["id"]]["missing"]:
                    self.assertEqual(m["lives_in"], "all notes", t["id"])

    def test_no_article_means_no_draft(self):
        r = review([{"id": "x", "topic": "printer", "needed_steps": ["power_cycle_printer"]}], {"printer": None})
        self.assertEqual(r[0]["result"], "none")

    def test_gate_needs_48_of_the_last_50(self):
        s = {"topics": [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}, {"id": "c", "name": "C", "excluded": "pos"}],
             "excluded_reasons": {"pos": "Point-of-sale outage"}}

        def drafts(topic, ok):
            return [{"topic": topic, "result": "approved" if i < ok else "edited"} for i in range(50)]

        g = gate(s, drafts("a", 48) + drafts("b", 47) + drafts("c", 50), [{"topic": "a"}])
        v = {t["id"]: t["verdict"] for t in g["topics"]}
        self.assertEqual(v, {"a": "AUTO-RESOLVE", "b": "KEEP DRAFTING", "c": "ALWAYS A PERSON"})

    def test_gate_needs_a_full_window(self):
        s = {"topics": [{"id": "a", "name": "A"}], "excluded_reasons": {}}
        g = gate(s, [{"topic": "a", "result": "approved"}] * 49, [{"topic": "a"}])
        self.assertEqual(g["topics"][0]["verdict"], "KEEP DRAFTING")


if __name__ == "__main__":
    unittest.main()
