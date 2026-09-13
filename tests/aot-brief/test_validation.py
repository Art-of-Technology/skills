"""Exercise rejected fixtures in isolated copies, with and without optimization.

Run: uv run --with pyyaml --with tiktoken python tests/aot-brief/test_validation.py
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class ValidationFailures(unittest.TestCase):
    def test_invalid_samples_fail_in_both_modes(self):
        source = Path(__file__).resolve().parents[2]
        cases = (
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
                        samples[0][field] = value
                        (target / 'samples.json').write_text(json.dumps(samples))
                        result = subprocess.run(
                            [sys.executable, *mode, str(target / 'validate.py')],
                            capture_output=True, text=True, check=False,
                        )
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn('FAIL: samples.json sample 1 (bug_fix)', result.stderr)
                        self.assertIn(expected, result.stderr)
                        self.assertNotIn('PASS:', result.stdout)
                        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
