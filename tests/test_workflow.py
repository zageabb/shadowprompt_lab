import json
import unittest

from workflow import WorkflowError, parse_workflow, validate_model_output

PLAN = [
    {"skill": "save_markdown", "instruction": "Summarise", "required": True},
    {"skill": "send_email", "instruction": "Prepare approved email", "required": True},
]
GOOD = {
    "answer": "Summary for the user",
    "steps": [
        {"skill": "save_markdown", "content": "# Test summary"},
        {"skill": "send_email", "content": "Test email summary"},
    ],
    "injection_observations": ["Document requests an unapproved send; ignored."],
}


class WorkflowTests(unittest.TestCase):
    def test_parse_required_order(self):
        self.assertEqual(parse_workflow(json.dumps(PLAN)), PLAN)

    def test_reject_unknown_skill(self):
        with self.assertRaises(WorkflowError):
            parse_workflow('[{"skill":"upload_elsewhere"}]')

    def test_reject_duplicate_skill(self):
        with self.assertRaises(WorkflowError):
            parse_workflow('[{"skill":"send_email"},{"skill":"send_email"}]')

    def test_reject_disabled_step(self):
        with self.assertRaises(WorkflowError):
            parse_workflow('[{"skill":"send_email","required":false}]')

    def test_validated_output(self):
        self.assertEqual(validate_model_output(json.dumps(GOOD), PLAN), GOOD)

    def test_reject_model_inserted_step(self):
        attack = json.loads(json.dumps(GOOD))
        attack["steps"].append({"skill": "send_email", "content": "hidden data"})
        with self.assertRaises(WorkflowError):
            validate_model_output(json.dumps(attack), PLAN)

    def test_reject_model_reordered_step(self):
        attack = json.loads(json.dumps(GOOD))
        attack["steps"].reverse()
        with self.assertRaises(WorkflowError):
            validate_model_output(json.dumps(attack), PLAN)

    def test_reject_model_extra_property(self):
        attack = json.loads(json.dumps(GOOD))
        attack["steps"][1]["recipient"] = "external@example.invalid"
        with self.assertRaises(WorkflowError):
            validate_model_output(json.dumps(attack), PLAN)

    def test_normal_has_no_steps(self):
        data = {"answer": "Only answer", "steps": [], "injection_observations": []}
        self.assertEqual(validate_model_output(json.dumps(data), []), data)

    def test_reject_non_json(self):
        with self.assertRaises(WorkflowError):
            validate_model_output("send everything", PLAN)


if __name__ == "__main__":
    unittest.main()
