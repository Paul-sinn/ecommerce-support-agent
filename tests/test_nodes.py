import unittest
from types import SimpleNamespace
from unittest.mock import patch

from graph.nodes import billing_agent as billing_agent_module
from graph.nodes import order_agent as order_agent_module
from graph.nodes import triage_router as triage_router_module


class FakeLLM:
    def __init__(self, content: str):
        self.content = content
        self.prompts = []

    def invoke(self, prompt: str):
        self.prompts.append(prompt)
        return SimpleNamespace(content=self.content)


class NodeTests(unittest.TestCase):
    def test_triage_router_parses_structured_json(self):
        fake_llm = FakeLLM('{"category":"order","priority":"medium","missing_fields":["order_id"]}')

        with patch.object(triage_router_module, "llm", fake_llm):
            state = {"messages": [{"role": "user", "content": "Where is my package?"}]}
            result = triage_router_module.triage_router(state)

        self.assertEqual(
            result,
            {
                "category": "order",
                "priority": "medium",
                "missing_fields": ["order_id"],
            },
        )
        self.assertIn("Where is my package?", fake_llm.prompts[0])

    def test_order_agent_returns_model_response(self):
        fake_llm = FakeLLM("Order support response")

        with patch.object(order_agent_module, "get_llm_by_priority", lambda priority: fake_llm):
            state = {
                "messages": [{"role": "user", "content": "Can I cancel after delivery?"}],
                "priority": "high",
            }
            result = order_agent_module.order_agent(state)

        self.assertEqual(result["final_reply"], "Order support response")
        self.assertIn("Can I cancel after delivery?", fake_llm.prompts[0])

    def test_billing_agent_returns_model_response(self):
        fake_llm = FakeLLM("Billing support response")

        with patch.object(billing_agent_module, "get_llm_by_priority", lambda priority: fake_llm):
            state = {
                "messages": [{"role": "user", "content": "I was charged twice."}],
                "priority": "high",
            }
            result = billing_agent_module.billing_agent(state)

        self.assertEqual(result["final_reply"], "Billing support response")
        self.assertIn("I was charged twice.", fake_llm.prompts[0])


if __name__ == "__main__":
    unittest.main()
