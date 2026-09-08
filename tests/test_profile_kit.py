import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC_PATH = ROOT / "scripts/sync_foundry_profiles.py"
spec = importlib.util.spec_from_file_location("sync_foundry_profiles", SYNC_PATH)
assert spec and spec.loader
sync_foundry_profiles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_foundry_profiles)
PROFILES = {
    "foundry-architect": {
        "context-foundry-architect", "context-foundry-intake",
        "context-foundry-map", "context-foundry-synthesis",
        "context-foundry-retrospective", "foundry-release-brief",
    },
    "foundry-worker": {
        "context-foundry-worker", "foundry-grounded-recovery",
        "foundry-verified-implementation-delivery", "context-foundry-evidence",
        "foundry-release-delivery",
    },
    "foundry-auditor": {
        "context-foundry-auditor", "testing", "foundry-recovery-audit",
        "foundry-verified-delivery-audit", "context-foundry-evidence-audit",
        "foundry-release-audit",
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

    def test_scope_configuration_preserves_inactive_recovery_only(self):
        config = (ROOT / "config" / "foundry.yaml").read_text(encoding="utf-8")
        self.assertIn("status: inactive_not_scheduled", config)
        self.assertIn("activation: explicit_project_scoped_authorization_required", config)
        self.assertNotIn("loop:\n", config)
        self.assertNotIn("recovery_fallback:", config)
        self.assertNotIn("goal-loop", config)
        self.assertNotIn("kanban-orchestrator", config)
        self.assertNotIn("foundry-card-orchestration", config)
        self.assertNotIn("foundry-discrepancy-to-delivery", config)

    def test_release_coordination_is_role_bound_and_target_guarded(self):
        architect = (ROOT / "profiles/foundry-architect/skills/foundry-release-brief/SKILL.md").read_text(encoding="utf-8").lower()
        worker = (ROOT / "profiles/foundry-worker/skills/foundry-release-delivery/SKILL.md").read_text(encoding="utf-8").lower()
        auditor = (ROOT / "profiles/foundry-auditor/skills/foundry-release-audit/SKILL.md").read_text(encoding="utf-8").lower()
        config = (ROOT / "config/foundry.yaml").read_text(encoding="utf-8")
        for token in ("repository slug", "checkout `origin` remote", "github rest api target"):
            self.assertIn(token, architect)
        self.assertIn("initial tracking issue", architect)
        self.assertIn("committing, commenting, linking, closing, tagging, or publishing as architect", architect)
        self.assertIn("pre-publication auditor pass", worker)
        self.assertIn("candidate auditor pass", worker)
        self.assertIn("external step partially succeeds", worker)
        self.assertIn("pre-publication audit", auditor)
        self.assertIn("post-publication audit", auditor)
        self.assertIn("closure auditor may use its card-derived closure adapter", auditor)
        self.assertIn("authentication: packet_supplied_nonsecret_helper", config)
        self.assertIn("closure: closure_auditor_after_candidate_pass_and_delivery", config)

    def test_external_contract_references_are_role_bound_and_card_body_is_limited(self):
        architect = (ROOT / "profiles/foundry-architect/SOUL.md").read_text(encoding="utf-8")
        worker = (ROOT / "profiles/foundry-worker/SOUL.md").read_text(encoding="utf-8")
        auditor = (ROOT / "profiles/foundry-auditor/SOUL.md").read_text(encoding="utf-8")

        self.assertIn("GitHub Issues or AI.Contract records are the sole work-contract bodies.", architect)
        self.assertIn("create-or-reuse and read back the canonical external contract", architect)
        self.assertIn("role, dependency, and receipt pointer", architect)
        self.assertIn("it never copies the contract body, scope, goals, acceptance criteria, verification, or non-goals", architect)
        self.assertIn("stop and create no execution cards", architect)

        for soul in (worker, auditor):
            self.assertIn("The referenced GitHub Issue or AI.Contract record is the sole work-contract body.", soul)
            self.assertIn("stable URL/ID/revision reference, role, dependency, and receipt pointer", soul)
            self.assertIn("Re-read the external contract immediately before", soul)
            self.assertIn("stop without", soul)
        self.assertIn("stop without source or external writes", worker)
        self.assertIn("stop without an audit verdict or external write", auditor)

    def test_source_assets_deploy_to_an_isolated_target_and_check_source_avoids_it(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "foundry-auditor").mkdir()
            (target / "foundry-architect").mkdir()
            self.assertEqual(sync_foundry_profiles.sync("foundry-auditor", True, target), [])
            self.assertEqual(sync_foundry_profiles.sync("foundry-architect", True, target), [])
            self.assertTrue((target / "foundry-auditor/adapters/closure_auditor.py").is_file())
            self.assertTrue((target / "foundry-architect/adapters/task_bound_issue.py").is_file())
            self.assertTrue((target / "foundry-auditor/ROLE-CONTRACT.md").is_file())
            self.assertEqual(sync_foundry_profiles.sync("foundry-auditor", False, target), [])
            self.assertEqual(sync_foundry_profiles.sync("foundry-architect", False, target), [])
        result = subprocess.run(
            [sys.executable, "scripts/sync_foundry_profiles.py", "--check-source"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mode=check-source", result.stdout)

    def test_closure_continuation_policy_is_role_bound_and_target_neutral(self):
        auditor = (ROOT / "profiles/foundry-auditor/skills/context-foundry-auditor/SKILL.md").read_text(encoding="utf-8")
        architect = (ROOT / "profiles/foundry-architect/skills/context-foundry-architect/SKILL.md").read_text(encoding="utf-8")
        workflow = "Closure Auditor PASS → fresh Architect selection pass → smallest justified next tranche."
        scope = "Foundry workflow applies to every authorized target, including active game resources."

        self.assertIn(workflow, auditor)
        self.assertIn("Closure PASS transfers selection only; it does not select or authorize a speculative successor.", auditor)
        self.assertIn("Candidate or Closure `REQUEST_CHANGES` and `BLOCKED_WITH_EVIDENCE` retain the independent, narrow corrective path", auditor)
        self.assertIn("do not start an unrelated tranche.", auditor)
        self.assertIn("Closure Auditor verification and Issue-close authority remain independent and unchanged", auditor)
        self.assertIn(scope, auditor)
        self.assertIn("does not impose game mechanics or product behavior", auditor)
        self.assertIn("does not change a target merely to codify this policy.", auditor)

        self.assertIn(workflow, architect)
        self.assertIn("inspects current specifications and open/nonterminal work", architect)
        self.assertIn("selects only the smallest evidence-justified tranche", architect)
        self.assertIn("not permission to create a speculative implementation chain", architect)
        self.assertIn("`NO ACTIONABLE NEXT STEP`", architect)
        self.assertIn("specifications are exhausted", architect)
        self.assertIn("non-corrective tool, capability, or integration; onboarding or access; a material decision", architect)
        self.assertIn("not a simple corrective action", architect)
        self.assertIn("exhausted boundary, non-corrective dependency, and smallest restart decision or enablement", architect)
        self.assertIn(scope, architect)
        self.assertIn("does not impose game mechanics or product behavior", architect)
        self.assertIn("does not change a target merely to codify this policy.", architect)

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
