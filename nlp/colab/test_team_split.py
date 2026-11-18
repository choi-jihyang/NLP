"""Verify split/merge coverage, provenance guards, overlaps and missing rows."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from journal import record_key, stable_hash
from team_split import assert_compatible, merge_records


class TeamMergeTests(unittest.TestCase):
    def setUp(self):
        self.inputs = [
            {"dataset": "test", "source_id": str(i), "source_sha256": "source", "input_sha256": f"input{i}"}
            for i in range(6)
        ]
        common = {
            "source_hashes": {"test": "source"},
            "model": {"revision": "pinned"},
            "prompt_version": "v1",
            "prompt_sha256": "prompt",
            "max_input_tokens": 6000,
            "max_new_tokens": 768,
            "batch_size": 8,
            "do_sample": False,
            "enable_thinking": False,
        }
        self.owner = {**common, "bundle_inputs_sha256": "full", "bundle_manifest_sha256": "owner"}
        self.team = {**common, "bundle_inputs_sha256": "tail", "bundle_manifest_sha256": "team"}
        self.assignment = {
            "parent_inputs_sha256": "full",
            "team_inputs_sha256": "tail",
            "total": 6,
            "owner_count": 4,
            "team_keys": ["test:4", "test:5"],
        }
        self.owner_rows = self.records(self.inputs[:4], self.owner)
        self.team_rows = self.records(self.inputs[4:], self.team)

    def records(self, sources, config):
        return [{**source, "status": "ok", "run_signature": stable_hash(config)} for source in sources]

    def merge(self):
        return merge_records(iter(self.inputs), self.owner_rows, self.team_rows, self.owner, self.team, self.assignment)

    def test_disjoint_work_has_exact_coverage_in_source_order(self):
        merged, report = self.merge()
        self.assertEqual([record_key(r) for r in merged], [record_key(s) for s in self.inputs])
        self.assertTrue(report["all_rows_semantically_processed"])

    def test_missing_and_error_are_not_reported_as_complete(self):
        self.team_rows.pop()
        self.team_rows[0]["status"] = "invalid_output"
        _, report = self.merge()
        self.assertEqual(report["missing_ids"], ["test:5"])
        self.assertFalse(report["all_rows_semantically_processed"])

    def test_overlap_keeps_owner_record_and_reports_it(self):
        self.owner_rows += self.records(self.inputs[4:5], self.owner)
        merged, report = self.merge()
        self.assertEqual(report["overlap_kept_owner"], ["test:4"])
        self.assertEqual(merged[4]["run_signature"], stable_hash(self.owner))

    def test_changed_revision_is_rejected(self):
        self.team["model"] = {"revision": "different"}
        with self.assertRaisesRegex(ValueError, "model"):
            self.merge()

    def test_tampered_input_provenance_is_rejected(self):
        self.team_rows[0]["input_sha256"] = "tampered"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.merge()

    def test_duplicate_result_is_rejected(self):
        self.team_rows.append(self.team_rows[0])
        with self.assertRaisesRegex(ValueError, "Duplicate ID"):
            self.merge()

    def test_non_tail_team_record_is_rejected(self):
        self.team_rows = self.records(self.inputs[:1], self.team)
        with self.assertRaisesRegex(ValueError, "Unexpected result"):
            self.merge()

    def long_profile(self):
        self.owner["model"] = {
            "revision": "pinned",
            "engine_settings": {"max_model_len": 7168, "max_num_seqs": 8, "seed": 0},
        }
        self.team["model"] = {
            "revision": "pinned",
            "engine_settings": {"max_model_len": 32768, "max_num_seqs": 1, "seed": 0},
        }
        self.team.update(inference_profile="team_long32k_v1", max_input_tokens=32000, batch_size=1)

    def test_explicit_long_profile_is_accepted_and_reported(self):
        self.long_profile()
        self.owner_rows = self.records(self.inputs[:4], self.owner)
        self.team_rows = self.records(self.inputs[4:], self.team)
        _, report = self.merge()
        self.assertEqual(report["team_profile"], "team_long32k_v1")
        self.assertEqual(report["team_input_limit"], 32000)

    def test_long_profile_still_rejects_changed_model_or_prompt(self):
        self.long_profile()
        self.team["model"]["revision"] = "different"
        with self.assertRaisesRegex(ValueError, "model/engine"):
            assert_compatible(self.owner, self.team)
        self.team["model"]["revision"] = "pinned"
        self.team["prompt_sha256"] = "changed"
        with self.assertRaisesRegex(ValueError, "prompt_sha256"):
            assert_compatible(self.owner, self.team)


if __name__ == "__main__":
    unittest.main()
