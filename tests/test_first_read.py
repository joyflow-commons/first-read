import subprocess
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from first_read import is_scene_break, split_passages


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

    def test_step_seals_and_reveals_atomically(self):
        self.start()
        first = self.run_cli("next", "--db", str(self.db)).stdout
        stepped = self.run_cli(
            "step", "--db", str(self.db), "--text", "The sock knows too much."
        ).stdout
        self.assertIn("Response sealed.", stepped)
        self.assertNotIn(first.strip(), stepped)
        with sqlite3.connect(self.db) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT body FROM responses WHERE passage_position = 0"
                ).fetchone()[0],
                "The sock knows too much.",
            )
            self.assertEqual(
                connection.execute(
                    "SELECT current_passage FROM session WHERE id = 1"
                ).fetchone()[0],
                1,
            )

    def test_begin_creates_session_and_reveals_first_passage(self):
        result = self.run_cli(
            "begin",
            "--db",
            str(self.db),
            "--source",
            str(SOURCE),
            "--target-words",
            "25",
        )
        self.assertIn("Reading session created.", result.stdout)
        self.assertIn("Detective Turnip entered", result.stdout)
        with sqlite3.connect(self.db) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT current_passage FROM session WHERE id = 1"
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM reveals").fetchone()[0],
                1,
            )
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM responses").fetchone()[0],
                0,
            )

    def test_step_completes_without_an_extra_next_call(self):
        self.start()
        output = self.run_cli("next", "--db", str(self.db)).stdout
        for index in range(20):
            output = self.run_cli(
                "step", "--db", str(self.db), "--text", f"Response {index}"
            ).stdout
            if "Reading session complete" in output:
                break
        else:
            self.fail("Atomic stepping did not complete within the safety bound")
        packet = self.run_cli("resume", "--db", str(self.db)).stdout
        self.assertIn("Reading complete", packet)

    def test_plan_estimates_without_revealing_prose_or_creating_state(self):
        result = self.run_cli(
            "plan", "--source", str(SOURCE), "--target-words", "25"
        )
        self.assertIn("no prose revealed", result.stdout)
        self.assertIn("Words:", result.stdout)
        self.assertIn("Expected passages / reading turns:", result.stdout)
        self.assertIn(
            "Expected session calls after preflight with begin + step:",
            result.stdout,
        )
        self.assertNotIn("Detective Turnip entered", result.stdout)
        self.assertNotIn("alphabetize", result.stdout)
        self.assertFalse(self.db.exists())

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

    def test_prior_exposure_receipt_survives_resume(self):
        self.run_cli(
            "start",
            "--db",
            str(self.db),
            "--source",
            str(SOURCE),
            "--prior-exposure",
            "I accidentally saw the first purple sock.",
        )
        packet = self.run_cli("resume", "--db", str(self.db)).stdout
        self.assertIn("Prior-exposure receipt", packet)
        self.assertIn("I accidentally saw the first purple sock.", packet)
        self.assertNotIn("orchestral mustard", packet)

    def test_full_lifecycle_never_leaks_ending_early(self):
        self.start()
        revealed = []
        for index in range(20):
            output = self.run_cli("next", "--db", str(self.db)).stdout.strip()
            if output.startswith("[End of work"):
                break
            revealed.append(output)
            if len(revealed) < 2:
                self.assertNotIn("alphabetize", output)
            self.run_cli(
                "respond",
                "--db",
                str(self.db),
                "--text",
                f"Synthetic response {index}",
            )
        else:
            self.fail("Reading did not reach its ending within the safety bound")
        self.assertIn("alphabetize", revealed[-1])
        self.assertNotIn("alphabetize", "\n".join(revealed[:-1]))
        packet = self.run_cli("resume", "--db", str(self.db)).stdout
        self.assertIn("Reading complete", packet)

    def test_ornamental_scene_break_forces_passage_boundary(self):
        divider = "– – \\= \\= ( \\* ) \\= \\= – –"
        text = (
            "The first scene closes with a smile.\n\n"
            f"{divider}\n\n"
            "The next room opens in sunlight."
        )
        passages = split_passages(text, target_words=500)
        self.assertEqual(
            passages,
            [
                "The first scene closes with a smile.",
                f"{divider}\n\nThe next room opens in sunlight.",
            ],
        )
        self.assertTrue(is_scene_break(divider))
        self.assertFalse(is_scene_break("...and then she answered."))

    def test_single_line_paragraph_export_still_flows(self):
        text = "\r\n".join(
            [
                "People Person",
                "First paragraph carries the opening setup and establishes the voice.",
                "Second paragraph introduces a warning that should remain suspenseful.",
                "Third paragraph changes the situation before the ending can be seen.",
                "Fourth paragraph contains the ending and must not leak into passage one.",
            ]
        )
        passages = split_passages(text, target_words=20)
        self.assertGreater(len(passages), 1)
        self.assertNotIn("Fourth paragraph", passages[0])
        self.assertEqual("\n\n".join(passages).count("Fourth paragraph"), 1)

    def test_start_refuses_oversized_passage_before_reveal(self):
        malformed = Path(self.temp.name) / "malformed.txt"
        malformed.write_text("word " * 1000, encoding="utf-8")
        result = self.run_cli(
            "start",
            "--db",
            str(self.db),
            "--source",
            str(malformed),
            "--target-words",
            "100",
            expected=2,
        )
        self.assertIn("oversized passage", result.stderr.lower())
        self.assertFalse(self.db.exists())


if __name__ == "__main__":
    unittest.main()
