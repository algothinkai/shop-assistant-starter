"""Recovery evidence, interruption, drift and bounded next-phase context."""
import copy,json,tempfile,unittest
from pathlib import Path
from .artifacts import TASKS,scan,export
from .workflow import manifest,recover,next_prompt


class ExplorationChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"source";self.out=Path(self.tmp.name)/"exports"
        for file in TASKS.values():
            path=self.root/file;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text("def refund_example():\n    return None\n")
        self.entries={t:export(self.out,scan(self.root,t)) for t in TASKS}

    def test_fresh_exports_resume_with_citations(self):
        state=recover(self.root,self.out,manifest(self.entries))
        self.assertEqual(state["status"],"ready")
        self.assertEqual(set(state["fresh"]),set(TASKS));self.assertEqual(state["rerun"],[])
        prompt=next_prompt(state,"Where should I investigate next?")
        self.assertTrue(prompt.startswith("VERIFIED SOURCE SNAPSHOTS"))
        self.assertIn("shop_assistant/business.py:1",prompt)
        self.assertIn("refund_example",prompt)
        self.assertIn("not prove runtime",prompt)

    def test_missing_export_is_explicit_and_not_empty_success(self):
        state=recover(self.root,self.out,manifest({"refund-code":self.entries["refund-code"]}))
        self.assertEqual(state["status"],"partial")
        self.assertEqual(state["rerun"],["refund-tests"])
        self.assertIn("refund-tests",next_prompt(state,"Continue"))

    def test_source_change_only_invalidates_dependent_task(self):
        (self.root/TASKS["refund-code"]).write_text("def changed(): pass\n")
        state=recover(self.root,self.out,manifest(self.entries))
        self.assertEqual(set(state["fresh"]),{"refund-tests"})
        self.assertEqual(state["rerun"],["refund-code"])
        self.assertNotIn("shop_assistant/business.py:1",next_prompt(state,"Continue"))

    def test_corrupt_or_deleted_export_does_not_erase_other_task(self):
        path=self.out/self.entries["refund-code"]["file"]
        for change in [lambda:path.write_text("{broken"),lambda:path.unlink()]:
            change();state=recover(self.root,self.out,manifest(self.entries))
            self.assertEqual(set(state["fresh"]),{"refund-tests"})
            self.assertEqual(state["rerun"],["refund-code"])

    def test_export_path_escape_or_extra_task_rejected(self):
        bad=copy.deepcopy(self.entries);bad["refund-code"]["file"]="../private.json"
        with self.assertRaises(ValueError):manifest(bad)
        with self.assertRaises(ValueError):manifest({"unknown":self.entries["refund-code"]})

    def test_wrong_export_identity_requires_rerun(self):
        value=scan(self.root,"refund-code");value["task"]="refund-tests"
        entry=export(self.out,value)
        index=manifest({"refund-tests":entry})
        state=recover(self.root,self.out,index)
        self.assertEqual(state["fresh"],{})
        self.assertEqual(set(state["rerun"]),set(TASKS))

    def test_empty_discovery_is_not_complete_analysis(self):
        (self.root/TASKS["refund-code"]).write_text("pass\n")
        entry=export(self.out,scan(self.root,"refund-code"))
        index=manifest({**self.entries,"refund-code":entry})
        state=recover(self.root,self.out,index)
        self.assertEqual(state["rerun"],["refund-code"])

    def test_quote_must_match_the_named_current_source_line(self):
        value=scan(self.root,"refund-code");value["findings"][0]["quote"]="invented evidence"
        entry=export(self.out,value);state=recover(self.root,self.out,manifest({**self.entries,"refund-code":entry}))
        self.assertEqual(state["rerun"],["refund-code"])

    def test_partial_manifest_survives_json_roundtrip(self):
        original=manifest({"refund-code":self.entries["refund-code"]})
        reloaded=json.loads(json.dumps(original))
        self.assertEqual(recover(self.root,self.out,original),recover(self.root,self.out,reloaded))

    def test_invalid_manifest_version_and_prompt_are_rejected(self):
        index=manifest(self.entries);index["version"]=2
        with self.assertRaises(ValueError):recover(self.root,self.out,index)
        with self.assertRaises(ValueError):next_prompt({},"Continue")

    def test_definition_looking_text_inside_string_is_not_code_evidence(self):
        path=self.root/TASKS["refund-code"]
        path.write_text("DOC = "+repr("\ndef refund_fake():\n")+"\n")
        # A real multiline string contains a definition-looking line but no AST function.
        path.write_text("DOC = "+chr(39)*3+"\ndef refund_fake():\n"+chr(39)*3+"\n")
        value=scan(self.root,"refund-code")
        value["findings"]=[{"symbol":"refund_fake","line":2,"quote":"def refund_fake():"}]
        entry=export(self.out,value)
        state=recover(self.root,self.out,manifest({**self.entries,"refund-code":entry}))
        self.assertEqual(state["rerun"],["refund-code"])
