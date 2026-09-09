import importlib.util
import json
import os
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
    "foundry-brainiac": set(),
    "foundry-watchdog": {"foundry-lifecycle-orchestration"},
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
            expected_heading = {
                "foundry-brainiac": "# Brainiac",
                "foundry-watchdog": "# Foundry Watchdog",
            }.get(profile, "# Context Foundry")
            self.assertIn(expected_heading, soul_template)
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

    def test_watchdog_is_board_only_and_does_not_add_runtime_automation(self):
        profile = ROOT / "profiles/foundry-watchdog"
        contract = (profile / "ROLE-CONTRACT.md").read_text(encoding="utf-8").lower()
        soul = (profile / "SOUL.md").read_text(encoding="utf-8").lower()
        skill = (profile / "skills/foundry-lifecycle-orchestration/SKILL.md").read_text(encoding="utf-8").lower()
        for token in ("observes only", "never authors", "edits source", "operates github", "accesses credentials", "changes cron", "issues an audit"):
            self.assertIn(token, contract)
        self.assertIn("empty or unchanged", soul)
        self.assertIn("do nothing", soul)
        self.assertIn("re-read every cited card", skill)
        self.assertNotIn("cronjob(", skill)

    def test_watchdog_scanner_handles_current_envelopes_and_nonhealthy_scope(self):
        scanner = ROOT / "profiles/foundry-watchdog/scripts/foundry_watchdog_scan.py"
        identity = (
            "Canonical external contract: https://github.com/stemarie/context-foundry/issues/19\n"
            "Contract ID/revision: Issue #19 / FOUNDRY-WATCHDOG-INITIAL-CONTRACT-V1 / " + "a" * 64
        )
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "tasks.json"
            fixture.write_text(json.dumps({"tasks": []}), encoding="utf-8")
            empty = subprocess.run([sys.executable, scanner, "--input", fixture], capture_output=True, text=True)
            self.assertEqual(empty.returncode, 0, empty.stderr)
            self.assertEqual(empty.stdout, "")

            fixture.write_text(json.dumps({"tasks": [
                {"id": "t_worker", "status": "done", "title": "Worker: complete kit", "body": identity,
                 "events": [{"kind": "completed", "created_at": 1, "payload": {"candidate": "a"}}]},
                {"id": "t_auditor", "status": "done", "title": "Candidate Auditor: audit kit", "body": identity,
                 "runs": [{"id": 2, "status": "completed", "summary": "PASS", "metadata": {"verdict": "PASS"}}]},
            ]}), encoding="utf-8")
            first = subprocess.run([sys.executable, scanner, "--input", fixture], capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(first.stdout)
            self.assertEqual([event["id"] for event in payload["events"]], ["t_auditor", "t_worker"])
            digest_file = Path(directory) / "digest"
            digest_file.write_text(payload["digest"], encoding="utf-8")
            unchanged = subprocess.run(
                [sys.executable, scanner, "--input", fixture, "--previous-digest-file", digest_file],
                capture_output=True, text=True,
            )
            self.assertEqual(unchanged.returncode, 0, unchanged.stderr)
            self.assertEqual(unchanged.stdout, "")

            changed = json.loads(fixture.read_text(encoding="utf-8"))
            changed["tasks"][1]["runs"][0]["summary"] = "REQUEST_CHANGES"
            fixture.write_text(json.dumps(changed), encoding="utf-8")
            changed_result = subprocess.run([sys.executable, scanner, "--input", fixture], capture_output=True, text=True)
            self.assertEqual(changed_result.returncode, 0, changed_result.stderr)
            self.assertNotEqual(json.loads(changed_result.stdout)["digest"], payload["digest"])

            fixture.write_text(json.dumps({"tasks": [
                {"id": "t_historical", "status": "done", "title": "Worker: historical", "body": identity},
            ]}), encoding="utf-8")
            historical = subprocess.run([sys.executable, scanner, "--input", fixture], capture_output=True, text=True)
            self.assertEqual(historical.returncode, 0, historical.stderr)
            self.assertEqual(historical.stdout, "")

            fixture.write_text(json.dumps({"tasks": [
                {"id": "t_malformed", "status": "review", "title": "Candidate Auditor: malformed", "body": "Canonical external contract: https://github.com/stemarie/context-foundry/issues/19"},
                {"id": "t_unrecognized", "status": "review", "title": "Worker: foreign", "body": "Canonical external contract: https://github.com/example/other/issues/19\nContract ID/revision: Issue #19 / MARKER / " + "b" * 64},
            ]}), encoding="utf-8")
            nonhealthy = subprocess.run([sys.executable, scanner, "--input", fixture], capture_output=True, text=True)
            self.assertEqual(nonhealthy.returncode, 0, nonhealthy.stderr)
            self.assertEqual(json.loads(nonhealthy.stdout)["scanner_status"], "non_healthy")

            closure = (
                "Canonical external contract: https://github.com/stemarie/context-foundry/issues/19\n"
                "Contract ID/revision: Issue #19 / FOUNDRY-WATCHDOG-INITIAL-CONTRACT-V1\n"
                "Role: Closure Auditor\nDependency: completed direct Delivery parent\nReceipt pointer: Delivery `t_delivery`"
            )
            fixture.write_text(json.dumps({"tasks": [{"id": "t_closure", "status": "review", "title": "Closure Auditor: close", "body": closure,
                                                       "events": [{"kind": "review_requested", "created_at": 2}]}]}), encoding="utf-8")
            closure_result = subprocess.run([sys.executable, scanner, "--input", fixture], capture_output=True, text=True)
            self.assertEqual(closure_result.returncode, 0, closure_result.stderr)
            self.assertEqual(json.loads(closure_result.stdout)["events"][0]["contract"]["sha256"], "")

            legacy = (
                "External contract: https://github.com/stemarie/context-foundry/issues/19\n"
                "Contract identity/revision: Issue #19; `FOUNDRY-WATCHDOG-INITIAL-CONTRACT-V1`; body SHA-256 `" + "c" * 64 + "`."
            )
            fixture.write_text(json.dumps({"tasks": [{"id": "t_legacy", "status": "review", "title": "Worker: legacy", "body": legacy}]}), encoding="utf-8")
            legacy_result = subprocess.run([sys.executable, scanner, "--input", fixture], capture_output=True, text=True)
            self.assertEqual(legacy_result.returncode, 0, legacy_result.stderr)
            self.assertEqual(json.loads(legacy_result.stdout)["events"][0]["contract"]["sha256"], "c" * 64)

    def test_watchdog_wrapper_installer_is_explicit_and_executable(self):
        installer = ROOT / "scripts/install_foundry_watchdog_wrapper.py"
        source = ROOT / "profiles/foundry-watchdog/scripts/foundry_watchdog_scan.sh"
        with tempfile.TemporaryDirectory() as directory:
            environment = {**os.environ, "HOME": directory}
            result = subprocess.run([sys.executable, installer], cwd=ROOT, env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            target = Path(directory) / ".hermes/scripts/foundry_watchdog_scan.sh"
            self.assertTrue(target.is_file())
            self.assertTrue(os.access(target, os.X_OK))
            self.assertEqual(target.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))
            self.assertIn("cron_created=false gateway_started=false", result.stdout)

    def test_sync_installs_watchdog_scanner_and_preserves_runtime_only_files(self):
        sync = ROOT / "scripts/sync_foundry_profiles.py"
        with tempfile.TemporaryDirectory() as directory:
            profiles = Path(directory) / ".hermes/profiles"
            for profile in PROFILES:
                (profiles / profile).mkdir(parents=True)
            worker = profiles / "foundry-worker"
            runtime_config = "platforms:\n  api_server:\n    enabled: true\n    key: private\n"
            (worker / "config.yaml").write_text(runtime_config, encoding="utf-8")
            (worker / ".env").write_text("PRIVATE_TOKEN=not-source\n", encoding="utf-8")
            environment = {**os.environ, "HOME": directory}
            apply = subprocess.run([sys.executable, sync, "--apply"], cwd=ROOT, env=environment, capture_output=True, text=True)
            self.assertEqual(apply.returncode, 0, apply.stderr)
            self.assertIn("profiles=5", apply.stdout)
            scanner = profiles / "foundry-watchdog/scripts/foundry_watchdog_scan.py"
            wrapper = profiles / "foundry-watchdog/scripts/foundry_watchdog_scan.sh"
            self.assertTrue(scanner.is_file())
            self.assertTrue(os.access(scanner, os.X_OK))
            self.assertTrue(os.access(wrapper, os.X_OK))
            self.assertIn("api_server:\n    enabled: true", (worker / "config.yaml").read_text(encoding="utf-8"))
            self.assertEqual((worker / ".env").read_text(encoding="utf-8"), "PRIVATE_TOKEN=not-source\n")
            fake_hermes = Path(directory) / "hermes"
            fake_hermes.write_text("#!/bin/sh\nprintf '%s\\n' '{\"tasks\": []}'\n", encoding="utf-8")
            fake_hermes.chmod(0o755)
            resolved = subprocess.run([wrapper], env={**environment, "HERMES_BIN": str(fake_hermes)}, capture_output=True, text=True)
            self.assertEqual(resolved.returncode, 0, resolved.stderr)
            self.assertEqual(resolved.stdout, "")
            check = subprocess.run([sys.executable, sync, "--check"], cwd=ROOT, env=environment, capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertIn("PROFILE_KIT_VALID", check.stdout)

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
            (target / "foundry-brainiac").mkdir()
            self.assertEqual(sync_foundry_profiles.sync("foundry-auditor", True, target), [])
            self.assertEqual(sync_foundry_profiles.sync("foundry-architect", True, target), [])
            self.assertEqual(sync_foundry_profiles.sync("foundry-brainiac", True, target), [])
            self.assertTrue((target / "foundry-auditor/adapters/closure_auditor.py").is_file())
            self.assertTrue((target / "foundry-auditor/schemas/closure_auditor_packet.schema.json").is_file())
            self.assertTrue((target / "foundry-architect/adapters/task_bound_issue.py").is_file())
            self.assertTrue((target / "foundry-auditor/ROLE-CONTRACT.md").is_file())
            self.assertTrue((target / "foundry-brainiac/SOUL.md").is_file())
            self.assertEqual(sync_foundry_profiles.sync("foundry-auditor", False, target), [])
            self.assertEqual(sync_foundry_profiles.sync("foundry-architect", False, target), [])
            self.assertEqual(sync_foundry_profiles.sync("foundry-brainiac", False, target), [])
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
