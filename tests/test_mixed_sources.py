"""Three-source grouping uses explicit fictional semantic annotations, no account access."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("native_history", ROOT / "skills/maintain-personal-context/scripts/native_history.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
FIXTURE = json.loads((ROOT / "tests/fixtures/mixed-sources.json").read_text())


def reconcile(f):
    return m.reconcile_claims(f["claims"], f["required_keys"])


class MixedSourceTests(unittest.TestCase):
    def test_same_fact_from_three_sources_one_value_all_provenance(self):
        result = reconcile(copy.deepcopy(FIXTURE))
        fact = next(f for f in result["facts"] if f["key"] == "preferred_format")
        self.assertEqual(len(fact["values"]), 1)
        self.assertEqual(len(fact["values"][0]["sources"]), 3)
        self.assertEqual(fact["status"], "known")
        self.assertFalse(fact["independent_evidence_by_source_count"])

    def test_explicit_later_user_correction_wins_stale_memory_and_profile(self):
        fact = next(f for f in reconcile(FIXTURE)["facts"] if f["key"] == "experience_years")
        self.assertEqual(fact["current_value"], "三年")
        old = next(v for v in fact["values"] if v["value"] == "八年")
        self.assertEqual(len(old["sources"]), 3)
        self.assertEqual(old["superseded_by"], "fixture-chat-explicit-correction")
        self.assertIsNone(fact["save_confirmation_date"])

    def test_known_fields_not_reasked_only_missing_or_conflict(self):
        result = reconcile(FIXTURE)
        self.assertEqual(result["question_keys"], ["current_goal"])
        self.assertNotIn("preferred_format", result["question_keys"])
        self.assertNotIn("experience_years", result["question_keys"])

    def test_replay_dedup_and_inputs_unchanged(self):
        f = copy.deepcopy(FIXTURE); expected = reconcile(f); before = copy.deepcopy(f)
        self.assertEqual(reconcile(f), expected)
        self.assertEqual(f, before)
        f["claims"] += copy.deepcopy(f["claims"])
        self.assertEqual(reconcile(f), expected)

    def test_memory_cannot_be_direct_or_assert_correction(self):
        for field, value in (("evidence_tier", "direct"), ("correction_of", "another value")):
            f = copy.deepcopy(FIXTURE); f["claims"][1][field] = value
            with self.assertRaises(m.HistoryError): reconcile(f)

    def test_later_or_undated_contradictory_user_material_stays_conflict(self):
        for date in ("2026-09-30T08:00:00+00:00", None):
            f = copy.deepcopy(FIXTURE); f["claims"][5]["recorded_at"] = date
            result = reconcile(f)
            self.assertIn("experience_years", result["conflict_keys"])
            self.assertIn("experience_years", result["question_keys"])

    def test_assistant_advice_does_not_replace_user_fact(self):
        f = copy.deepcopy(FIXTURE)
        f["claims"].append({"key": "experience_years", "value": "专业水平", "source_kind": "conversation", "source_id": "fixture-assistant-advice", "author_role": "assistant", "evidence_tier": "direct", "recorded_at": "2026-09-30T08:00:00+00:00"})
        fact = next(v for v in reconcile(f)["facts"] if v["key"] == "experience_years")
        self.assertEqual(fact["current_value"], "三年")
        self.assertEqual(fact["status"], "known")

    def test_later_equal_or_undated_unknown_author_material_keeps_conflict(self):
        for date in ("2026-09-30T08:00:00+00:00", "2026-09-10T08:00:00+00:00", None):
            with self.subTest(date=date):
                f = copy.deepcopy(FIXTURE)
                f["claims"][5].update(author_role="unknown", recorded_at=date)
                result = reconcile(f)
                fact = next(v for v in result["facts"] if v["key"] == "experience_years")
                self.assertEqual(fact["status"], "conflict")
                self.assertIsNone(fact["current_value"])
                self.assertIn("experience_years", result["question_keys"])
                old = next(v for v in fact["values"] if v["value"] == "八年")
                self.assertNotIn("superseded_by", old)
                self.assertEqual(old["sources"][-1]["author_role"], "unknown")

    def test_unknown_material_conflict_without_older_user_authority(self):
        f = copy.deepcopy(FIXTURE)
        f["claims"][5].update(author_role="unknown", recorded_at=None)
        f["claims"] = [r for r in f["claims"] if r["source_id"] not in
                       ("fixture-chat-old-experience", "fixture-memory-old-experience")]
        result = reconcile(f)
        self.assertIn("experience_years", result["conflict_keys"])
        fact = next(v for v in result["facts"] if v["key"] == "experience_years")
        self.assertIsNone(fact["current_value"])

    def test_dated_old_unknown_material_allows_exact_explicit_correction(self):
        f = copy.deepcopy(FIXTURE)
        f["claims"][5]["author_role"] = "unknown"
        result = reconcile(f)
        fact = next(v for v in result["facts"] if v["key"] == "experience_years")
        self.assertEqual(fact["status"], "known")
        self.assertEqual(fact["current_value"], "三年")
        old = next(v for v in fact["values"] if v["value"] == "八年")
        self.assertEqual(old["superseded_by"], "fixture-chat-explicit-correction")
        self.assertEqual(old["sources"][-1]["author_role"], "unknown")
        self.assertNotIn("experience_years", result["question_keys"])

    def test_later_unknown_material_other_value_is_unresolved_conflict(self):
        f = copy.deepcopy(FIXTURE)
        f["claims"][5].update(author_role="unknown", value="六年",
                              recorded_at="2026-09-30T08:00:00+00:00")
        result = reconcile(f)
        self.assertIn("experience_years", result["conflict_keys"])
        fact = next(v for v in result["facts"] if v["key"] == "experience_years")
        self.assertIsNone(fact["current_value"])
        candidate = next(v for v in fact["values"] if v["value"] == "六年")
        self.assertEqual(candidate["sources"][0]["author_role"], "unknown")

    def test_old_unknown_material_other_value_never_overrides_newer_user(self):
        f = copy.deepcopy(FIXTURE)
        f["claims"][5].update(author_role="unknown", value="六年")
        result = reconcile(f)
        fact = next(v for v in result["facts"] if v["key"] == "experience_years")
        self.assertEqual(fact["status"], "known")
        self.assertEqual(fact["current_value"], "三年")
        self.assertNotIn("experience_years", result["question_keys"])
        old = next(v for v in fact["values"] if v["value"] == "六年")
        self.assertNotIn("superseded_by", old)

    def test_unknown_author_same_value_preserves_grade_without_reasking(self):
        f = copy.deepcopy(FIXTURE)
        f["claims"][2].update(author_role="unknown", recorded_at=None)
        result = reconcile(f)
        fact = next(v for v in result["facts"] if v["key"] == "preferred_format")
        self.assertEqual(fact["status"], "known")
        self.assertEqual(len(fact["values"]), 1)
        self.assertEqual(fact["values"][0]["sources"][-1]["author_role"], "unknown")
        self.assertNotIn("preferred_format", result["question_keys"])

    def test_unknown_author_material_alone_never_becomes_user_fact(self):
        f = {"required_keys": ["experience_years"], "claims": [copy.deepcopy(FIXTURE["claims"][5])]}
        f["claims"][0]["author_role"] = "unknown"
        result = reconcile(f)
        self.assertEqual(result["facts"][0]["status"], "summary_only")
        self.assertIsNone(result["facts"][0]["current_value"])
        self.assertEqual(result["facts"][0]["summary_candidate"], "八年")

    def test_assistant_suggestion_alone_does_not_answer_a_missing_user_goal(self):
        f = {"required_keys": ["goal"], "claims": [{"key": "goal", "value": "发展事业", "source_kind": "conversation", "source_id": "fixture-assistant-goal", "author_role": "assistant", "evidence_tier": "direct", "recorded_at": None}]}
        result = reconcile(f)
        self.assertEqual(result["facts"][0]["status"], "unconfirmed")
        self.assertIsNone(result["facts"][0]["current_value"])
        self.assertEqual(result["question_keys"], ["goal"])

    def test_summary_only_is_visible_candidate_not_confirmed_personal_fact(self):
        f = {"required_keys": ["summary_slot", "missing_slot"], "claims": [{"key": "summary_slot", "value": "偏好简洁", "source_kind": "memory", "source_id": "fixture-memory-only", "author_role": "unknown", "evidence_tier": "summary", "recorded_at": None}]}
        result = reconcile(f)
        self.assertEqual(result["facts"][0]["status"], "summary_only")
        self.assertIsNone(result["facts"][0]["current_value"])
        self.assertEqual(result["facts"][0]["summary_candidate"], "偏好简洁")
        self.assertEqual(result["question_keys"], ["missing_slot"])

    def test_same_source_identity_with_changed_claim_rejected(self):
        f = copy.deepcopy(FIXTURE); row = copy.deepcopy(f["claims"][0]); row["value"] = "changed"
        f["claims"].append(row)
        with self.assertRaises(m.HistoryError): reconcile(f)


if __name__ == "__main__":
    unittest.main()
