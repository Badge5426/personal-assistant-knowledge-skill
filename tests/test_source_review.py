"""Personal source selection/readiness regressions; fictional adults, no tools."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/maintain-personal-context/scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("source_review_result", SCRIPTS / "first_run.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
FIXTURE = json.loads((ROOT / "tests/fixtures/first-run.json").read_text())


class SourceReviewTests(unittest.TestCase):
    def test_missing_review_cannot_treat_empty_claims_as_an_empty_person(self):
        data = copy.deepcopy(FIXTURE["zero"]); del data["source_review"]
        with self.assertRaises(m.ResultError): m.build_result(data)

    def test_three_successful_channels_do_not_replace_an_unread_master_profile(self):
        data = copy.deepcopy(FIXTURE["zero"])
        data["source_review"][0] = {"role": "personal_profile", "status": "discovered_unread",
            "scope": "selected fictional existing profile", "reason": "identified but not read"}
        for item in data["source_review"][1:]:
            item.update(status="read", source_ids=["fictional-read-" + item["role"]])
        result = m.build_result(data)
        self.assertFalse(result["source_review"]["complete_in_checked_scope"])
        self.assertEqual([a["kind"] for a in result["actions"]], ["source_review_action"])
        self.assertTrue(all(r["state"] == "source_review_pending" for r in result["identity"]))
        text = m.render_result(result)
        self.assertIn("有源未读", text)
        self.assertNotIn("提供一个有代表性的经历", text)
        self.assertNotIn("当前最想解决的问题未知", text)

    def test_partial_stale_and_failed_sources_defer_generic_questions(self):
        for status in ["partial", "stale", "failed"]:
            data = copy.deepcopy(FIXTURE["master_profile"])
            data["source_review"][2].update(status=status, reason="actual selected-source gap")
            result = m.build_result(data)
            self.assertEqual(len(result["actions"]), 1)
            self.assertEqual(result["actions"][0]["kind"], "source_review_action")
            self.assertTrue(all(r["fact"] is not None for r in result["identity"]))
            self.assertIn("资料与项目索引", result["actions"][0]["first_step"])

    def test_definitely_blocked_sources_keep_known_actions_without_futile_reads_or_questions(self):
        blocked = ["entry_missing", "entry_unavailable", "permission_denied", "nested_permission_denied"]
        for status in blocked:
            with self.subTest(status=status):
                data = copy.deepcopy(FIXTURE["master_profile"])
                memory = data["source_review"][3]
                if status == "nested_permission_denied":
                    memory["discovered_sources"] = [{"source_id": "fictional-blocked-memory",
                        "status": "permission_denied", "reason": "confirmed access refusal"}]
                else:
                    memory.update(status=status, reason="confirmed unavailable in this scope")
                before = copy.deepcopy(data)
                result = m.build_result(data)
                self.assertEqual(len(result["actions"]), len(data["recommendations"]))
                self.assertTrue(all(a["kind"] == "recommendation" for a in result["actions"]))
                self.assertLessEqual(len(result["actions"]), 3)
                self.assertTrue(all(r["fact"] is not None for r in result["identity"]))
                self.assertEqual(result["source_review"]["blocked_roles"], ["related_memory"])
                self.assertEqual(result["source_review"]["continuation_roles"], [])
                self.assertFalse(result["source_review"]["complete_in_checked_scope"])
                self.assertTrue(any("相关定向记忆" in g for g in result["coverage_gaps"]))
                self.assertEqual(m.build_result(data), result)
                self.assertEqual(data, before)
        # A separate readable source still gets a continuation; the rejected one does not.
        data = copy.deepcopy(FIXTURE["master_profile"])
        data["source_review"][2].update(status="discovered_unread", reason="readable source not yet read")
        data["source_review"][3].update(status="permission_denied", reason="confirmed access refusal")
        result = m.build_result(data)
        self.assertEqual([a["kind"] for a in result["actions"]], ["source_review_action"])
        self.assertIn("资料与项目索引", result["actions"][0]["first_step"])
        self.assertNotIn("相关定向记忆", result["actions"][0]["first_step"])
        # With no grounded advice, keep the blocked gap without inventing a personal questionnaire.
        data = copy.deepcopy(FIXTURE["zero"])
        data["source_review"][3].update(status="entry_unavailable", reason="confirmed unavailable")
        result = m.build_result(data)
        self.assertEqual(result["actions"], [])
        self.assertIn("来源受阻", m.render_result(result))

    def test_actual_bounded_absence_allows_three_small_questions_without_claiming_all_history(self):
        result = m.build_result(FIXTURE["zero"])
        self.assertTrue(result["source_review"]["complete_in_checked_scope"])
        self.assertEqual(len(result["actions"]), 3)
        self.assertTrue(all(r["state"] == "unknown_in_checked_scope" for r in result["identity"]))
        self.assertIn("账户总量未知", m.render_result(result))

    def test_rich_master_profile_with_unrelated_engineering_uses_personal_content(self):
        result = m.build_result(FIXTURE["master_profile"])
        facts = {r["key"]: r["fact"] for r in result["identity"]}
        self.assertEqual(facts["name"]["value"], "周岚")
        self.assertIn("青原市", facts["introduction"]["value"])
        self.assertEqual(result["priority"]["fact"]["value"], "为一件已有木柜作品准备第一段演示")
        self.assertIn("两件木柜", facts["skills"]["value"])
        self.assertIn("打印机A已售", facts["resources"]["value"])
        self.assertTrue(all(any(s.startswith("fictional-master-") for s in f["source_ids"]) for f in facts.values()))
        self.assertNotIn("程序测试通过", m.render_result(result))
        self.assertNotIn("五个设计预览", facts["skills"]["value"])

    def test_known_experience_tools_and_main_direction_are_not_asked_again(self):
        result = m.build_result(FIXTURE["master_profile"])
        questions = [a for a in result["actions"] if a["kind"] == "information_action"]
        self.assertEqual([a["key"] for a in questions], ["time_resources"])
        self.assertEqual(len(result["actions"]), 3)
        self.assertIn("只补充", questions[0]["what"])
        self.assertIn("无需重填", questions[0]["how"])

    def test_no_existing_space_or_profile_can_use_reviewed_current_and_history_facts(self):
        data = copy.deepcopy(FIXTURE["master_profile"])
        data["entry"] = {"status": "unavailable", "reason": "fictional client has no Space output tool"}
        data["source_review"] = copy.deepcopy(FIXTURE["zero"]["source_review"])
        data["raw_sources"] = []
        for claim in data["claims"]:
            if claim["author_role"] == "user":
                claim.update(source_kind="conversation", evidence_tier="direct",
                             source_id="fictional-reviewed-current-or-native-" + claim["key"])
        result = m.build_result(data)
        self.assertTrue(result["source_review"]["complete_in_checked_scope"])
        self.assertEqual(result["entry"]["status"], "unavailable")
        self.assertTrue(all(row["state"] == "known" for row in result["identity"]))
        self.assertEqual(result["priority"]["fact"]["value"], "为一件已有木柜作品准备第一段演示")
        self.assertEqual([a["key"] for a in result["actions"] if a["kind"] == "information_action"],
                         ["time_resources"])

    def test_user_specified_master_cannot_be_replaced_by_reading_only_logo(self):
        data = copy.deepcopy(FIXTURE["zero"])
        data["source_review"][0] = {"role": "personal_profile", "status": "read",
            "scope": "user explicitly selected fictional master", "source_ids": ["fictional-logo-thread"],
            "discovered_sources": [
                {"source_id": "fictional-logo-thread", "status": "read"},
                {"source_id": "fictional-user-selected-master", "status": "discovered_unread",
                 "reason": "selected master not yet read"}]}
        result = m.build_result(data)
        self.assertFalse(result["source_review"]["complete_in_checked_scope"])
        self.assertEqual(result["source_review"]["items"][0]["status"], "partial")
        self.assertIn("fictional-user-selected-master", " ".join(result["coverage_gaps"]))
        self.assertEqual([a["kind"] for a in result["actions"]], ["source_review_action"])

    def test_unspecified_location_multiple_projects_and_memory_cannot_stop_at_logo(self):
        data = copy.deepcopy(FIXTURE["master_profile"])
        for role, found in [("materials_index", "fictional-discovered-second-project"),
                            ("related_memory", "fictional-discovered-personal-memory")]:
            item = next(r for r in data["source_review"] if r["role"] == role)
            item.update(scope="authorized cross-project discovery; no user location supplied",
                        discovered_sources=[{"source_id": found, "status": "discovered_unread",
                                             "reason": "discovered relevant source still unread"}])
        result = m.build_result(data)
        self.assertEqual(set(result["source_review"]["pending_roles"]), {"materials_index", "related_memory"})
        self.assertEqual([a["kind"] for a in result["actions"]], ["source_review_action"])
        self.assertEqual(result["identity"][0]["fact"]["value"], "周岚")
        self.assertNotIn("提供一个有代表性的经历", m.render_result(result))
        self.assertEqual(data["source_review"][2]["status"], "read")

    def test_unconfirmed_material_is_not_silently_promoted_to_confirmed_profile(self):
        data = copy.deepcopy(FIXTURE["master_profile"])
        next(c for c in data["claims"] if c["key"] == "name")["author_role"] = "unknown"
        name = next(r for r in m.build_result(data)["identity"] if r["key"] == "name")
        self.assertIsNone(name["fact"])
        self.assertEqual(name["state"], "needs_refresh")

    def test_new_explicit_completion_preserves_old_history_without_reopening_project(self):
        old = {"key": "project_state", "value": "not started", "source_id": "fictional-old-project",
            "source_kind": "conversation", "author_role": "user", "evidence_tier": "direct",
            "recorded_at": "2026-01-10T09:00:00+00:00"}
        newer = dict(old, value="completed and displayed", source_id="fictional-current-project",
                     recorded_at="2026-03-10T09:00:00+00:00", correction_of="not started")
        fact = m.reconcile_claims([newer, old])["facts"][0]
        self.assertEqual(fact["current_value"], "completed and displayed")
        self.assertEqual(next(v for v in fact["values"] if v["value"] == "not started")["superseded_by"],
                         "fictional-current-project")

    def test_latest_user_content_rejection_is_not_overridden_by_old_technical_pass(self):
        old = {"key": "content_acceptance", "value": "technical checks passed", "source_id": "fictional-old-audit",
            "source_kind": "conversation", "author_role": "assistant", "evidence_tier": "direct",
            "recorded_at": "2026-03-10T09:00:00+00:00"}
        new = dict(old, value="personal content rejected", source_id="fictional-user-rejection", author_role="user",
                   recorded_at="2026-03-11T09:00:00+00:00")
        self.assertEqual(m.reconcile_claims([old, new])["facts"][0]["current_value"], "personal content rejected")

    def test_conflict_in_one_field_does_not_erase_other_known_background(self):
        data = copy.deepcopy(FIXTURE["master_profile"])
        resource = copy.deepcopy(next(c for c in data["claims"] if c["key"] == "resources"))
        resource.update(value="contradictory undated source", author_role="unknown", source_id="fictional-conflict", recorded_at=None)
        data["claims"].append(resource)
        data["recommendations"] = data["recommendations"][:1]
        identity = {r["key"]: r for r in m.build_result(data)["identity"]}
        self.assertEqual(identity["resources"]["state"], "needs_refresh")
        self.assertIsNone(identity["resources"]["fact"])
        self.assertEqual(identity["name"]["fact"]["value"], "周岚")

    def test_review_requires_actual_scope_identifiers_and_gap_reason(self):
        for field in ["scope", "source_ids"]:
            data = copy.deepcopy(FIXTURE["master_profile"])
            del data["source_review"][0][field]
            with self.assertRaises(m.ResultError): m.build_result(data)
        data = copy.deepcopy(FIXTURE["zero"]); del data["source_review"][0]["reason"]
        with self.assertRaises(m.ResultError): m.build_result(data)
        data = copy.deepcopy(FIXTURE["zero"]); data["source_review"].append(copy.deepcopy(data["source_review"][0]))
        with self.assertRaises(m.ResultError): m.build_result(data)
        for found in ["not a list", [{"source_id": "fictional-x", "status": "not_found_in_checked_scope"}],
                      [{"source_id": "fictional-x", "status": "read"}],
                      [{"source_id": "fictional-x", "status": "partial"}]]:
            data = copy.deepcopy(FIXTURE["master_profile"])
            data["source_review"][0]["discovered_sources"] = found
            with self.assertRaises(m.ResultError): m.build_result(data)

    def test_review_and_personal_claims_are_not_mutated_and_repeat_is_identical(self):
        data = copy.deepcopy(FIXTURE["master_profile"]); before = copy.deepcopy(data)
        result = m.build_result(data)
        self.assertEqual(m.build_result(data), result)
        self.assertEqual(data, before)


if __name__ == "__main__":
    unittest.main()
