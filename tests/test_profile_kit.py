import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    "foundry-architect": {
        "context-foundry-architect", "goal-loop", "kanban-orchestrator",
        "ai-contract-card-orchestration", "ai-contract-discrepancy-to-delivery",
    },
    "foundry-worker": {
        "context-foundry-worker", "ai-contract-grounded-recovery",
        "ai-contract-verified-implementation-delivery",
    },
    "foundry-auditor": {
        "context-foundry-auditor", "testing", "ai-contract-recovery-audit",
        "ai-contract-verified-delivery-audit",
    },
}


class ProfileKitTests(unittest.TestCase):
    def test_declared_skills_exist_with_frontmatter(self):
        for profile, expected in PROFILES.items():
            root = ROOT / "profiles" / profile
            actual = {path.parent.name for path in (root / "skills").glob("*/SKILL.md")}
            self.assertEqual(actual, expected)
            self.assertTrue((root / "profile.yaml").is_file())
            self.assertTrue((root / "ROLE-CONTRACT.md").is_file())
            self.assertTrue((root / "SOUL.template.md").is_file())
            self.assertTrue((root / "config.template.yaml").is_file())
            role_contract = (root / "ROLE-CONTRACT.md").read_text(encoding="utf-8")
            soul_template = (root / "SOUL.template.md").read_text(encoding="utf-8")
            self.assertIn("role contract", role_contract.lower())
            self.assertIn("# Context Foundry", soul_template)
            for skill in actual:
                content = (root / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertTrue(content.startswith("---\n"), f"{profile}/{skill} lacks frontmatter")

    def test_gateway_port_plan_is_valid(self):
        result = subprocess.run(
            [sys.executable, "scripts/check_foundry_gateway_ports.py"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GATEWAY_PORT_PLAN_VALID", result.stdout)


if __name__ == "__main__":
    unittest.main()
