"""Observable zero/sparse/rich first-result behavior; fictional annotations, no API."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/maintain-personal-context/scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("first_run", SCRIPTS / "first_run.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
FIXTURE = json.loads((ROOT / "tests/fixtures/first-run.json").read_text())


class FirstRunTests(unittest.TestCase):
    def test_zero_data_unknown_identity_three_simple_information_actions(self):
        result = m.build_result(FIXTURE["zero"])
        self.assertTrue(all(row["fact"] is None for row in result["identity"]))
        self.assertIsNone(result["priority"]["fact"])
        self.assertEqual([a["key"] for a in result["actions"]],
                         ["current_problem", "representative_experience", "time_resources"])
        for action in result["actions"]:
            self.assertEqual(action["kind"], "information_action")
            for field in ("what", "why", "how", "first_step", "confirmation_condition"):
                self.assertTrue(action[field].strip())
        self.assertNotIn("https://", m.render_result(result))

    def test_sparse_data_uses_known_problem_without_reasking(self):
        result = m.build_result(FIXTURE["sparse"])
        self.assertEqual(result["priority"]["fact"]["value"], FIXTURE["sparse"]["claims"][0]["value"])
        self.assertEqual(len(result["actions"]), 3)
        self.assertEqual(result["actions"][0]["kind"], "recommendation")
        self.assertEqual([a["key"] for a in result["actions"] if a["kind"] == "information_action"],
                         ["representative_experience", "time_resources"])
        self.assertTrue(all(row["fact"] is None for row in result["identity"]))

    def test_rich_data_uses_correction_evidence_three_advice_and_working_entry(self):
        result = m.build_result(FIXTURE["rich"])
        identity = {row["key"]: row["fact"] for row in result["identity"]}
        self.assertEqual(identity["name"]["value"], "林远")
        self.assertEqual(identity["skills"]["value"], "两年展台设计经历")
        self.assertEqual(identity["skills"]["source_ids"], ["fictional-source-12", "fictional-source-31"])
        self.assertTrue(any("已存记忆摘要" in s for s in identity["name"]["source_notes"]))
        self.assertTrue(any("用户原话" in s for s in identity["name"]["source_notes"]))
        self.assertEqual(len(result["actions"]), 3)
        self.assertTrue(all(a["kind"] == "recommendation" for a in result["actions"]))
        for action in result["actions"]:
            self.assertTrue(action["basis"])
            self.assertTrue(action["first_step"])
            self.assertTrue(action["confirmation_condition"])
        rendered = m.render_result(result)
        self.assertIn("<https://example.invalid/fictional-root>", rendered)
        self.assertNotIn("五年", rendered)
        self.assertNotIn("八十件", rendered)

    def test_recommendations_never_mutate_facts_and_replay_is_identical(self):
        data = copy.deepcopy(FIXTURE["rich"]); before = copy.deepcopy(data)
        expected = m.build_result(data)
        self.assertEqual(m.build_result(data), expected)
        self.assertEqual(data, before)
        data["claims"] += copy.deepcopy(data["claims"])
        self.assertEqual(m.build_result(data), expected)
        self.assertFalse(any(a["label"] in f["fact"]["value"] for a in expected["actions"]
                             for f in expected["identity"] if f["fact"]))

    def test_summary_assistant_or_conflict_cannot_ground_priority_or_advice(self):
        for change in (dict(author_role="assistant"),
                       dict(source_kind="memory", author_role="unknown", evidence_tier="summary")):
            data = copy.deepcopy(FIXTURE["sparse"]); data["claims"][0].update(change)
            with self.assertRaises(m.ResultError): m.build_result(data)
            data["recommendations"] = []
            result = m.build_result(data)
            self.assertIsNone(result["priority"]["fact"])
            self.assertEqual(result["actions"][0]["key"], "current_problem")
        data = copy.deepcopy(FIXTURE["sparse"])
        other = copy.deepcopy(data["claims"][0]); other.update(value="另一个问题", source_id="fictional-conflict")
        data["claims"].append(other)
        with self.assertRaises(m.ResultError): m.build_result(data)

    def test_each_advice_needs_known_basis_first_step_and_confirmation(self):
        for field, bad in (("basis_keys", []), ("basis_keys", ["unknown"]),
                           ("first_step", " "), ("confirmation_condition", "")):
            data = copy.deepcopy(FIXTURE["rich"]); data["recommendations"][0][field] = bad
            with self.assertRaises(m.ResultError): m.build_result(data)
        data = copy.deepcopy(FIXTURE["rich"]); data["recommendations"] *= 2
        with self.assertRaises(m.ResultError): m.build_result(data)
        data["recommendations"] = []
        with self.assertRaises(m.ResultError): m.build_result(data)

    def test_information_actions_reserve_space_and_total_never_exceeds_three(self):
        data = copy.deepcopy(FIXTURE["sparse"]); data["recommendations"] *= 3
        actions = m.build_result(data)["actions"]
        self.assertEqual(len(actions), 3)
        self.assertEqual(sum(a["kind"] == "recommendation" for a in actions), 1)
        self.assertEqual(sum(a["kind"] == "information_action" for a in actions), 2)

    def test_unverified_missing_unsafe_entry_does_not_print_a_fake_working_link(self):
        for entry in ({"status": "verified"}, {"status": "verified", "url": "https://user:secret" + "@example.invalid/root"},
                      {"status": "verified", "url": "https://example.invalid/root?" + "sig=secret"},
                      {"status": "pending", "reason": "not read back", "url": "https://example.invalid/root"},
                      {"status": "unavailable"}):
            data = copy.deepcopy(FIXTURE["zero"]); data["entry"] = entry
            with self.assertRaises(m.ResultError): m.build_result(data)

    def test_markup_in_claims_is_literal_not_an_extra_action_or_link(self):
        data = copy.deepcopy(FIXTURE["rich"])
        data["claims"][1]["value"] = "简介\n# injected\n[open](https://example.invalid) <script>"
        rendered = m.render_result(m.build_result(data))
        self.assertNotIn("\n# injected", rendered)
        self.assertNotIn("[open](", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_cli_reads_only_selected_fixture_no_file_changes(self):
        before = {p.relative_to(ROOT): p.read_bytes() for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            selected = Path(tmp) / "selected.json"; selected.write_text(json.dumps(FIXTURE["zero"]))
            completed = subprocess.run([sys.executable, "-B", str(SCRIPTS / "first_run.py"), "--input", str(selected)],
                                       capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, m.render_result(m.build_result(FIXTURE["zero"])))
            self.assertEqual(list(Path(tmp).iterdir()), [selected])
        after = {p.relative_to(ROOT): p.read_bytes() for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
