import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class DirectMaintenanceBoundaryTests(unittest.TestCase):
    def test_every_delivery_role_states_direct_maintenance_boundary(self):
        for role, skill in (("architect", "foundry-release-brief"), ("worker", "foundry-release-delivery"), ("auditor", "foundry-release-audit")):
            with self.subTest(role=role):
                text = (ROOT / f"profiles/foundry-{role}/skills/{skill}/SKILL.md").read_text()
                self.assertIn("## Direct Foundry maintenance boundary", text)
                self.assertIn("Do not create Kanban maintenance cards", text)
                self.assertIn("AI.Contract", text)
                self.assertIn("current authorization", text)

if __name__ == "__main__":
    unittest.main()
