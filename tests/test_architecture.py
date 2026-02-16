import unittest

from main import route_to_agent
from graph.nodes.policy_completeness_guard import policy_completeness_guard
from graph.nodes.policy_risk_guard import policy_risk_guard
from graph.nodes.policy_scope_guard import policy_scope_guard


class ArchitectureTests(unittest.TestCase):
    def test_route_to_agent_ends_when_policy_blocks(self):
        state = {"policy_status": "OUT_OF_SCOPE", "category": "order"}
        self.assertEqual(route_to_agent(state), "end")

    def test_route_to_agent_routes_to_order(self):
        state = {"policy_status": "VALID", "category": "order"}
        self.assertEqual(route_to_agent(state), "order_agent")

    def test_route_to_agent_routes_to_billing(self):
        state = {"policy_status": "VALID", "category": "billing"}
        self.assertEqual(route_to_agent(state), "billing_agent")

    def test_route_to_agent_ends_for_unknown_category(self):
        state = {"policy_status": "VALID", "category": "unknown"}
        self.assertEqual(route_to_agent(state), "end")

    def test_policy_scope_guard_blocks_unknown_category(self):
        result = policy_scope_guard({"category": "unknown"})
        self.assertEqual(result["policy_status"], "OUT_OF_SCOPE")

    def test_policy_scope_guard_allows_supported_category(self):
        result = policy_scope_guard({"category": "order"})
        self.assertEqual(result["policy_status"], "VALID")

    def test_policy_completeness_guard_blocks_when_fields_missing(self):
        result = policy_completeness_guard({"missing_fields": ["order_id", "email"]})
        self.assertEqual(result["policy_status"], "NEED_MORE_INFO")
        self.assertIn("order_id", result["policy_message"])

    def test_policy_completeness_guard_allows_complete_request(self):
        result = policy_completeness_guard({"missing_fields": []})
        self.assertEqual(result["policy_status"], "VALID")

    def test_policy_risk_guard_high_for_high_priority_billing(self):
        result = policy_risk_guard({"category": "billing", "priority": "high"})
        self.assertEqual(result["policy_risk_level"], "HIGH")

    def test_policy_risk_guard_low_otherwise(self):
        result = policy_risk_guard({"category": "order", "priority": "medium"})
        self.assertEqual(result["policy_risk_level"], "LOW")


if __name__ == "__main__":
    unittest.main()
