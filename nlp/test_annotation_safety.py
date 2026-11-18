"""약한 주석에서의 AI 근거 혼입·지시 부정·문항 경계 회귀 검사."""

import unittest

from annotation_rules import annotate


class AnnotationSafetyTests(unittest.TestCase):
    def test_assistant_error_is_not_student_attempt(self):
        result = annotate(
            "Explain this code",
            [
                {"role": "assistant", "content": "ValueError: bad shape"},
            ],
        )
        self.assertIs(result["labels"]["has_self_attempt_evidence"], False)

    def test_repeated_assistant_error_is_not_new_attempt(self):
        result = annotate(
            "ValueError: bad shape",
            [
                {"role": "assistant", "content": "An example is ValueError: bad shape"},
            ],
        )
        self.assertIsNone(result["labels"]["has_self_attempt_evidence"])
        self.assertEqual(result["evidence"], [])

    def test_answer_prohibition_is_not_positive_request(self):
        result = annotate("Do not give me the answer. Explain the concept.", [])
        self.assertIsNot(result["labels"]["requests_complete_answer"], True)

    def test_generic_example_is_not_forced_positive(self):
        result = annotate("Give me an example paragraph", [])
        self.assertIsNot(result["labels"]["requests_complete_answer"], True)

    def test_past_work_is_not_carried_across_unknown_question(self):
        result = annotate("What next?", [{"role": "student", "content": "x = 2"}])
        self.assertIsNone(result["labels"]["has_self_attempt_evidence"])

    def test_student_error_span_matches_original(self):
        text = "  I get ValueError: shape mismatch"
        result = annotate(text, [])
        self.assertIs(result["labels"]["has_self_attempt_evidence"], True)
        for span in result["evidence"]:
            self.assertEqual(text[span["start"] : span["end"]], span["text"])


if __name__ == "__main__":
    unittest.main()
