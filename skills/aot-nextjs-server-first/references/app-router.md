# App Router: server-first idioms

Contents: server-only module, RSC reads, parallel fetches, suspense and streaming, DTO mapping, server actions, revalidation, error and empty states, verification.

## Server-only API client

`server-only` turns an accidental client import into a build error. That guarantee is the point.

```ts
// lib/api/server.ts
import 'server-only'
import { cookies } from 'next/headers'

const BASE = process.env.API_BASE_URL!        // not NEXT_PUBLIC_
const SERVICE_TOKEN = process.env.API_TOKEN!  // not NEXT_PUBLIC_

export async function apiGet<T>(
  path: string,
  init?: { revalidate?: number | false; tags?: string[] },
): Promise<T> {
  const session = (await cookies()).get('session')?.value
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      authorization: `Bearer ${SERVICE_TOKEN}`,
      'x-session': session ?? '',        // upstream resolves the user
    },
    cache: init?.revalidate === false ? 'no-store' : 'force-cache',
    next: init?.revalidate === false
      ? undefined
      : { revalidate: init?.revalidate ?? 60, tags: init?.tags },
  })
  if (!res.ok) throw new ApiError(res.status, path)
  return res.json() as Promise<T>
}
```

Per-user data uses `revalidate: false`, which sets `no-store`. Caching one user's contact list and serving it to another is a privacy incident, not a performance win.

## Reads in the server component

```tsx
// app/(app)/contacts/page.tsx  — server component, no 'use client'
import { listContacts } from '@/lib/api/contacts'
import { ContactTable } from './contact-table'

export default async function ContactsPage({
  searchParams,
}: { searchParams: Promise<{ q?: string; page?: string }> }) {
  const { q, page } = await searchParams
  const contacts = await listContacts({ q, page: Number(page ?? 1) })
  return <ContactTable initialData={contacts} />
}
```

The client table receives data as props on first paint. No mount fetch, no spinner, no shift.

## Parallel, never sequential

```tsx
// bad: waterfall, total time is the sum
const org = await getOrg(orgId)
const plan = await getPlan(org.planId)
const seats = await getSeats(orgId)

// good: independent calls run together
const [org, seats] = await Promise.all([getOrg(orgId), getSeats(orgId)])
const plan = await getPlan(org.planId)   // genuinely dependent, stays sequential
```

## Streaming instead of blocking

Slow segments belong behind their own boundary so the shell paints immediately.

```tsx
// app/(app)/contacts/[id]/page.tsx
export default async function ContactPage({ params }) {
  const { id } = await params
  return (
    <>
      <ContactHeader id={id} />               {/* fast, awaited inline */}
      <Suspense fallback={<TimelineSkeleton />}>
        <ContactTimeline id={id} />           {/* slow, streams in */}
      </Suspense>
      <Suspense fallback={<DealsSkeleton />}>
        <ContactDeals id={id} />
      </Suspense>
    </>
  )
}
```

Skeleton dimensions must match the resolved content. A 64px skeleton replaced by a 180px panel is layout shift with extra steps. Set explicit heights and row counts.

Route-level `loading.tsx` covers navigation. Component-level `Suspense` covers slow data inside a route. Use both.

## DTO mapping at the server edge

Map before the boundary. Everything passed to a client component is in the RSC payload and readable.

```ts
// lib/api/contacts.ts
import 'server-only'

export type ContactDto = {
  id: string
  name: string
  email: string
  stage: 'lead' | 'active' | 'lost'
}

export async function listContacts(q: ListQuery): Promise<ContactDto[]> {
  const rows = await apiGet<UpstreamContact[]>(buildPath(q), { revalidate: false })
  return rows.map(r => ({
    id: r.id,
    name: `${r.first_name} ${r.last_name}`.trim(),
    email: r.email,
    stage: r.pipeline_stage,
    // internal_notes, acquisition_cost, deleted_at, owner_tenant_id: dropped
  }))
}
```

Explicit field lists, never spread. A spread leaks every field the upstream adds later.

## Mutations as server actions

```ts
// app/(app)/contacts/actions.ts
'use server'
import { revalidateTag } from 'next/cache'
import { z } from 'zod'
import { requireSession } from '@/lib/auth/server'

const Schema = z.object({
  id: z.string().uuid(),
  stage: z.enum(['lead', 'active', 'lost']),
})

export async function updateStage(input: unknown) {
  const session = await requireSession()          // tenant comes from here
  const parsed = Schema.safeParse(input)
  if (!parsed.success) return { ok: false as const, error: 'invalid_input' }

  await apiPatch(`/orgs/${session.orgId}/contacts/${parsed.data.id}`, {
    stage: parsed.data.stage,
  })
  revalidateTag(`contacts:${session.orgId}`)
  return { ok: true as const }
}
```

Points worth keeping: tenant from the session and never from the argument, schema validation on every action because actions are public HTTP endpoints, typed result instead of thrown strings, tag revalidation so lists refresh without a full reload.

Optimistic UI stays on the client with `useOptimistic` wrapping the action call. Server-first does not mean sluggish.

## Errors and empty states

`error.tsx` catches thrown server errors per segment. Return a typed failure from actions instead of throwing for expected cases such as validation or conflict. Never swallow an upstream failure into an empty array; an empty list and a failed request look identical to the user and lead to bad support tickets.

## Verification after each route migration

```bash
npm run build
grep -rl "$API_HOST" .next/static 2>/dev/null && echo "LEAK: host in client bundle"
grep -rlE "[A-Za-z0-9_-]{32,}" .next/static 2>/dev/null | head   # inspect hits manually
```

Then load the route with network throttling on. Content appearing before hydration and never swapping afterward means the migration worked.
