import copy
import unittest
from .fixtures import SOURCES,finding,report
from .synthesis import synthesize

OLD="POL-RETURN-2026-06";NEW="POL-RETURN-2026-09";FAQ="FAQ-RETURNS-2026-09";SHIP="POL-SHIP-2026-06"


class ResearchChecks(unittest.TestCase):
    def run_case(self,reports,topics=("returns",),as_of="2026-09-15",sources=None):
        return synthesize(list(topics),as_of,reports,sources or SOURCES)

    def test_current_disagreement_preserves_both_attributed_values(self):
        value=self.run_case({"returns":report("returns",[NEW,FAQ])})["topics"]["returns"]
        self.assertEqual(value["coverage"],"contested")
        self.assertEqual({c["value"] for c in value["claims"]},{30,45})
        self.assertEqual({c["source_id"] for c in value["claims"]},{NEW,FAQ})
        self.assertTrue(all(c["effective_on"]=="2026-09-01" for c in value["claims"]))
        self.assertEqual(value["conflicts"],["return_window_days"])

    def test_superseded_source_is_history_not_current_conflict(self):
        sources=[s for s in SOURCES if s["id"]!=FAQ]
        value=self.run_case({"returns":report("returns",[OLD,NEW])},sources=sources)["topics"]["returns"]
        self.assertEqual(value["coverage"],"supported")
        self.assertEqual([c["source_id"] for c in value["claims"]],[NEW])
        self.assertEqual([c["source_id"] for c in value["historical"]],[OLD])
        self.assertEqual(value["conflicts"],[])

    def test_future_sources_do_not_change_past_policy(self):
        value=self.run_case({"returns":report("returns",[OLD,NEW,FAQ])},as_of="2026-08-15")["topics"]["returns"]
        self.assertEqual(value["coverage"],"supported")
        self.assertEqual([c["value"] for c in value["claims"]],[30])
        self.assertEqual(len(value["out_of_scope"]),2)

    def test_missing_current_source_creates_targeted_follow_up(self):
        value=self.run_case({"returns":report("returns",[NEW])})["topics"]["returns"]
        self.assertEqual(value["coverage"],"gap")
        self.assertEqual(value["missing_sources"],[FAQ])
        self.assertEqual(len(value["claims"]),1)

    def test_valid_empty_differs_from_access_failure(self):
        empty=self.run_case({"returns":report("returns",status="empty")})["topics"]["returns"]
        failed=self.run_case({"returns":report("returns",status="error")})["topics"]["returns"]
        self.assertEqual(empty["coverage"],"empty")
        self.assertIsNone(empty["error"])
        self.assertEqual(failed["coverage"],"unavailable")
        self.assertEqual(failed["error"]["type"],"timeout")
        self.assertTrue(failed["attempts"])

    def test_partial_error_preserves_findings_and_healthy_sibling(self):
        result=self.run_case({"returns":report("returns",[NEW],"error"),"shipping":report("shipping",[SHIP])},topics=("returns","shipping"))
        self.assertEqual(result["topics"]["returns"]["coverage"],"partial_failure")
        self.assertEqual(len(result["topics"]["returns"]["claims"]),1)
        self.assertEqual(result["topics"]["shipping"]["coverage"],"supported")
        self.assertFalse(result["ready"])

    def test_forged_quote_or_cross_topic_result_is_not_accepted(self):
        for changed in [dict(quote="shortened evidence"),dict(value=True),dict(source_id=SHIP)]:
            item=report("returns",[NEW]);item["findings"][0].update(changed)
            value=self.run_case({"returns":item})["topics"]["returns"]
            self.assertEqual(value["coverage"],"invalid_evidence")
            self.assertEqual(value["claims"],[])

    def test_invalid_sibling_does_not_destroy_valid_work(self):
        result=self.run_case({"returns":{"status":"ok"},"shipping":report("shipping",[SHIP])},topics=("returns","shipping"))
        self.assertEqual(result["topics"]["returns"]["coverage"],"invalid_evidence")
        self.assertEqual(result["topics"]["shipping"]["coverage"],"supported")

    def test_empty_cannot_carry_findings_or_hide_failure(self):
        for item in [report("returns",[NEW],"empty"),{**report("returns",status="error"),"status":"empty"}]:
            self.assertEqual(self.run_case({"returns":item})["topics"]["returns"]["coverage"],"invalid_evidence")

    def test_input_reports_and_catalog_are_not_mutated(self):
        item={"returns":report("returns",[OLD,NEW,FAQ])};original=copy.deepcopy(item);catalog=copy.deepcopy(SOURCES)
        result=self.run_case(item);result["topics"]["returns"]["claims"][0]["value"]=999
        self.assertEqual(item,original);self.assertEqual(SOURCES,catalog)
