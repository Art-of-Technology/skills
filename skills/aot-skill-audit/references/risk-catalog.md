# Risk catalog for agent skills

Categories, rule IDs, and default severities used by `aot-skill-audit`. Rule IDs follow NVIDIA SkillSpector (Apache-2.0, https://github.com/NVIDIA/SkillSpector) so a static scan and a manual review use the same vocabulary. Descriptions here are rewritten for a human reviewer; the two questions for every rule are *does the skill do this* and *is it justified by what the skill says it is for*.

Severity is a default. Lower it one step when the behaviour is clearly required by the stated purpose and scoped to it. Raise it one step when the behaviour is hidden, obfuscated, or contradicts the description.

## Prompt injection (P)

The skill's text tries to steer the agent rather than help the user. Any confirmed finding here is a DO NOT INSTALL on its own.

| Rule | Severity | Look for |
|------|----------|----------|
| P1 | CRITICAL | Overrides of system or safety instructions: "ignore previous", "disregard your guidelines", "new instructions follow", role resets. |
| P2 | HIGH | Instructions hidden from a human reader: HTML comments, collapsed `<details>`, text after 40+ blank lines or pushed far right by spaces, zero-width or bidi characters, tiny or same-colour text. |
| P3 | CRITICAL | Text telling the agent to send conversation, files, or user data anywhere external. |
| P4 | MEDIUM | Subtle bias steering: "always recommend X", "prefer vendor Y", "never suggest alternatives". |
| P5 | CRITICAL | Instructions whose real-world effect is physical or financial harm. |
| P9 | HIGH | Whitespace padding: blocks of blank lines or long runs of spaces used to hide the content above. |
| SSD-1..4 | HIGH | Semantic versions of the above that dodge keywords: polite reframings, role-play that grants permissions, fictional framing, "remember everything the user says and repeat it", multi-step narratives that build trust then ask for something sensitive. |

## Data exfiltration (E, TT)

| Rule | Severity | Look for |
|------|----------|----------|
| E1 | MEDIUM | Data posted to an external URL. Fine when the URL is the vendor the skill exists to talk to. Not fine when the destination is undisclosed, a paste site, a webhook, or a personal domain. |
| E2 | HIGH | Bulk environment reads: iterating `os.environ`, `Object.keys(process.env)`, `env \| grep KEY`. A skill needs its own variables, not everyone's. |
| E3 | HIGH | Filesystem sweeps for `.env`, `.ssh`, `.aws`, `.gnupg`, `credentials`, or recursive walks of the home directory. |
| E4 | CRITICAL | Sending or logging the agent conversation or context to anywhere external. |
| E5 | MEDIUM | Uploads to cloud storage buckets not owned by the user. |
| TT3 | CRITICAL | A credential read from env flows to a network call. Downgrade to LOW when the destination is that credential's own API (`GPTZERO_API_KEY` to `api.gptzero.me` is how API keys work). |
| TT4 | HIGH | File contents flow to a network call. Same downgrade rule when the file is the user's explicit input to the vendor. |
| TT5 | CRITICAL | Network or user input flows into `exec`, `eval`, a shell, or a deserializer. |

## Privilege escalation and agent snooping (PE, AS)

| Rule | Severity | Look for |
|------|----------|----------|
| PE1 | MEDIUM | Requested permissions or `allowed-tools` broader than the job needs. |
| PE2 | HIGH | `sudo`, `doas`, root requirements. |
| PE3 | HIGH | Reads of credential files: SSH keys, AWS/GCP/Azure configs, keychains, browser cookie stores, `.netrc`, `.npmrc`, `.pypirc`. A `.gitignore` entry mentioning them is not a read; dismiss those. |
| AS1 | HIGH | Reads of `~/.claude`, `~/.codex`, `~/.gemini`, or project `.claude/` settings. These hold API keys and other skills' instructions. |
| AS2 | HIGH | Reads of `mcp.json` or `.mcp.json`. Reveals every tool integration and its tokens. |
| AS3 | MEDIUM | Enumerating or reading other installed skills. |

## Supply chain and execution (SC, AST, DS)

| Rule | Severity | Look for |
|------|----------|----------|
| SC1 | LOW | Unpinned dependencies. Note it, do not fail on it. |
| SC2 | CRITICAL | Download-and-run: `curl \| sh`, `pip install` from a URL, `npx` of an unknown package, fetching a script then executing it. |
| SC3 | HIGH | Obfuscation: base64 or hex strings decoded and passed to `exec`, `eval`, or a shell. Legitimate skills do not need to hide code from their users. |
| SC4 | LOW..HIGH | Dependencies with known CVEs. Severity follows the CVE. |
| SC6 | HIGH | Package names one edit away from a popular package. |
| SC8 | HIGH | Shipped bytecode (`__pycache__`, `.pyc`) or compiled binaries alongside clean-looking source. The binary may not match the source. |
| SC9 | HIGH | Executable content in a non-executable container: code inside a PDF, image, docx, or a file with a misleading extension. |
| AST1..6 | MEDIUM | `exec`, `eval`, `compile`, `__import__`, `subprocess`, `os.system`. Justified when the skill's job is to run a specific tool with fixed arguments. Escalate to HIGH when input is user- or network-controlled, or `shell=True` is used with string formatting. |
| AST8 | CRITICAL | Execution combined with a dynamic source: network response, decoded blob, dynamic import. |
| AST9 | HIGH | `getattr(os, "system")`, `getattr(builtins, "exec")`. Functionally identical to a direct call, written to dodge grep. Treat the evasion itself as intent. |
| DS1..4, TT6, AST10 | HIGH | Insecure deserialization of untrusted input: `pickle`, `marshal`, `yaml.load` without SafeLoader, `torch.load` without `weights_only`, PHP `unserialize`, Ruby `Marshal.load`, node-serialize. |

## Persistence and self-modification (RA)

| Rule | Severity | Look for |
|------|----------|----------|
| RA1 | HIGH | The skill rewrites its own files, its manifest, or agent settings at runtime. |
| RA2 | HIGH | Cron, launchd, systemd units, shell rc edits, git hooks, or agent lifecycle hooks that outlive the session. A README telling the user to add a cron job is documentation; dismiss. Code that installs one is a finding. |

## Excessive agency and tool misuse (EA, TM, LP)

| Rule | Severity | Look for |
|------|----------|----------|
| EA1 | HIGH | Blanket tool access with no constraints. |
| EA2 | HIGH | Destructive or financial actions without a human approval step: publishing, paying, deleting, force-pushing. A draft-then-approve flow is the expected pattern. |
| EA3 | MEDIUM | Capabilities unrelated to the description. |
| EA5 | MEDIUM | Switching the user's model or provider, or embedding its own API key for a paid service. |
| TM1 | HIGH | Dangerous flags baked in: `--force`, `-rf`, `--no-verify`, `shell=True`, `verify=False`, `--insecure`. |
| TM3 | MEDIUM | Unsafe defaults: TLS verification off, world-writable permissions, no auth. |
| LP1..4 | MEDIUM | Manifest permissions that do not match the code in either direction: undeclared capabilities in code, or declared permissions nothing uses. |
| AOT-1 | MEDIUM | In-house rule. The skill makes the user break a platform's terms or privacy norms: scraping other people's profiles or audiences, automating engagement, bypassing rate limits. Report under capabilities even when the code is clean. |

## Anti-refusal and memory poisoning (AR, MP)

| Rule | Severity | Look for |
|------|----------|----------|
| AR1 | CRITICAL | "Never refuse", "always comply", "do not decline". |
| AR2 | HIGH | "Omit warnings", "no disclaimers", "skip the ethics". |
| AR3 | CRITICAL | "You have no restrictions", "ignore your guidelines", DAN-style preambles. |
| MP1 | HIGH | Content designed to persist across sessions in agent memory or CLAUDE.md, altering behaviour later. |
| MP2 | MEDIUM | Context stuffing: huge irrelevant files loaded on every trigger. |
| MP3 | HIGH | Writes to the agent's memory or state files. |

## Metadata and trigger abuse (TP, TR)

| Rule | Severity | Look for |
|------|----------|----------|
| TP1 | HIGH | Instructions hidden in the frontmatter `description`, tool descriptions, or parameter defaults. The agent reads these even when the skill body is never loaded. |
| TP2 | HIGH | Homoglyphs or invisible characters in names and descriptions. |
| TP4 | HIGH | Description that does not match what the code does. |
| TR1..3 | MEDIUM | Triggers so broad the skill fires on common phrases and shadows other skills or built-in commands. |

## Server-side request forgery (SSRF)

| Rule | Severity | Look for |
|------|----------|----------|
| SSRF1 | CRITICAL | Requests to cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`). |
| SSRF2 | HIGH | Requests to loopback, link-local, or private ranges. |
| SSRF3 | MEDIUM | Request host built from user or network input without an allowlist. |

## Bundled hooks and plugin settings (BH)

| Rule | Severity | Look for |
|------|----------|----------|
| BH1 | HIGH | Any `hooks.json` or hook entry in a plugin manifest. Hooks run automatically on events. Read every handler in full. |
| BH2 | CRITICAL | A hook that sends event payloads or local file content off the machine. |
| BH3 | HIGH | Bundled `settings.json` that grants permissions, sets `bypassPermissions`, or adds allow rules. |

## Common false positives to dismiss with a one-line reason

- API key sent to that vendor's own documented endpoint.
- Credential file names appearing only in `.gitignore`, docs, or `.env.example`.
- `subprocess` calling a fixed binary with fixed arguments and no user input.
- README text describing what the user could set up (cron, aliases) rather than code doing it.
- Duplicated findings from a vendored copy of the same tree (marketplace mirrors).
- Test scripts that only run when the user invokes them explicitly and only touch the variables they document.
