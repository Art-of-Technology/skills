---
name: aot-nextjs-server-first
description: Audit and refactor a Next.js app so data fetching happens on the server, backend credentials never reach the browser, and client-side fetch waterfalls stop causing UI flicker. Use this skill whenever the user asks to "make requests server side", "hide the API payload", "proxy API calls", "stop the UI flickering", "remove client-side fetching", "move this to RSC", "add a BFF", "run aot-nextjs-server-first", or complains about loading spinners, layout shift, waterfalls, double renders, or a backend URL and token visible in DevTools or the JS bundle. Also trigger when reviewing NEXT_PUBLIC_ environment variables, useEffect fetch calls, route handlers, server actions, App Router data flow, TanStack Query setup, caching and revalidation strategy, or multi-tenant scoping in a Next.js frontend. Even if the user does not say "audit", use this skill when they want Next.js data access reviewed or moved behind the server.
---

# aot-nextjs-server-first

Move a Next.js app to a server-first data model. Find every browser-originated call to the backend, route reads through React Server Components, route interactive traffic through a thin BFF layer, keep credentials server side, and remove the fetch waterfalls that cause flicker. Report first. Refactor only after the user confirms.

Two goals sit behind this work, and they are separate. Keep them separate in the report.

1. Correctness and secrecy. Backend base URLs, service tokens, and internal field shapes stay on the server. A leaked token is exploitable by anyone.
2. Perceived performance. Server-rendered first paint with streamed suspense boundaries removes the mount-spinner-fetch-shift sequence.

## Do not confuse hiding with authorization

State this in the report when the user's stated goal is hiding payloads. An authenticated user reads whatever their session grants, DevTools open or not. Proxying does not change the authorization surface. The controls that matter are DTO shaping, field-level allow lists, and tenant scoping enforced in the query. Treat any finding of the form "sensitive field visible in response" as an authorization or DTO finding, not a transport finding.

## What you produce

A single report:

- Summary: Next.js version, router mode, data libraries detected, counts by severity.
- Findings table: ID, severity, category, `file:line`, one-line issue, one-line fix.
- Per-finding detail with a migration snippet in the codebase's idiom.
- A data flow map: which routes render on the server, which components fetch on the client, and where the backend token is read.
- A migration plan ordered by severity and blast radius.

## Scope before scanning

Infer these. Confirm only what you cannot.

1. Target. Repo root, an app inside a monorepo, or a diff. Default to the working tree.
2. Mode. Report-only, or report then refactor. Default to report-only.
3. Backend topology. Same-process API routes, a separate internal API on a private network, or a third-party API. This decides whether a BFF proxy is needed at all. A same-origin API with cookie auth needs far less proxying than a separate service holding a service token.

## Step 1: Detect the setup

```bash
cat package.json 2>/dev/null | grep -E '"(next|react|@tanstack/react-query|swr|axios|ky|@trpc/client)"'
ls -d app src/app pages src/pages 2>/dev/null
ls next.config.* middleware.* 2>/dev/null
grep -rn "NEXT_PUBLIC_" --include='*.ts' --include='*.tsx' --include='*.env*' . 2>/dev/null | head -50
```

Record router mode. App Router with RSC is the target architecture. Pages Router work routes through `getServerSideProps` and API routes instead; the checklist still applies but the idioms differ. Read `references/app-router.md` for App Router, `references/pages-router.md` for Pages Router.

## Step 2: Scan for browser-originated backend access

```bash
# fetch inside effects: the main flicker source
grep -rn -A6 "useEffect(" --include='*.tsx' --include='*.ts' . 2>/dev/null | grep -nE "fetch\(|axios\.|\.get\(|\.post\(" | head -50

# client components doing network work
grep -rln "'use client'" --include='*.tsx' . 2>/dev/null | xargs grep -ln "fetch(\|axios\|ky(" 2>/dev/null

# backend base URLs and tokens exposed to the bundle
grep -rn "NEXT_PUBLIC_.*\(API\|URL\|TOKEN\|KEY\|SECRET\)" --include='*.ts' --include='*.tsx' . 2>/dev/null

# absolute backend hosts hardcoded in components
grep -rnE "https?://[a-zA-Z0-9.-]+" --include='*.tsx' . 2>/dev/null | grep -v "schema.org\|w3.org" | head -30

# route handlers and server actions already present
ls app/api 2>/dev/null; grep -rln "'use server'" --include='*.ts' --include='*.tsx' . 2>/dev/null
```

Then confirm empirically where possible. If the app builds, grep the client chunks for the backend host and any token-shaped string. A hit in `.next/static` is a 🔴 with proof.

```bash
grep -rl "$(echo BACKEND_HOST_HERE)" .next/static 2>/dev/null | head
```

## Step 3: Review against the checklist

Order reflects impact on a multi-tenant CRM handling PII.

1. Credentials in the bundle. Service tokens, API keys, internal hosts, or basic-auth strings reachable from client code or `NEXT_PUBLIC_*`. Any hit is 🔴.
2. Tenant and ownership scoping. Every server-side read derives tenant and user from the session on the server. Never from a client-supplied `orgId`, header, or query param. A route handler that forwards a client-supplied tenant id is 🔴.
3. Route handler as open proxy. A catch-all handler forwarding arbitrary paths, methods, or upstream URLs from the client is 🔴. Proxies expose an allow list of operations, not a tunnel.
4. Initial reads on the client. Above-the-fold data fetched in `useEffect` or a client query hook instead of the server component. Causes flicker and an extra round trip. 🟠.
5. Fetch waterfalls. Sequential dependent fetches, parent fetch then child fetch on mount. Parallelise on the server, or colocate per-component fetches inside suspense boundaries. 🟠.
6. Missing suspense boundaries and streaming. No `loading.tsx`, no `Suspense` around slow segments, so the whole route blocks or the whole route blinks. 🟠.
7. Layout shift from unreserved space. Skeletons that do not match final dimensions, images without dimensions, lists that grow after hydration. 🟠.
8. Mutations from the client to the backend directly. Writes should go through server actions or a BFF route handler so the token stays server side and revalidation is controlled. 🟠.
9. DTO shaping. Server passes raw upstream entities into client components. Internal fields, cost prices, notes, soft-delete flags, and audit columns cross the boundary. Map to explicit DTOs at the server edge. 🟠.
10. Serialization weight. Large payloads serialized into the RSC stream or into client props when the client needs three fields. Slows first paint. 🟡.
11. Caching and revalidation. Every server fetch declares intent: `cache`, `next.revalidate`, or `no-store`. Unintentional caching of per-user data is a correctness and privacy bug, not a perf nit. Per-user data cached across requests is 🔴.
12. Client cache still available where needed. Search-as-you-type, infinite lists, and optimistic updates need a client cache. Removing TanStack Query wholesale to satisfy a server-first rule makes the UX worse. Flag over-migration as a 🟡 finding against the plan, not against the code.
13. Auth propagation. Session cookie read server side, forwarded upstream as a service token plus asserted user identity. No token minted in the browser.
14. Error and empty states. Server errors surface through `error.tsx` and typed action results, not silent empty arrays that look like no data.
15. Middleware weight. Auth checks in middleware are cheap only if they avoid network calls per request. Flag per-request upstream calls in middleware. 🟡.
16. Request deduplication. Same upstream call issued by multiple server components in one render without dedupe or cache.

Record `file:line`, the concrete effect, and the fix in the codebase's idiom.

## Step 4: Choose the target architecture per data path

Do not apply one rule to every call. Classify each data path and record the classification in the report.

- Initial page reads. Server component calls the upstream directly over the private network with a service token. Never through the browser.
- Mutations. Server actions. Return typed results. Revalidate the affected tags or paths.
- Interactive reads, meaning typeahead, filters, pagination, polling. Thin BFF route handlers under `app/api/bff/*`. Session cookie in, DTO out, tenant scope enforced server side. Client keeps its cache.
- Third-party keyed APIs. Always proxied. No exceptions.
- Public static content. Fetch on the server at build or with a revalidate window.

Two rules to state plainly in the report: zero fetch calls inside `useEffect`, and no `NEXT_PUBLIC_*` beyond genuinely public identifiers such as an analytics site id.

Read `references/bff-proxy.md` before writing any proxy or server action code.

## Step 5: Triage

- 🔴 Critical. Credential or internal host in the bundle. Client-supplied tenant id trusted server side. Open proxy. Per-user data cached across requests.
- 🟠 High. Client-side initial reads, waterfalls, direct client writes to the backend, raw entities crossing the client boundary.
- 🟡 Medium. Caching intent unset, oversized payloads, missing skeleton dimensions, per-request middleware calls.
- 🔵 Low. Naming, colocation, and structural cleanups.

Read the real code before scoring. A `NEXT_PUBLIC_` variable holding a public Stripe publishable key is not a finding. Say so under "Reviewed, not a risk".

## Step 6: Report

Use this exact structure.

```markdown
# Next.js Server-First Audit: <target>

**Next:** <version> | **Router:** app | pages | **Data libs:** <detected>
**Scope:** <paths> | **Date:** <date>
**Risk summary:** 🔴 N  🟠 N  🟡 N  🔵 N

## Data flow map
| Route / component | Current fetch site | Credential location | Target |
|---|---|---|---|
| /contacts | client useEffect | NEXT_PUBLIC_API_TOKEN | RSC + service token |

## Findings
| ID | Sev | Category | Location | Issue | Fix |
|----|-----|----------|----------|-------|-----|
| 1 | 🔴 | Credential exposure | lib/api.ts:8 | Service token read from NEXT_PUBLIC_API_TOKEN in client module | Move to server-only module, proxy via route handler |

## Detail
### 1. 🔴 Service token in client bundle
**Location:** lib/api.ts:8
**Effect:** Anyone reading the JS bundle calls the backend as the service account.
**Fix:**
\`\`\`ts
// before, imported by a client component
const token = process.env.NEXT_PUBLIC_API_TOKEN
// after: server-only module
import 'server-only'
const token = process.env.API_TOKEN
\`\`\`

## Flicker analysis
- <route>: N sequential client fetches on mount, no suspense boundary, skeleton height mismatch of Npx.

## Migration plan
1. <highest severity, smallest blast radius first>
```

Stop here in report-only mode.

## Step 7: Refactor loop (only after confirmation)

Migrate one route at a time, top of the plan first. Never a whole-app rewrite in one pass.

1. Create the server-only client module with `import 'server-only'` and the token from a non-public env var.
2. Move the route's initial read into the server component. Delete the effect. Add a suspense boundary with a skeleton matching final dimensions.
3. Convert writes to server actions. Add revalidation.
4. Add BFF handlers only for genuinely interactive reads. Session in, DTO out, tenant scope in the query.
5. Verify: rebuild, grep `.next/static` for the backend host and token, load the route with JS throttled and confirm no post-hydration content swap.
6. Screenshot before and after if a browser is available. Flicker claims need evidence.
7. If an open PR exists, hand the commit and review cycle to `aot-pr-loop`.

## Hard rules

- Never commit or push without explicit confirmation.
- Never build a catch-all proxy that forwards client-chosen upstream paths or URLs.
- Never trust a tenant or user id from the client, including in a route handler.
- Declare caching intent on every server fetch. Per-user data is `no-store` or user-tagged.
- Keep the client cache where interactivity depends on it. Server-first is a default, not a ban.
- Read the matching reference file before writing migration code.
- Migrate route by route with verification between steps.

## Reference files

- `references/app-router.md` — RSC data access, suspense and streaming layout, server actions, revalidation tags, `server-only`, DTO mapping at the edge.
- `references/bff-proxy.md` — Route handler proxy pattern, allow-listed operations, session to service-token exchange, TanStack Query against the BFF, tenant scoping.
- `references/pages-router.md` — `getServerSideProps` equivalents, API route proxying, incremental migration path to App Router.
