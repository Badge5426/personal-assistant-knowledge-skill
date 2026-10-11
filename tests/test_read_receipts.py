"""Fictional receipt regressions, including an incorrectly inherited route failure."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/maintain-personal-context/scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("receipt_result", SCRIPTS / "first_run.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
FIXTURE = json.loads((ROOT / "tests/fixtures/first-run.json").read_text())["master_profile"]


def data_with_check(**changes):
    data = copy.deepcopy(FIXTURE)
    check = {"source_kind": "chatgpt_conversation", "reader_kind": "chatgpt_conversation",
             "scope_kind": "selected_messages", "requested_message_ids": ["fictional-life-message"],
             "returned_message_ids": ["fictional-life-message"], "content_omitted": False,
             "truncated": False, "next_cursor": None}
    check.update(changes)
    data["source_review"][0]["read_check"] = check
    return data


class ReadReceiptTests(unittest.TestCase):
    def test_unreported_aggregate_flags_leave_returned_target_unknown(self):
        for aggregate in [{}, {"content_omitted": False}, {"truncated": False}]:
            for messages in [[], [{"id": "fictional-life-message"}]]:
                with self.subTest(aggregate=aggregate, messages=messages):
                    data = data_with_check(returned_messages=messages)
                    check = data["source_review"][0]["read_check"]
                    for flag in ("content_omitted", "truncated"):
                        check.pop(flag, None)
                    check.update(aggregate)
                    result = m.build_result(data)
                    item = result["source_review"]["items"][0]
                    self.assertEqual(item["read_check"]["target_completeness"]["fictional-life-message"], "unknown")
                    self.assertEqual(item["status"], "partial")
                    self.assertFalse(result["source_review"]["complete_in_checked_scope"])
                    self.assertIsNotNone(result["identity"][0]["fact"])

    def test_missing_target_flag_needs_explicit_aggregate_evidence(self):
        for missing in ("content_omitted", "truncated"):
            with self.subTest(missing=missing):
                other = "truncated" if missing == "content_omitted" else "content_omitted"
                data = data_with_check(returned_messages=[{"id": "fictional-life-message", other: False}])
                check = data["source_review"][0]["read_check"]
                check.pop(missing, None)
                check[other] = False
                item = m.build_result(data)["source_review"]["items"][0]
                self.assertEqual(item["read_check"]["target_completeness"]["fictional-life-message"], "unknown")
                self.assertEqual(item["status"], "partial")

    def test_explicit_target_false_flags_complete_without_aggregate_flags(self):
        for aggregate in [{}, {"content_omitted": True, "truncated": True}]:
            with self.subTest(aggregate=aggregate):
                data = data_with_check(returned_messages=[{"id": "fictional-life-message",
                    "content_omitted": False, "truncated": False}])
                check = data["source_review"][0]["read_check"]
                for flag in ("content_omitted", "truncated"):
                    check.pop(flag, None)
                check.update(aggregate)
                result = m.build_result(data)
                item = result["source_review"]["items"][0]
                self.assertEqual(item["read_check"]["target_completeness"]["fictional-life-message"], "complete")
                self.assertEqual(item["status"], "read")
                self.assertTrue(result["source_review"]["complete_in_checked_scope"])
                self.assertTrue(any("不证明整段" in g for g in result["coverage_gaps"]))

    def test_explicit_target_true_flags_remain_incomplete_without_aggregate_flags(self):
        for flag in ("content_omitted", "truncated"):
            with self.subTest(flag=flag):
                data = data_with_check(returned_messages=[{"id": "fictional-life-message", flag: True}])
                check = data["source_review"][0]["read_check"]
                for name in ("content_omitted", "truncated"):
                    check.pop(name, None)
                item = m.build_result(data)["source_review"]["items"][0]
                self.assertEqual(item["read_check"]["target_completeness"]["fictional-life-message"], "incomplete")
                self.assertEqual(item["status"], "partial")

    def test_explicit_aggregate_false_can_cover_unreported_target_flags(self):
        for messages in [[], [{"id": "fictional-life-message"}],
                         [{"id": "fictional-life-message", "content_omitted": False}]]:
            with self.subTest(messages=messages):
                result = m.build_result(data_with_check(content_omitted=False, truncated=False,
                    returned_messages=messages))
                item = result["source_review"]["items"][0]
                self.assertEqual(item["read_check"]["target_completeness"]["fictional-life-message"], "complete")
                self.assertEqual(item["status"], "read")

    def test_target_own_omission_cannot_be_hidden_by_its_returned_id(self):
        data = data_with_check(content_omitted=True, returned_messages=[
            {"id": "fictional-life-message", "content_omitted": True}])
        result = m.build_result(data)
        self.assertEqual(result["source_review"]["items"][0]["status"], "partial")
        self.assertFalse(result["source_review"]["complete_in_checked_scope"])
        self.assertIsNotNone(result["identity"][0]["fact"])

    def test_source_previous_cursor_and_truncation_keep_incomplete_scope(self):
        for receipt in [{"previous_cursor": "fictional-older"}, {"truncated": True}]:
            with self.subTest(receipt=receipt):
                result = m.build_result(data_with_check(scope_kind="source", **receipt))
                self.assertEqual(result["source_review"]["items"][0]["status"], "partial")
                self.assertEqual(result["source_review"]["continuation_roles"], ["personal_profile"])

    def test_parent_own_gap_survives_its_only_refused_child(self):
        for status in ["stale", "partial", "failed", "discovered_unread"]:
            with self.subTest(status=status):
                data = copy.deepcopy(FIXTURE)
                data["source_review"][0].update(status=status, reason="parent itself still needs review",
                    discovered_sources=[{"source_id": "fictional-refused-child", "status": "permission_denied",
                                         "reason": "current child refusal"}])
                result = m.build_result(data)
                self.assertEqual(result["source_review"]["continuation_roles"], ["personal_profile"])
                self.assertEqual(result["source_review"]["blocked_roles"], [])

    def test_wrong_native_route_does_not_prove_chatgpt_unavailable(self):
        data = data_with_check(reader_kind="codex_thread")
        data["source_review"][0].update(status="entry_unavailable", reason="old native route failed")
        result = m.build_result(data)
        self.assertEqual(result["source_review"]["continuation_roles"], ["personal_profile"])
        self.assertEqual(result["source_review"]["blocked_roles"], [])
        self.assertEqual(result["actions"][0]["kind"], "source_review_action")

    def test_read_flag_cannot_hide_missing_exact_target(self):
        result = m.build_result(data_with_check(returned_message_ids=["fictional-unrelated-recent-message"]))
        self.assertFalse(result["source_review"]["complete_in_checked_scope"])
        self.assertEqual(result["source_review"]["items"][0]["status"], "partial")
        self.assertTrue(any("fictional-life-message" in g for g in result["coverage_gaps"]))

    def test_selected_target_is_complete_without_claiming_whole_conversation(self):
        result = m.build_result(data_with_check(content_omitted=True, next_cursor="fictional-next",
            returned_message_ids=["fictional-life-message", "fictional-other-message"], returned_messages=[
                {"id": "fictional-life-message", "content_omitted": False},
                {"id": "fictional-other-message", "content_omitted": True}]))
        self.assertTrue(result["source_review"]["complete_in_checked_scope"])
        self.assertTrue(any("content_omitted=true" in g for g in result["coverage_gaps"]))
        self.assertTrue(any("不证明整段" in g for g in result["coverage_gaps"]))
        self.assertEqual(len(result["actions"]), 3)

    def test_response_omission_without_target_completeness_stays_unknown(self):
        result = m.build_result(data_with_check(content_omitted=True))
        item = result["source_review"]["items"][0]
        self.assertEqual(item["status"], "partial")
        self.assertEqual(item["read_check"]["target_completeness"]["fictional-life-message"], "unknown")

    def test_confirmed_no_continuation_retains_facts_and_stops_source_retry(self):
        data = data_with_check(content_omitted=True, continuation_available=False, returned_messages=[
            {"id": "fictional-life-message", "content_omitted": True}])
        before = copy.deepcopy(data)
        result = m.build_result(data)
        self.assertEqual(result["source_review"]["items"][0]["status"], "partial")
        self.assertEqual(result["source_review"]["blocked_roles"], ["personal_profile"])
        self.assertEqual(result["source_review"]["continuation_roles"], [])
        self.assertTrue(all(a["kind"] == "recommendation" for a in result["actions"]))
        self.assertIsNotNone(result["identity"][0]["fact"])
        self.assertTrue(any("停止此源续读" in g for g in result["coverage_gaps"]))
        self.assertEqual(m.build_result(data), result)
        self.assertEqual(data, before)

    def test_target_truncation_is_distinct_from_other_message_truncation(self):
        for truncated, expected in [(True, "partial"), (False, "read")]:
            with self.subTest(truncated=truncated):
                result = m.build_result(data_with_check(truncated=True, previous_cursor="fictional-older",
                    returned_messages=[{"id": "fictional-life-message", "truncated": truncated}]))
                self.assertEqual(result["source_review"]["items"][0]["status"], expected)
                self.assertTrue(any("previous_cursor" in g for g in result["coverage_gaps"]))

    def test_invalid_new_receipt_flags_do_not_silently_claim_completeness(self):
        for change in [{"truncated": "true"}, {"truncated": None}, {"content_omitted": None},
                       {"previous_cursor": ""}, {"continuation_available": "false"},
                       {"returned_messages": [{"id": "fictional-life-message", "content_omitted": "true"}]},
                       {"returned_messages": [{"id": "fictional-life-message", "truncated": None}]},
                       {"returned_messages": [{"id": "fictional-life-message", "content_omitted": None}]},
                       {"returned_messages": [{"id": "fictional-not-returned", "content_omitted": False}]}]:
            with self.subTest(change=change), self.assertRaises(m.ResultError):
                m.build_result(data_with_check(**change))

    def test_whole_source_omission_or_pagination_keeps_continuation(self):
        for changes in [{"content_omitted": True}, {"next_cursor": "fictional-next"}]:
            result = m.build_result(data_with_check(scope_kind="source", **changes))
            self.assertEqual(result["source_review"]["continuation_roles"], ["personal_profile"])

    def test_observed_version_change_refreshes_before_personal_questions(self):
        result = m.build_result(data_with_check(read_version=4, latest_version=6))
        self.assertEqual(result["source_review"]["items"][0]["status"], "stale")
        self.assertEqual([a["kind"] for a in result["actions"]], ["source_review_action"])
        self.assertIsNotNone(result["identity"][0]["fact"])

    def test_old_missing_entry_is_rechecked_but_current_refusal_is_preserved(self):
        data = data_with_check(status_origin="inherited")
        data["source_review"][0].update(status="entry_missing", reason="previous environment")
        self.assertEqual(m.build_result(data)["source_review"]["continuation_roles"], ["personal_profile"])
        data["source_review"][0].update(status="permission_denied", reason="explicit source refusal")
        data["source_review"][0]["read_check"]["reader_kind"] = "codex_thread"
        self.assertEqual(m.build_result(data)["source_review"]["blocked_roles"], ["personal_profile"])

    def test_parent_blocked_entry_does_not_hide_a_distinct_readable_child(self):
        data = copy.deepcopy(FIXTURE)
        data["source_review"][2].update(status="entry_unavailable", reason="one old entry unavailable",
            discovered_sources=[{"source_id": "fictional-independent-project-doc", "status": "discovered_unread",
                                 "reason": "readable authorized second source"}])
        result = m.build_result(data)
        self.assertEqual(result["source_review"]["continuation_roles"], ["materials_index"])
        self.assertEqual(result["source_review"]["blocked_roles"], [])

    def test_nested_read_receipt_also_preserves_pending_target(self):
        data = data_with_check()
        row = data["source_review"][0]
        row["discovered_sources"] = [{"source_id": row["source_ids"][0], "status": "read",
            "read_check": dict(row["read_check"], returned_message_ids=[])}]
        self.assertEqual(m.build_result(data)["source_review"]["items"][0]["status"], "partial")

    def test_invalid_receipt_is_rejected_and_input_is_not_mutated(self):
        data = data_with_check(); before = copy.deepcopy(data)
        self.assertEqual(m.build_result(data), m.build_result(data))
        self.assertEqual(data, before)
        for change in [{"content_omitted": "true"}, {"requested_message_ids": []},
                       {"read_version": 4}, {"reader_kind": "invented_tool"},
                       {"status_origin": "assumed"}]:
            with self.subTest(change=change), self.assertRaises(m.ResultError):
                m.build_result(data_with_check(**change))


if __name__ == "__main__":
    unittest.main()
