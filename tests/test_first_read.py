import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "first_read.py"
SOURCE = ROOT / "examples" / "detective-turnip.md"


class FirstReadCLITest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "reading.db"

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, expected=0):
        result = subprocess.run(
            [sys.executable, str(CLI), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, expected, result.stderr)
        return result

    def start(self):
        return self.run_cli(
            "start", "--db", str(self.db), "--source", str(SOURCE), "--target-words", "25"
        )

    def test_response_gate_and_exact_replay(self):
        self.start()
        first = self.run_cli("next", "--db", str(self.db)).stdout
        self.assertIn("Detective Turnip entered", first)
        replay = self.run_cli("next", "--db", str(self.db)).stdout
        self.assertIn(first.strip(), replay)
        self.assertIn("response required", replay)
        self.run_cli("respond", "--db", str(self.db), "--text", "The sock knows too much.")
        second = self.run_cli("next", "--db", str(self.db)).stdout
        self.assertNotEqual(first.strip(), second.strip())

    def test_response_is_immutable(self):
        self.start()
        self.run_cli("next", "--db", str(self.db))
        self.run_cli("respond", "--db", str(self.db), "--text", "Original thought")
        result = self.run_cli(
            "respond", "--db", str(self.db), "--text", "Hindsight manicure", expected=2
        )
        self.assertIn("sealed", result.stderr)

    def test_resume_from_fresh_process_contains_only_revealed_material(self):
        self.start()
        first = self.run_cli("next", "--db", str(self.db)).stdout.strip()
        self.run_cli("respond", "--db", str(self.db), "--text", "Mustard is a clue.")
        self.run_cli("checkpoint", "--db", str(self.db), "--text", "I distrust the empty dryers.")
        packet = self.run_cli("resume", "--db", str(self.db)).stdout
        self.assertIn(first, packet)
        self.assertIn("Mustard is a clue.", packet)
        self.assertIn("I distrust the empty dryers.", packet)
        self.assertNotIn("purple sock shouted", packet)
        self.assertNotIn("remaining", packet.lower())

    def test_start_refuses_to_overwrite_session(self):
        self.start()
        result = self.run_cli(
            "start", "--db", str(self.db), "--source", str(SOURCE), expected=2
        )
        self.assertIn("Refusing to overwrite", result.stderr)


if __name__ == "__main__":
    unittest.main()
