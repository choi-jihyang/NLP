import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from contract import PROMPT_VERSION, parse_annotation
from test_colab_workflow import candidate

from integrate_studychat_final import choose_candidate, validate_ok


class FinalIntegrationTests(unittest.TestCase):
    def test_valid_original_is_preserved_and_invalid_claim_is_not_chosen(self):
        original = {"row": {"status": "ok"}, "validation_error": None}
        later = {"row": {"status": "ok"}, "validation_error": None}
        self.assertIs(choose_candidate([original, later])[0], original)
        original["validation_error"] = "wrong quote"
        self.assertIs(choose_candidate([original, later])[0], later)

    def test_stored_label_tampering_is_detected(self):
        source = {"message": "help", "history": []}
        text = json.dumps(candidate())
        row = {**parse_annotation(text, source), "status": "ok", "raw_response": text, "prompt_version": PROMPT_VERSION}
        self.assertIsNone(validate_ok(row, source))
        row["labels"]["is_learning_context"] = False
        self.assertIn("Stored fields differ", validate_ok(row, source))

    def test_no_success_is_invented_for_failed_attempts(self):
        first = {"row": {"status": "context_overflow"}, "validation_error": None}
        last = {"row": {"status": "invalid_output"}, "validation_error": None}
        chosen, valid = choose_candidate([first, last])
        self.assertIs(chosen, last)
        self.assertFalse(valid)


if __name__ == "__main__":
    unittest.main()
