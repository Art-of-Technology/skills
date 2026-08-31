# BFF proxy: allow-listed route handlers

Contents: when a proxy earns its place, the anti-pattern, the pattern, tenant scoping, TanStack Query against the BFF, streaming and uploads, rate limiting, third-party keys.

## When a proxy earns its place

Add a BFF handler only for interactive reads the client must issue itself: typeahead search, filter changes, cursor pagination, polling, and anything feeding a client cache. Everything else belongs in a server component read or a server action.

A proxy adds a network hop and turns the Next server into a throughput bottleneck. That cost is worth paying for interactivity and for third-party keys. Paying it for a page's initial data is a waste.

## The anti-pattern

```ts
// app/api/[...path]/route.ts  — do not do this
export async function GET(req: Request, { params }) {
  const path = params.path.join('/')
  return fetch(`${process.env.API_BASE_URL}/${path}`, {
    headers: { authorization: `Bearer ${process.env.API_TOKEN}` },
  })
}
```

This publishes the entire backend to the internet under the service account's authority. Path traversal, admin endpoints, other tenants' data, all reachable. Worse than the exposed token, because now the endpoint looks sanctioned.

Same failure with a URL parameter: `?url=` turns the handler into an SSRF gadget against the private network and cloud metadata.

## The pattern: named operations

One handler per operation. Explicit input schema. Explicit output DTO. Tenant from the session.

```ts
// app/api/bff/contacts/search/route.ts
import { NextResponse } from 'next/server'
import { z } from 'zod'
import { requireSession } from '@/lib/auth/server'
import { searchContacts } from '@/lib/api/contacts'

const Query = z.object({
  q: z.string().trim().min(1).max(100),
  cursor: z.string().max(200).optional(),
  limit: z.coerce.number().int().min(1).max(50).default(20),
})

export async function GET(req: Request) {
  const session = await requireSession()          // 401 if absent
  const parsed = Query.safeParse(
    Object.fromEntries(new URL(req.url).searchParams),
  )
  if (!parsed.success) {
    return NextResponse.json({ error: 'invalid_query' }, { status: 400 })
  }

  const page = await searchContacts({
    ...parsed.data,
    orgId: session.orgId,                          // server-derived, always
  })

  return NextResponse.json(page, {
    headers: { 'cache-control': 'private, no-store' },
  })
}
```

Four properties to preserve in every handler:

- Session resolved server side. No `orgId`, `tenantId`, or `userId` accepted from the client, including in headers.
- Input validated with a bounded schema. Cap `limit` or a client sets it to 100000.
- Response is a DTO. Same mapping used by the server components.
- `cache-control: private, no-store` on per-user responses so no shared cache retains them.

Directory layout keeps the surface visible: `app/api/bff/<resource>/<operation>/route.ts`. Reviewing the tree tells you the whole client-reachable API.

## Tenant scoping belongs in the query

```ts
// wrong: filter applied after fetching
const all = await api.get(`/contacts/${id}`)
if (all.orgId !== session.orgId) throw new Error('nope')

// right: scope is part of the request
const contact = await api.get(`/orgs/${session.orgId}/contacts/${id}`)
```

The first version depends on a check nobody removes by accident. The second makes cross-tenant access unrepresentable.

## TanStack Query against the BFF

The client keeps its cache. Only the target changes: relative BFF paths instead of the backend host.

```ts
// components/contact-search.tsx
'use client'
export function useContactSearch(q: string) {
  return useQuery({
    queryKey: ['contacts', 'search', q],
    queryFn: async ({ signal }) => {
      const res = await fetch(
        `/api/bff/contacts/search?q=${encodeURIComponent(q)}`,
        { signal },
      )
      if (!res.ok) throw new Error('search_failed')
      return res.json() as Promise<ContactPage>
    },
    enabled: q.length > 0,
    placeholderData: keepPreviousData,   // no blank flash between keystrokes
    staleTime: 30_000,
  })
}
```

`placeholderData: keepPreviousData` removes the flicker on every keystroke. Cookies ride along automatically on same-origin requests, so no token handling in the client.

Seed the cache from the server render to skip the first client fetch:

```tsx
// server component
const initial = await searchContacts({ q: '', orgId: session.orgId })
return <ContactSearch initialData={initial} />
```

## Streaming, uploads, downloads

Pass the body through instead of buffering, and keep the size cap.

```ts
export async function POST(req: Request) {
  const session = await requireSession()
  const len = Number(req.headers.get('content-length') ?? 0)
  if (len > 25_000_000) {
    return NextResponse.json({ error: 'too_large' }, { status: 413 })
  }
  const upstream = await fetch(`${BASE}/orgs/${session.orgId}/files`, {
    method: 'POST',
    headers: {
      authorization: `Bearer ${TOKEN}`,
      'content-type': req.headers.get('content-type') ?? 'application/octet-stream',
    },
    body: req.body,
    duplex: 'half',
  })
  return new Response(upstream.body, { status: upstream.status })
}
```

For large downloads, prefer a short-lived signed URL from the backend over proxying bytes through Next.

## Rate limiting

BFF handlers sit on the public internet under a service account. Typeahead endpoints in particular are cheap to abuse for bulk extraction. Apply a per-session limit in the handler or in middleware, and cap page size.

## Third-party keyed APIs

Always proxied, no judgement call. Maps geocoding, enrichment providers, messaging APIs, PSPs. The key stays in a non-public env var, the handler exposes one named operation, and the response is mapped to a DTO so provider internals stay out of the client.
