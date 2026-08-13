import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_evidence.py"

class ValidateEvidenceTests(unittest.TestCase):
    def write_packet(self, directory):
        packet = Path(directory) / "packet.md"
        packet.write_text("packet_id: CF-test\nquestion: Is the evidence cited?\n")
        return packet

    def test_accepts_cited_fact(self):
        with tempfile.TemporaryDirectory() as directory:
            packet = self.write_packet(directory)
            evidence = Path(directory) / "evidence.json"
            evidence.write_text(json.dumps({"packet_id":"CF-test","question":"Is the evidence cited?","claims":[{"claim_id":"C-1","claim":"A fact","classification":"fact","confidence":"high","evidence":[{"source_id":"src-001","location":"line 1","excerpt":"proof","observed_at":"2026-01-01T00:00:00Z"}],"limitations":[]}]}))
            completed = subprocess.run([sys.executable, str(SCRIPT), str(evidence), "--packet", str(packet)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn('"status": "valid"', completed.stdout)

    def test_rejects_uncited_fact(self):
        with tempfile.TemporaryDirectory() as directory:
            packet = self.write_packet(directory)
            evidence = Path(directory) / "evidence.json"
            evidence.write_text(json.dumps({"packet_id":"CF-test","question":"Is the evidence cited?","claims":[{"claim_id":"C-1","claim":"A fact","classification":"fact","confidence":"high","evidence":[],"limitations":[]}]}))
            completed = subprocess.run([sys.executable, str(SCRIPT), str(evidence), "--packet", str(packet)], capture_output=True, text=True)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("uncited fact", completed.stderr)

if __name__ == "__main__":
    unittest.main()
