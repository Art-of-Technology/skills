"""Validate synthetic reporting samples; measure output with cl100k_base.

Run: uv run --with pyyaml --with tiktoken python tests/aot-brief/validate.py
These fixtures demonstrate compression, not production compliance guarantees.
"""
import json
from pathlib import Path
import re

import tiktoken
import yaml

def require(condition, message):
    """Fail with actionable context, including when Python uses -O."""
    if not condition:
        raise SystemExit(f'FAIL: {message}')


ROOT = Path(__file__).resolve().parents[2]
skill = (ROOT / 'skills/aot-brief/SKILL.md').read_text()
front = yaml.safe_load(skill.split('---', 2)[1])
require(front['name'] == 'aot-brief', 'SKILL.md: name must be aot-brief')
require(front['metadata']['version'] == '0.2.0', 'SKILL.md: version must be 0.2.0')
require(len(front['description']) < 1024, 'SKILL.md: description must be under 1024 characters')
require(len(skill.splitlines()) < 120, 'SKILL.md: must contain fewer than 120 lines')
require('\u2014' not in skill, 'SKILL.md: em dashes are forbidden')
for trigger in ('brief', 'terse', 'short answer', 'status', 'what changed'):
    require(trigger in front['description'], f'SKILL.md: missing trigger {trigger!r}')
encoder = tiktoken.get_encoding('cl100k_base')
samples = json.loads((Path(__file__).parent / 'samples.json').read_text())
require(len(samples) == 3, 'samples.json: expected exactly three samples')
order = ['DONE', 'NEXT', 'BLOCKED', 'DECIDE']
before_total = after_total = 0
for index, sample in enumerate(samples, 1):
    context = f'samples.json sample {index} ({sample.get("name", "unnamed")})'
    reply = sample['reply']
    lines = reply.splitlines()
    notes = [line for line in lines if line.startswith('Note:')]
    warnings = [line for line in lines if line.startswith('Warning:')]
    require(len(notes) <= 1, f'{context}: allow at most one Note: line')
    if warnings:
        require(len(lines) == 1, f'{context}: a Warning: must stand alone; wait for yes')
    else:
        regular_lines = [line for line in lines if not line.startswith('Note:')]
        require(0 < len(regular_lines) <= 8,
                f'{context}: expected 1-8 reply lines excluding one optional Note:')
    for line_number, line in enumerate(lines, 1):
        require(len(line.split()) <= 12, f'{context}: line {line_number} exceeds 12 words')
    labels = [line.partition(':')[0] for line in lines
              if line.strip() and not line.startswith(('Note:', 'Warning:'))]
    require(labels or warnings, f'{context}: expected at least one block label')
    require(all(label in order for label in labels), f'{context}: unknown block label')
    require(labels == sorted(labels, key=order.index), f'{context}: blocks must follow {order}')
    decisions = [line for line in lines if line.startswith('DECIDE:')]
    if decisions:
        options = [line for line in decisions if re.match(r'DECIDE: \d+[.)] ', line)]
        require(1 <= len(options) <= 3, f'{context}: expected 1-3 numbered decision options')
        require(sum('(default)' in option for option in options) == 1,
                f'{context}: mark exactly one option (default)')
        require(sum(line.count('?') for line in lines) == 1,
                f'{context}: expected exactly one decision question')
        require(lines[-1].startswith('DECIDE:') and lines[-1].endswith('?'),
                f'{context}: end with a DECIDE question')
    before = len(encoder.encode(sample['baseline_reply']))
    after = len(encoder.encode(reply))
    require(before > 0, f'{context}: baseline_reply must not be empty')
    saving = 1 - after / before
    require(saving >= 0.30, f'{context}: token reduction {saving:.1%} is below 30%')
    before_total += before
    after_total += after
    print(f'{len(lines)} lines; {before} -> {after} tokens; {saving:.1%} fewer')
print(f'Total: {before_total} -> {after_total}; {1-after_total/before_total:.1%} fewer')
print('PASS: skill constraints and three synthetic response fixtures')
