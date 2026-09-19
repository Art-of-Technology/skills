"""Exercise accepted and rejected fixtures in isolated copies, with and without optimization.

Run: uv run --with pyyaml --with tiktoken python tests/aot-brief/test_validation.py
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class ValidationBoundaries(unittest.TestCase):
    def test_boundaries_in_both_modes(self):
        source = Path(__file__).resolve().parents[2]
        regular = '\n'.join(['DONE: Pass tests.'] * 8)
        note = 'Note: Restarting clears cached sessions.'
        warning = 'Warning: Deleting backups is irreversible. Reply yes to proceed.'
        cases = (
            ('note_at_limit', 'reply', regular + '\n' + note, None),
            ('note_before_question', 'reply',
             'DECIDE: 1. Keep backups (default).\n' + note +
             '\nDECIDE: Which option do you prefer?', None),
            ('standalone_warning', 'reply', warning, None),
            ('blank_separator', 'reply', 'DONE: Pass tests.\n\nNEXT: Ship fixes.', None),
            ('whitespace_separator', 'reply', 'DONE: Pass tests.\n \t \nNEXT: Ship fixes.', None),
            ('blank_lines_over_limit', 'reply', '\n\n'.join(['DONE: Pass tests.'] * 5),
             'expected 1-8 reply lines'),
            ('blank_only', 'reply', '\n \t \n', 'expected at least one block label'),
            ('two_notes', 'reply', regular + '\n' + note + '\n' + note,
             'allow at most one Note: line'),
            ('ten_lines', 'reply', regular + '\nDONE: Pass lint.\n' + note,
             'expected 1-8 reply lines'),
            ('long_note', 'reply', 'DONE: Pass tests.\nNote: ' + 'word ' * 12,
             'line 2 exceeds 12 words'),
            ('note_only', 'reply', note, 'expected 1-8 reply lines'),
            ('note_after_question', 'reply',
             'DECIDE: 1. Keep backups (default).\nDECIDE: Which option?\n' + note,
             'end with a DECIDE question'),
            ('warning_with_action', 'reply', warning + '\nDONE: Delete backups.',
             'a Warning: must stand alone'),
            ('long_warning', 'reply', 'Warning: ' + 'word ' * 12,
             'line 1 exceeds 12 words'),
            ('too_many_lines', 'reply', 'DONE: Pass tests.\n' * 9, 'expected 1-8 reply lines'),
            ('empty_baseline', 'baseline_reply', '', 'baseline_reply must not be empty'),
            ('invalid_label', 'reply', 'INVALID: Pass tests.', 'unknown block label'),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(source / 'skills/aot-brief', root / 'skills/aot-brief')
            target = root / 'tests/aot-brief'
            target.mkdir(parents=True)
            shutil.copy(source / 'tests/aot-brief/validate.py', target)
            original = (source / 'tests/aot-brief/samples.json').read_text()
            for mode in ([], ['-O']):
                for name, field, value, expected in cases:
                    with self.subTest(mode=mode, case=name):
                        samples = json.loads(original)
                        # Boundary fixtures test formatting, not compression performance.
                        if field == 'reply':
                            samples[0]['baseline_reply'] = 'Verbose baseline text. ' * 200
                        samples[0][field] = value
                        (target / 'samples.json').write_text(json.dumps(samples))
                        result = subprocess.run(
                            [sys.executable, *mode, str(target / 'validate.py')],
                            capture_output=True, text=True, check=False,
                        )
                        if expected is None:
                            self.assertEqual(result.returncode, 0, result.stderr)
                            self.assertIn('PASS:', result.stdout)
                            continue
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('FAIL: samples.json sample 1 (bug_fix)', result.stderr)
                        self.assertIn(expected, result.stderr)
                        self.assertNotIn('PASS:', result.stdout)
                        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
