# Response samples

Run from the repository root:

```sh
uv run --with pyyaml --with tiktoken python tests/aot-brief/validate.py
```

An independent agent read the skill and generated three synthetic reporting
fixtures: a completed bug fix, a refactor across three files, and a decision.
No application changes or application test runs are implied by these fixtures.
The baselines and compressed replies describe the same supplied facts.

Measured with `tiktoken`'s `cl100k_base` tokenizer:

| Sample | Baseline tokens | Brief tokens | Reduction | Lines |
|---|---:|---:|---:|---:|
| Bug fix | 70 | 47 | 32.9% | 5 |
| Three-file refactor | 79 | 54 | 31.6% | 6 |
| Decision | 59 | 41 | 30.5% | 3 |
| Total | 208 | 142 | 31.7% | |

The validator checks structure, caps, decision formatting, skill metadata,
and token reduction. Fact preservation was manually reviewed. These small,
agent-authored fixtures are demonstrations, not a held-out benchmark or proof
of reliable compliance across models. Production savings require paired real
replies and the deployed model's tokenizer. Reasoning tokens are excluded.

Assessment: stable labels and short lines make results easier to scan.
Rigid caps can displace useful explanations into files and repeat label tokens.
The exceptions and explicit uncertainty rule preserve important context.
