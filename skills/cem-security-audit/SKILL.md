---
name: cem-security-audit
description: Run a security audit on a TypeScript/Node.js or C#/ASP.NET Core codebase and produce a prioritized findings report with concrete fixes. Use this skill whenever the user asks to "run a security audit", "security review", "audit my code", "check for vulnerabilities", "review this for security", "pentest my app", "run cem-security-audit", or mentions OWASP, IDOR, broken access control, XSS, CSRF, SSRF, SQL injection, secrets leaking, mass assignment, or insecure file upload. Also trigger when reviewing authentication, authorization, multi-tenant data isolation, JWT handling, payment or PSP integration security, webhook handling, or dependency vulnerabilities before shipping. Covers Express, Fastify, NestJS, Next.js, Prisma, ASP.NET Core, EF Core, and Dapper. Even if the user does not say the word "audit", use this skill when they want code checked for security issues.
---

# cem-security-audit

Audit a web codebase for security defects and return a prioritized, fixable report. Detect the stack, run the scanners, review the code against a focused checklist, triage by severity, then report. Apply fixes only after the user confirms.

This skill targets your stack: TypeScript/Node.js (Express, Fastify, NestJS, Next.js, Prisma, BullMQ) and C#/ASP.NET Core (EF Core, Dapper). Stack-specific remediation idioms live in the reference files. Read the one that matches before writing any fix.

## What you produce

The deliverable is a single report. Build everything toward it:

- A summary: stack detected, scope scanned, finding counts by severity, top risks.
- A findings table: ID, severity icon, category, `file:line`, one-line issue, one-line fix.
- Per-finding detail with a remediation snippet in the codebase's own idiom.
- Scanner output summary: dependency vulnerabilities, SAST hits, secret hits.
- A remediation plan ordered by severity.

## Scope before scanning

Determine three things from context. Confirm only what you cannot infer.

1. Target. The repo root, a service inside a monorepo, or a diff. Default to the current working tree.
2. Mode. Report-only, or report then fix. Default to report-only. Never commit changes without explicit confirmation.
3. Depth. Fast (scanners plus high-severity manual review) or full (every checklist item). Default to full for money or PII handling code, fast otherwise.

If the user has an open PR and wants fixes applied, hand the fix phase to `cem-pr-loop` rather than committing directly here.

## Step 1: Detect the stack

```bash
# Node / TypeScript
ls package.json tsconfig.json 2>/dev/null
cat package.json 2>/dev/null | grep -E '"(express|fastify|@nestjs/core|next|prisma|@prisma/client|bullmq|jsonwebtoken|jose)"'

# .NET
ls *.sln **/*.csproj 2>/dev/null
grep -rEl 'Microsoft.AspNetCore|EntityFrameworkCore|Dapper' --include=*.csproj . 2>/dev/null
```

Route to the matching reference file before remediation:

- Node/TypeScript: read `references/nodejs-typescript.md`.
- C#/.NET: read `references/dotnet.md`.
- Both present (monorepo or polyglot): read both.

## Step 2: Run the automated scanners

Run what is installed. Note any tool the environment lacks so the user can add it. Do not fail the audit because one scanner is missing; manual review still applies.

Secrets, all stacks:

```bash
gitleaks detect --no-banner --redact -v 2>/dev/null || echo "gitleaks not installed"
# fallback
git grep -nE '(secret|password|api[_-]?key|token|private[_-]?key)\s*[:=]' -- . 2>/dev/null | head -50
```

SAST, all stacks:

```bash
semgrep --config auto --error --quiet 2>/dev/null || echo "semgrep not installed"
```

Node/TypeScript:

```bash
npm audit --omit=dev --audit-level=high 2>/dev/null || true
npx --yes retire --severity high 2>/dev/null || true
# if eslint-plugin-security is present
npx --yes eslint . --no-eslintrc --plugin security --rule '{"security/detect-eval-with-expression":"error"}' 2>/dev/null || true
```

.NET:

```bash
dotnet list package --vulnerable --include-transitive 2>/dev/null || true
dotnet list package --deprecated 2>/dev/null || true
```

Capture counts. Vulnerable dependencies with a known exploit are 🔴 by default.

## Step 3: Manual review against the checklist

Scanners miss logic flaws. Walk the checklist below. Order reflects impact on a multi-tenant platform that handles money and PII, so start at the top.

1. Access control and tenant isolation. Every read and write checks ownership at the data layer, not the route. No user reads or mutates another user's or org's rows. IDs are non-guessable or ownership-checked. No IDOR. This is the highest-value class for your platforms.
2. Authentication and session. JWT algorithm pinned on verify, `alg: none` rejected, `exp` enforced, secret is 256-bit random. Tokens in httpOnly Secure SameSite cookies, not localStorage. Session invalidation on logout, role change, and account removal.
3. Injection. SQL through parameterized queries or safe ORM methods. Flag raw query builders fed user input (`$queryRawUnsafe`, `FromSqlRaw`, string-concatenated Dapper). Command injection in any shell-out. NoSQL operator injection.
4. Secrets exposure. No secrets in client bundles, `NEXT_PUBLIC_*`, source maps, hidden fields, or logs. Server-side only for keys.
5. SSRF. Any server-side fetch of a user-influenced URL validates scheme, resolves DNS, blocks private and cloud-metadata ranges, and limits redirects. Webhooks, URL previews, PSP callbacks, and media fetchers all qualify.
6. Mass assignment. Writes whitelist fields. No spreading raw request bodies into `update`. Role and balance fields never client-settable.
7. Input validation. Server-side schema validation on every boundary (HTTP body, query, params, queue job payloads, webhook bodies). Reject unknown fields.
8. Output encoding and XSS. Framework escaping left on. No `dangerouslySetInnerHTML` or `Html.Raw` with user data without sanitization. SVG uploads treated as active content.
9. CSRF. State-changing cookie-authenticated endpoints carry CSRF protection plus SameSite. Pure bearer-token APIs are exempt; confirm the auth model first.
10. File upload. Type by magic bytes not extension, size capped server-side, random stored names, served from a separate origin with `Content-Disposition: attachment` and `nosniff`.
11. Path traversal. User input never lands in a file path without canonicalize-and-confine.
12. XXE. XML parsers disable DTD and external entities. Applies to SOAP, SAML, and Office or SVG uploads.
13. Security headers. HSTS, CSP without `unsafe-inline` scripts, `nosniff`, frame denial, referrer policy.
14. Rate limiting and abuse. Auth, password reset, payment, and bonus or promo endpoints are rate-limited and abuse-aware. Relevant to fraud and bonus abuse on gambling platforms.
15. Logging and PII. Logs redact secrets, tokens, full card numbers, and PII. Check the Pino or logger config for redaction paths.
16. Crypto. Passwords use Argon2id, bcrypt, or scrypt. No MD5, SHA1, or bare SHA256 for passwords. Strong randomness for tokens.
17. Error handling. No stack traces or SQL errors to clients in production.

For each hit, record `file:line`, the concrete risk, and the fix in the codebase's idiom from the reference file.

## Step 4: Triage findings

Assign severity. Read the real code before scoring; scanners and pattern matches produce false positives.

- 🔴 Critical. Exploitable now with direct impact: auth bypass, IDOR on money or PII, injection, exposed live secret, SSRF to metadata.
- 🟠 High. Strong risk needing a plausible precondition: missing CSRF on a sensitive action, weak JWT config, unsafe file upload.
- 🟡 Medium. Defense-in-depth gap: missing security header, broad CORS, verbose errors.
- 🔵 Low or info. Hardening note or stylistic risk.

False positive: drop it from the report or list it under a short "Reviewed, not a risk" note with the reason.

## Step 5: Report

Use this exact structure.

```markdown
# Security Audit: <target>

**Stack:** <detected stack> | **Scope:** <paths or diff> | **Date:** <date>
**Risk summary:** 🔴 N  🟠 N  🟡 N  🔵 N

## Findings

| ID | Sev | Category | Location | Issue | Fix |
|----|-----|----------|----------|-------|-----|
| 1  | 🔴  | Access control | src/orders/get.ts:42 | Order fetched by id with no ownership check | Filter by userId at query |

## Detail

### 1. 🔴 Missing ownership check on order fetch
**Location:** src/orders/get.ts:42
**Risk:** Any authenticated user reads any order by guessing the id. Direct PII and financial exposure.
**Fix:**
\`\`\`ts
// before
const order = await prisma.order.findUnique({ where: { id } })
// after
const order = await prisma.order.findFirst({ where: { id, userId: ctx.user.id } })
\`\`\`

## Scanner output
- Dependencies: <N high/critical from npm audit or dotnet vulnerable>
- SAST: <N semgrep findings, top rules>
- Secrets: <N gitleaks hits>

## Remediation plan
1. <highest-severity fix first>
2. ...
```

Present the report. Stop here in report-only mode.

## Step 6: Fix loop (only if mode is fix and user confirms)

1. Show the findings table and proposed action per row. Wait for confirmation.
2. Apply the smallest change that closes each finding. No unrelated refactors.
3. Re-run the relevant scanner to confirm the fix and check for regressions.
4. If an open PR exists, switch to `cem-pr-loop` to commit, respond to review threads, and drive the quality gate. Otherwise commit per the user's normal flow with a message listing each fix.

## Severity drives action, not blind application

A wrong fix from a misread finding is worse than the finding. Confirm the issue maps to the real code state before changing anything. When a finding depends on context you cannot see (deployment, gateway, WAF), state the assumption in the report rather than guessing.

## Hard rules

- Never commit or push without explicit confirmation.
- Never weaken a control to make a test pass.
- Read the matching reference file before writing a fix.
- Report-only by default. Fixing is opt-in.
- Surface every 🔴 to the user. Never drop one silently.
- Mark false positives with a reason. Do not pad the report.
- Prefer the codebase's existing libraries and idioms over introducing new dependencies.

## Reference files

- `references/nodejs-typescript.md` — Express, Fastify, NestJS, Next.js, Prisma, BullMQ, JWT, Pino. Vulnerable-vs-secure snippets per checklist item.
- `references/dotnet.md` — ASP.NET Core, EF Core, Dapper, model binding, antiforgery, JWT validation, headers middleware. Vulnerable-vs-secure snippets per checklist item.
