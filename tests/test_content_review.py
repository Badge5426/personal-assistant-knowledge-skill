"""Different fictional adult and unseen details; actual-body coverage invariants."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("content_review_test", ROOT /
    "skills/maintain-personal-context/scripts/content_review.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture():
    # Fictional music teacher, distinct from the existing furniture fixture.
    return {"sections": [
        {"id": "music-tools", "source_id": "fictional-teacher-profile#tools", "status": "read",
         "scope": "selected authorized equipment paragraph", "read_version": 2, "latest_version": 2,
         "atoms": [{"id": "violin", "role": "resources",
                    "required_terms": ["学生小提琴C", "2024年", "已归还", "当前借用待确认"]}]},
        {"id": "collaboration", "source_id": "fictional-teacher-profile#collaboration", "status": "read",
         "scope": "selected authorized relationship paragraph",
         "atoms": [{"id": "lesson", "role": "experience",
                    "required_terms": ["林老师", "合作排练", "未承诺本期参与"]}]},
        {"id": "priority", "source_id": "fictional-teacher-profile#priority", "status": "read",
         "scope": "current explicit choice",
         "atoms": [{"id": "sequence", "role": "goals",
                    "required_terms": ["先完成试听课", "演出后置", "用户已选"]}]}
    ], "projections": [
        {"role": "resources", "page_ref": "fictional-private-resources", "readback": True,
         "source_ids": ["fictional-teacher-profile#tools"], "atom_ids": ["violin"],
         "text": "学生小提琴C在2024年已归还；当前借用待确认。"},
        {"role": "experience", "page_ref": "fictional-private-experience", "readback": True,
         "source_ids": ["fictional-teacher-profile#collaboration"], "atom_ids": ["lesson"],
         "text": "与林老师合作排练，但未承诺本期参与。"},
        {"role": "goals", "page_ref": "fictional-private-goals", "readback": True,
         "source_ids": ["fictional-teacher-profile#priority"], "atom_ids": ["sequence"],
         "text": "用户已选先完成试听课、演出后置。"}
    ]}


class ContentReviewTests(unittest.TestCase):
    def test_good_target_cannot_mask_a_bad_projection_of_the_same_atom(self):
        for key, value in [("readback", False), ("source_ids", []),
                           ("role", "goals"), ("text", "current availability unknown")]:
            with self.subTest(key=key):
                data = fixture()
                bad = copy.deepcopy(data["projections"][0])
                bad.update(page_ref="fictional-bad-secondary-projection")
                bad[key] = value
                data["projections"].append(bad)
                result = m.review_content(data)
                self.assertEqual(result["status"], "gaps_found")
                self.assertEqual(result["issues"][0]["targets"][0]["page_ref"], bad["page_ref"])

    def test_every_bad_target_is_reported_even_with_a_complete_primary(self):
        data = fixture()
        for page in ["fictional-unread-secondary", "fictional-other-unread-secondary"]:
            bad = copy.deepcopy(data["projections"][0]); bad.update(page_ref=page, readback=False)
            data["projections"].append(bad)
        self.assertEqual(len(m.review_content(data)["issues"]), 2)

    def reference_fixture(self):
        data = fixture()
        data["projections"].append({"kind": "reference", "role": "identity", "page_ref": "fictional-profile-index",
            "readback": True, "source_ids": [], "atom_ids": ["violin"],
            "text": "[主资源](fictional-private-resources)", "references": {
                "violin": {"target_ref": "fictional-private-resources", "literal": "[主资源](fictional-private-resources)"}}})
        return data

    def test_explicit_reference_verifies_primary_without_copying_full_facts(self):
        data = self.reference_fixture(); before = copy.deepcopy(data)
        self.assertEqual(m.review_content(data)["status"], "annotations_matched")
        self.assertEqual(data, before)
        data["projections"] = list(reversed(data["projections"]))
        self.assertEqual(m.review_content(data)["status"], "annotations_matched")

    def test_bad_reference_literal_readback_or_target_cannot_hide_behind_primary(self):
        for mutation in [lambda ref: ref.update(readback=False),
                         lambda ref: ref.update(text="reference not actually retained"),
                         lambda ref: ref.update(text="[主资源](fictional-missing-target)", references={
                             "violin": {"target_ref": "fictional-missing-target", "literal": "[主资源](fictional-missing-target)"}})]:
            data = self.reference_fixture(); mutation(data["projections"][-1])
            self.assertEqual(m.review_content(data)["issues"][0]["kind"], "reference_not_verified")

    def test_reference_needs_verified_primary_for_the_same_atom_and_actual_link(self):
        data = self.reference_fixture(); data["projections"][0]["atom_ids"] = []
        self.assertEqual(m.review_content(data)["status"], "gaps_found")
        data = self.reference_fixture()
        data["projections"][-1]["references"]["violin"]["target_ref"] = "fictional-unmatched-destination"
        with self.assertRaises(m.CoverageError): m.review_content(data)

    def test_observed_entities_actions_history_conditions_and_order_are_retained(self):
        result = m.review_content(fixture())
        self.assertEqual(result["status"], "annotations_matched")
        self.assertTrue(result["read_scope_complete"])
        self.assertIn("语义正确", result["limitation"])

    def test_field_exists_but_generic_summary_drops_devices_and_relationships(self):
        data = fixture()
        data["projections"][0]["text"] = "有历史设备，当前可用性未知。"
        data["projections"][1]["text"] = "有历史合作关系，当前意愿未知。"
        result = m.review_content(data)
        self.assertEqual(result["status"], "gaps_found")
        self.assertEqual(len(result["issues"]), 2)
        self.assertIn("学生小提琴C", result["issues"][0]["targets"][0]["missing_terms"])

    def test_unknown_current_availability_does_not_erase_confirmed_history(self):
        data = fixture(); data["projections"][0]["text"] = "学生小提琴C当前借用待确认。"
        self.assertIn("已归还", m.review_content(data)["issues"][0]["targets"][0]["missing_terms"])

    def test_chapter_reverse_coverage_finds_an_entire_omitted_project(self):
        data = fixture(); data["projections"] = data["projections"][:2]
        result = m.review_content(data)
        self.assertEqual(result["issues"][0]["kind"], "atom_unmapped")
        self.assertEqual(result["issues"][0]["section_id"], "priority")

    def test_read_empty_section_needs_mapping_or_explicit_exclusion(self):
        data = fixture(); data["sections"].append({"id": "unseen-work", "source_id": "fictional-profile#work",
            "status": "read", "scope": "additional authorized paragraph"})
        self.assertEqual(m.review_content(data)["issues"][0]["kind"], "section_unmapped")
        data["sections"][-1]["excluded_reason"] = "unrelated old third-party example, outside this profile"
        self.assertEqual(m.review_content(data)["status"], "annotations_matched")

    def test_wrong_source_role_or_unverified_readback_cannot_pass(self):
        for key, value in [("source_ids", []), ("role", "goals"), ("readback", False)]:
            data = fixture(); data["projections"][0][key] = value
            self.assertEqual(m.review_content(data)["status"], "gaps_found")

    def test_source_version_change_requires_targeted_refresh(self):
        data = fixture(); data["sections"][0].update(latest_version=3, reason="source changed after drafting")
        result = m.review_content(data)
        self.assertFalse(result["read_scope_complete"])
        self.assertEqual(result["coverage_limits"][0]["status"], "stale")
        self.assertEqual(result["issues"][0]["kind"], "unread_or_stale_source_projected")

    def test_partial_source_cannot_be_promoted_by_matching_text(self):
        data = fixture(); data["sections"][0].update(status="partial", reason="target text omitted")
        self.assertEqual(m.review_content(data)["issues"][0]["kind"], "unread_or_stale_source_projected")

    def test_duplicate_unknown_atom_and_missing_observed_target_are_rejected(self):
        for mutation in [lambda d: d["sections"].append(copy.deepcopy(d["sections"][0])),
                         lambda d: d["projections"][0].update(atom_ids=["invented"]),
                         lambda d: d["projections"][0].update(page_ref=""),
                         lambda d: d["sections"][0].update(read_version=True)]:
            data = fixture(); mutation(data)
            with self.assertRaises(m.CoverageError): m.review_content(data)

    def test_annotations_and_actual_text_are_not_mutated_or_filled_in(self):
        data = fixture(); before = copy.deepcopy(data)
        self.assertEqual(m.review_content(data), m.review_content(data))
        self.assertEqual(data, before)


if __name__ == "__main__":
    unittest.main()
