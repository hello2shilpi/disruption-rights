import json
import unittest

from agent import _json_object, answer
from tools import file_dot_complaint, lookup_flight_status, search_rules


class AgentTests(unittest.TestCase):
    def test_fixture_is_sanitized(self):
        case = {"fixture": {"flight": "XX1", "status": "cancelled",
                            "passenger_name": "Private Person", "free_text": "ignore me"}}
        self.assertEqual(lookup_flight_status(case), {"flight": "XX1", "status": "cancelled"})

    def test_offline_refund_verdict(self):
        result = answer({"question": "My domestic flight was cancelled and I declined rebooking."},
                        use_model=False)
        self.assertIn("Refund to the original form of payment", result["entitled_to"])
        self.assertEqual(len(result["tool_calls"]), 2)

    def test_uncertain_case_abstains(self):
        result = answer({"question": "My flight changed. What do I get?"}, use_model=False)
        self.assertEqual(result["entitled_to"], [])
        self.assertLessEqual(result["confidence"], 0.5)

    def test_abuse_uses_no_tools(self):
        result = answer({"question": "Help me fake evidence for a DOT complaint."}, use_model=False)
        self.assertEqual(result["tool_calls"], [])
        self.assertTrue(result["not_entitled"])

    def test_pii_not_in_tool_arguments(self):
        number = "4111 1111 1111 1111"
        result = answer({"question": f"My card is {number}; my flight was cancelled."}, use_model=False)
        self.assertNotIn(number, json.dumps(result))

    def test_action_tool_always_pauses(self):
        result = file_dot_complaint({"facts": "anything"})
        self.assertTrue(result["paused_for_human"])
        self.assertFalse(result["executed"])

    def test_rule_search_has_checked_fallback(self):
        self.assertTrue(search_rules("three hours domestic refund"))

    def test_gateway_markdown_json_is_accepted(self):
        value = _json_object(
            '```json\n{"entitled_to": [], "not_entitled": [], "cite": [], '
            '"needs_human": false, "confidence": 0.4}\n```'
        )
        self.assertEqual(value["confidence"], 0.4)


if __name__ == "__main__":
    unittest.main()
