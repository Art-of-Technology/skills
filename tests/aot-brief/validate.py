"""Validate synthetic reporting samples; measure output with cl100k_base.

Run: uv run --with pyyaml --with tiktoken python tests/aot-brief/validate.py
These fixtures demonstrate compression, not production compliance guarantees.
"""
import json
from pathlib import Path
import re

import tiktoken
import yaml

ROOT = Path(__file__).resolve().parents[2]
skill = (ROOT / 'skills/aot-brief/SKILL.md').read_text()
front = yaml.safe_load(skill.split('---', 2)[1])
assert front['name'] == 'aot-brief'
assert front['metadata']['version'] == '0.2.0'
assert len(front['description']) < 1024
assert len(skill.splitlines()) < 120
assert '\u2014' not in skill
for trigger in ('brief', 'terse', 'short answer', 'status', 'what changed'):
    assert trigger in front['description']
encoder = tiktoken.get_encoding('cl100k_base')
samples = json.loads((Path(__file__).parent / 'samples.json').read_text())
assert len(samples) == 3
order = ['DONE', 'NEXT', 'BLOCKED', 'DECIDE']
before_total = after_total = 0
for sample in samples:
    reply = sample['reply']
    lines = reply.splitlines()
    assert 0 < len(lines) <= 8
    assert all(len(line.split()) <= 12 for line in lines)
    labels = [line.partition(':')[0] for line in lines]
    assert all(label in order for label in labels)
    assert labels == sorted(labels, key=order.index)
    decisions = [line for line in lines if line.startswith('DECIDE:')]
    if decisions:
        options = [line for line in decisions if re.match(r'DECIDE: \d+[.)] ', line)]
        assert 1 <= len(options) <= 3
        assert sum('(default)' in option for option in options) == 1
        assert sum('?' in line for line in lines) == 1
        assert lines[-1].startswith('DECIDE:') and lines[-1].endswith('?')
    before = len(encoder.encode(sample['baseline_reply']))
    after = len(encoder.encode(reply))
    saving = 1 - after / before
    assert saving >= 0.30, (sample['task'], saving)
    before_total += before
    after_total += after
    print(f'{len(lines)} lines; {before} -> {after} tokens; {saving:.1%} fewer')
print(f'Total: {before_total} -> {after_total}; {1-after_total/before_total:.1%} fewer')
print('PASS: skill constraints and three synthetic response fixtures')
