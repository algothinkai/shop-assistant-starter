"""Risk checks for the capstone hand-in boundary."""
import json
from pathlib import Path
from copy import deepcopy
import unittest
import tempfile
from .workflow import CapstoneError, inspect, load_json

ROOT = Path(__file__).parent
CASES = json.loads((ROOT / "cases.json").read_text())


class CapstoneChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.responses = json.loads((ROOT / "response.json").read_text())

    def test_all_six_bound_refs_and_full_author_response_structure(self):
        report = inspect(CASES, self.responses)
        self.assertEqual({x["id"] for x in report["cases"]}, {"C1","C2","C3","C4","C5","C6"})
        self.assertTrue(report["all_required_evidence_cited"])
        self.assertEqual(report["mastery"], "UNVERIFIED")
        refs = {v for c in CASES["cases"] for v in c["objective_refs"]}
        expected = {f"1.{n}" for n in range(1,8)} | {f"2.{n}" for n in range(1,6)} | {f"3.{n}" for n in range(1,7)} | {f"4.{n}" for n in range(1,7)} | {f"5.{n}" for n in range(1,7)}
        self.assertEqual(refs, expected)
        self.assertEqual(len(refs),30)

    def test_wrong_or_missing_case_not_misreported_complete(self):
        for changed in (self.responses[:-1], self.responses+[self.responses[-1]]):
            with self.assertRaises(CapstoneError): inspect(CASES, changed)
        bad = deepcopy(self.responses); bad[0]["id"] = "C2"
        with self.assertRaises(CapstoneError): inspect(CASES,bad)

    def test_missing_evidence_keeps_report_incomplete_and_unverified(self):
        bad = deepcopy(self.responses);bad[0]["evidence"]=["identity"]
        result = inspect(CASES,bad)
        self.assertFalse(result["all_required_evidence_cited"])
        self.assertFalse(result["cases"][0]["demonstrated"])

    def test_invalid_choices_and_short_or_oversized_answers_rejected(self):
        for field,value in (("choice","Z"),("transfer_choice","Z"),("reason","ok"),("prediction","x"*2001)):
            bad=deepcopy(self.responses);bad[0][field]=value
            with self.assertRaises(CapstoneError):inspect(CASES,bad)

    def test_extra_or_unknown_evidence_not_accepted(self):
        for values in (["password"],["policy","policy"]):
            bad=deepcopy(self.responses);bad[0]["evidence"]=values
            with self.assertRaises(CapstoneError):inspect(CASES,bad)

    def test_duplicate_response_keys_and_bad_json_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "response.json"
            for payload in ('[{"id":"C2","id":"C1"}]', '{"outer":{"choice":"B","choice":"A"}}', '{', 'NaN'):
                path.write_text(payload)
                with self.assertRaises(CapstoneError):
                    load_json(path)

    def test_one_case_can_finish_before_later_responses_exist(self):
        first = self.responses[:1]
        report = inspect(CASES, first, case_id="C1")
        self.assertEqual(len(report["cases"]), 1)
        self.assertEqual(report["cases"][0]["id"], "C1")
        self.assertTrue(report["all_required_evidence_cited"])
        self.assertEqual(report["mastery"], "UNVERIFIED")
        with self.assertRaises(CapstoneError):
            inspect(CASES, first, case_id="C2")
        with self.assertRaises(CapstoneError):
            inspect(CASES, first)
