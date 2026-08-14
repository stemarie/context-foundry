import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    "foundry-architect": {
        "context-foundry-architect", "goal-loop", "kanban-orchestrator",
        "foundry-card-orchestration", "foundry-discrepancy-to-delivery",
        "context-foundry-intake", "context-foundry-map", "context-foundry-synthesis",
        "context-foundry-retrospective",
    },
    "foundry-worker": {
        "context-foundry-worker", "foundry-grounded-recovery",
        "foundry-verified-implementation-delivery", "context-foundry-evidence",
    },
    "foundry-auditor": {
        "context-foundry-auditor", "testing", "foundry-recovery-audit",
        "foundry-verified-delivery-audit", "context-foundry-evidence-audit",
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
            self.assertTrue((root / "SOUL.md").is_file())
            self.assertTrue((root / "config.yaml").is_file())
            role_contract = (root / "ROLE-CONTRACT.md").read_text(encoding="utf-8")
            soul_template = (root / "SOUL.md").read_text(encoding="utf-8")
            self.assertIn("role contract", role_contract.lower())
            self.assertIn("# Context Foundry", soul_template)
            for skill in actual:
                content = (root / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertTrue(content.startswith("---\n"), f"{profile}/{skill} lacks frontmatter")
                self.assertNotIn("ai-contract-", content.lower(), f"{profile}/{skill} retains old ownership")
                self.assertNotIn("source: ai.contract", content.lower(), f"{profile}/{skill} retains old source")

    def test_generic_skill_pack_is_role_bound_and_runtime_free(self):
        expected = {
            "foundry-architect": {
                "context-foundry-intake", "context-foundry-map",
                "context-foundry-synthesis", "context-foundry-retrospective",
            },
            "foundry-worker": {"context-foundry-evidence"},
            "foundry-auditor": {"context-foundry-evidence-audit"},
        }
        forbidden = ("cronjob(", "schedule=", "gateway restart", "api_server_key")
        for profile, skills in expected.items():
            for skill in skills:
                content = (ROOT / "profiles" / profile / "skills" / skill / "SKILL.md").read_text(encoding="utf-8").lower()
                self.assertIn("## contract", content)
                self.assertIn("## verification", content)
                self.assertTrue(all(token not in content for token in forbidden), f"{profile}/{skill} adds runtime behavior")

    def test_contract_orchestration_kit_is_self_validating(self):
        result = subprocess.run(
            [sys.executable, "kits/contract-orchestration/verification/validate.py", "--self-test"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "VALID")

    def test_gateway_port_plan_is_valid(self):
        result = subprocess.run(
            [sys.executable, "scripts/check_foundry_gateway_ports.py"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GATEWAY_PORT_PLAN_VALID", result.stdout)


if __name__ == "__main__":
    unittest.main()
