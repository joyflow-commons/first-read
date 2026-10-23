import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from first_read import close_chapter, connect, next_passage, start

CLI = Path(__file__).resolve().parents[1] / 'first_read.py'
BOOK = '## The brass kettle\n\nOPENING_ONLY the kettle politely asks for a hat.\n\nSECOND_PASSAGE the hat refuses to negotiate today.\n\n## SECRET_TITLE\n\nSECRET_END the cupboard was elected mayor yesterday.\n'


class ChapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'book.db'
        self.source = Path(self.temp.name) / 'SECRET_FILENAME.md'
        self.source.write_text(BOOK)

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(CLI), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stderr)
        return result.stdout + result.stderr

    def begin(self):
        return self.cli('begin', '--db', str(self.db), '--source', str(self.source), '--chapter-level', '2', '--target-words', '8')

    def reach_seam(self):
        self.begin()
        return self.cli('step', '--db', str(self.db), '--text', 'A polite kettle.')

    def close(self, *args, ok=True):
        return self.cli('close-chapter', '--db', str(self.db), '--card', 'The hat refuses.', '--state-delta', 'Negotiations stalled.', *args, ok=ok)

    def assert_blind(self, output):
        for secret in ('SECRET_TITLE', 'SECRET_END', 'SECRET_FILENAME'):
            self.assertNotIn(secret, output)

    def test_plan_is_anonymous_and_bad_structure_fails_before_creation(self):
        self.assert_blind(self.cli('plan', '--source', str(self.source), '--chapter-level', '2'))
        for source in ('preamble\n\n' + BOOK, 'no headings', '## Empty\n\n## Empty too\n', '## Code\n\n```\n## Fake\n```', '# Part\n\n' + BOOK):
            self.source.write_text(source)
            self.cli('begin', '--db', str(self.db), '--source', str(self.source), '--chapter-level', '2', ok=False)
            self.assertFalse(self.db.exists())

    def test_seam_cold_resume_deliberate_open_and_final_close(self):
        self.assert_blind(self.reach_seam())
        self.assert_blind(self.cli('step', '--db', str(self.db), '--text', 'Oops', ok=False))
        with connect(self.db) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM responses').fetchone()[0], 1)
        self.assert_blind(self.close('--text', 'That hat has opinions.'))
        for command in ('next', 'resume'):
            packet = self.cli(command, '--db', str(self.db))
            self.assert_blind(packet)
        self.assertIn('The hat refuses.', packet)
        self.assertIn('Negotiations stalled.', packet)
        self.close('--text', 'Rewrite', ok=False)
        opened = self.cli('open-chapter', '--db', str(self.db))
        self.assertIn('SECRET_TITLE', opened)
        self.assertIn('SECRET_END', opened)
        continued = self.cli('resume', '--db', str(self.db))
        self.assertIn('The hat refuses.', continued)
        self.assertIn('Negotiations stalled.', continued)
        self.cli('open-chapter', '--db', str(self.db), ok=False)
        self.assertIn('complete', self.close('--text', 'Democracy in the cupboard.'))
        self.assertIn('Reading complete', self.cli('resume', '--db', str(self.db)))
        self.assertIn('End of work', self.cli('next', '--db', str(self.db)))

    def test_respond_cannot_bypass_gate_and_existing_response_is_preserved(self):
        self.reach_seam()
        self.cli('respond', '--db', str(self.db), '--text', 'Already sealed.')
        self.assert_blind(self.cli('next', '--db', str(self.db)))
        self.close('--text', 'Replacement', ok=False)
        self.close()
        self.assertIn('Already sealed.', self.cli('resume', '--db', str(self.db)))

    def test_early_close_and_empty_artifacts_leave_state_unchanged(self):
        self.begin()
        self.close('--text', 'Too early', ok=False)
        self.cli('open-chapter', '--db', str(self.db), ok=False)
        self.cli('step', '--db', str(self.db), '--text', 'Go on.')
        self.close(ok=False)
        self.cli('close-chapter', '--db', str(self.db), '--text', 'response', '--card', ' ', '--state-delta', 'state', ok=False)
        with connect(self.db) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM responses').fetchone()[0], 1)
            self.assertIsNone(connection.execute('SELECT closed_at FROM chapters WHERE position=0').fetchone()[0])

    def test_failure_rolls_back_response_and_all_artifacts(self):
        self.reach_seam()
        with connect(self.db) as connection:
            connection.execute("CREATE TRIGGER fail_close BEFORE UPDATE ON chapters BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            close_chapter(self.db, 'must roll back', 'card', 'state')
        with connect(self.db) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM responses').fetchone()[0], 1)
            chapter = connection.execute('SELECT * FROM chapters WHERE position=0').fetchone()
            self.assertIsNone(chapter['closed_at'])
            self.assertIsNone(chapter['card'])
            self.assertIsNone(chapter['state_delta'])
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM reveals').fetchone()[0], 2)

    def test_indented_markdown_headings_preserve_hard_boundary(self):
        self.source.write_text('## One\n\nOpening.\n\n   ## SECRET_TITLE\n\nSECRET_END.')
        self.begin()
        self.assert_blind(self.cli('step', '--db', str(self.db), '--text', 'No crossing', ok=False))
        self.close('--text', 'Stop here.')
        self.assert_blind(self.cli('resume', '--db', str(self.db)))
        self.assertIn('SECRET_END', self.cli('open-chapter', '--db', str(self.db)))

    def test_unstructured_sessions_still_work(self):
        start(self.db, self.source, 8)
        self.assertIn('OPENING_ONLY', next_passage(self.db))
        self.close('--text', 'No chapters', ok=False)
        self.cli('open-chapter', '--db', str(self.db), ok=False)


if __name__ == '__main__':
    unittest.main()
