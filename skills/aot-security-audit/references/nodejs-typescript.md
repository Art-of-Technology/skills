# Node / TypeScript remediation idioms

Vulnerable-vs-secure patterns for Express, Fastify, NestJS, Next.js, Prisma, BullMQ, JWT, and Pino. Match the fix to the framework already in the codebase. Do not introduce a new framework to fix a finding.

## 1. Access control and tenant isolation

Scope every query by the authenticated principal at the data layer.

```ts
// VULNERABLE: ownership never checked
const order = await prisma.order.findUnique({ where: { id } })

// SECURE: ownership in the query
const order = await prisma.order.findFirst({ where: { id, userId: ctx.user.id } })
if (!order) throw new NotFoundException() // 404, not 403, to avoid enumeration

// Multi-tenant: filter by org on every call
const rows = await prisma.invoice.findMany({ where: { orgId: ctx.user.orgId } })
```

NestJS: enforce with a guard plus a resource check, not the route alone.

```ts
@UseGuards(JwtAuthGuard)
@Get(':id')
async get(@Param('id') id: string, @Req() req) {
  const doc = await this.svc.findOwned(id, req.user.id) // ownership inside the service
  if (!doc) throw new NotFoundException()
  return doc
}
```

## 2. Authentication and JWT

Pin the algorithm on verify. Never trust the token header. Store in cookies, not localStorage.

```ts
import jwt from 'jsonwebtoken'

// SIGN
const token = jwt.sign(
  { sub: userId, jti: crypto.randomUUID() },
  process.env.JWT_SECRET!,            // 256-bit random, not a phrase
  { algorithm: 'HS256', expiresIn: '15m' }
)

// VERIFY: whitelist the algorithm, reject 'none'
const decoded = jwt.verify(token, process.env.JWT_SECRET!, { algorithms: ['HS256'] })

// SEND
res.cookie('token', token, { httpOnly: true, secure: true, sameSite: 'strict' })
```

Invalidate on logout, role change, and account removal via a short TTL plus a revocation list (a Redis set of revoked `jti` works with your stack).

## 3. Injection

Prisma is safe by default. The risk is the raw escape hatch.

```ts
// VULNERABLE: string interpolation into raw SQL
await prisma.$queryRawUnsafe(`SELECT * FROM "User" WHERE email = '${email}'`)

// SECURE: tagged template parameterizes
await prisma.$queryRaw`SELECT * FROM "User" WHERE email = ${email}`
```

Command execution: never pass user input to a shell.

```ts
// VULNERABLE
exec(`convert ${userPath} out.png`)
// SECURE: no shell, args array
execFile('convert', [userPath, 'out.png'])
```

## 4. Secrets exposure

```ts
// VULNERABLE: bundled to the client in Next.js
export const STRIPE_SECRET = process.env.NEXT_PUBLIC_STRIPE_SECRET // shipped to browser

// SECURE: server-only, no NEXT_PUBLIC_ prefix, read in a server context
const stripe = new Stripe(process.env.STRIPE_SECRET!) // route handler or server action
```

Check committed `.env`, source maps in production, and any secret read in a `'use client'` file.

## 5. SSRF

Guard every server-side fetch of a user-influenced URL. Relevant to webhooks, URL previews, PSP callbacks, and media fetchers.

```ts
import dns from 'node:dns/promises'
import net from 'node:net'

const BLOCKED = [/^127\./, /^10\./, /^192\.168\./, /^169\.254\./, /^::1$/, /^fc00:/i]

async function assertSafeUrl(raw: string) {
  const u = new URL(raw)
  if (!['http:', 'https:'].includes(u.protocol)) throw new Error('scheme')
  const { address } = await dns.lookup(u.hostname)
  if (net.isIP(address) === 0) throw new Error('resolve')
  if (BLOCKED.some(r => r.test(address))) throw new Error('private range')
  return address // pin this IP for the request; do not re-resolve
}
```

Disable or validate redirects on the fetch client. Block `169.254.169.254` explicitly for cloud metadata.

## 6. Mass assignment

```ts
// VULNERABLE: client can set role or balance
await prisma.user.update({ where: { id }, data: req.body })

// SECURE: whitelist
const data = { name: req.body.name, avatar: req.body.avatar }
await prisma.user.update({ where: { id }, data })
```

## 7. Input validation with Zod

Validate every boundary, including queue jobs and webhook bodies. Reject unknown keys.

```ts
const Body = z.object({ name: z.string().min(1), email: z.string().email() }).strict()
const parsed = Body.parse(req.body) // throws on unknown or invalid

// BullMQ: validate job data on the consumer, never trust the payload
worker.process(async job => {
  const data = JobSchema.parse(job.data)
})
```

## 8. XSS

```tsx
// VULNERABLE
<div dangerouslySetInnerHTML={{ __html: comment }} />
// SECURE: render as text, or sanitize first
import DOMPurify from 'isomorphic-dompurify'
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(comment) }} />
```

Treat uploaded SVG as active content. Serve from a separate origin or sanitize.

## 9. CSRF

Needed for cookie-authenticated state changes. Pure bearer-token APIs do not need it; confirm the auth model first.

```ts
// Fastify
import csrf from '@fastify/csrf-protection'
app.register(csrf, { cookieOpts: { sameSite: 'strict', secure: true } })

// Express
import { doubleCsrf } from 'csrf-csrf'
const { doubleCsrfProtection } = doubleCsrf({ getSecret: () => process.env.CSRF_SECRET! })
app.use(doubleCsrfProtection)
```

## 10. File upload

```ts
import { fileTypeFromBuffer } from 'file-type'

const ALLOWED = new Set(['image/jpeg', 'image/png'])
const type = await fileTypeFromBuffer(buffer) // magic bytes, not extension
if (!type || !ALLOWED.has(type.mime)) throw new Error('type')
if (buffer.length > 5 * 1024 * 1024) throw new Error('size')
const name = `${crypto.randomUUID()}.${type.ext}` // discard original name
// store outside webroot, serve with Content-Disposition: attachment and nosniff
```

## 11. Path traversal

```ts
import path from 'node:path'

function safeJoin(base: string, userPath: string) {
  const target = path.resolve(base, userPath)
  if (!target.startsWith(path.resolve(base) + path.sep)) throw new Error('traversal')
  return target
}
```

## 12. Security headers with Helmet

```ts
import helmet from 'helmet'
app.use(helmet({
  contentSecurityPolicy: {
    directives: { defaultSrc: ["'self'"], scriptSrc: ["'self'"], frameAncestors: ["'none'"] }
  },
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true }
}))
// Fastify: @fastify/helmet with the same options
```

## 13. Rate limiting and abuse

```ts
// Fastify
import rateLimit from '@fastify/rate-limit'
app.register(rateLimit, { max: 5, timeWindow: '1 minute' }) // tighten on /auth, /password-reset, /payout
```

For gambling flows, rate-limit bonus and promo claims and add per-user and per-IP abuse checks.

## 14. Logging and PII with Pino

Redact secrets, tokens, card numbers, and PII. Audit the logger config.

```ts
const logger = pino({
  redact: {
    paths: ['req.headers.authorization', 'req.headers.cookie', '*.password', '*.token', '*.cardNumber', 'user.email'],
    censor: '[redacted]'
  }
})
```

## 15. Crypto

```ts
import argon2 from 'argon2'
const hash = await argon2.hash(password, { type: argon2.argon2id })
const ok = await argon2.verify(hash, password)
// bcrypt is acceptable. Never MD5, SHA1, or bare SHA256 for passwords.
// Tokens: crypto.randomBytes(32).toString('hex'), never Math.random()
```

## Tooling

```bash
npm audit --omit=dev --audit-level=high
npx --yes retire --severity high
semgrep --config p/typescript --config p/nodejs --config p/owasp-top-ten --quiet
# eslint-plugin-security and eslint-plugin-no-unsanitized in the lint config catch sink patterns
```
