# Pages Router: server-first idioms and migration path

Contents: server reads, API route proxying, tenant scoping, flicker fixes, incremental migration to App Router.

## Server reads

`getServerSideProps` runs on the server only. Its imports never reach the bundle, so the API client and token live safely inside it.

```tsx
// pages/contacts/index.tsx
export const getServerSideProps: GetServerSideProps<Props> = async (ctx) => {
  const session = await getSession(ctx.req)
  if (!session) {
    return { redirect: { destination: '/login', permanent: false } }
  }
  const contacts = await listContacts({           // server-only module
    orgId: session.orgId,
    q: typeof ctx.query.q === 'string' ? ctx.query.q : undefined,
  })
  return { props: { contacts } }                  // already DTO-mapped
}
```

Two constraints to respect. Props are serialized into `__NEXT_DATA__` and readable in page source, so map to DTOs before returning. And `getServerSideProps` blocks navigation, so keep it to the data the first paint needs and load secondary panels through the client cache.

For cacheable public data use `getStaticProps` with `revalidate`. Never for per-user data.

## API routes as the proxy layer

Same rules as App Router route handlers. One file per named operation, session server side, bounded schema, DTO out.

```ts
// pages/api/bff/contacts/search.ts
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') return res.status(405).end()
  const session = await getSession(req)
  if (!session) return res.status(401).json({ error: 'unauthorized' })

  const parsed = Query.safeParse(req.query)
  if (!parsed.success) return res.status(400).json({ error: 'invalid_query' })

  const page = await searchContacts({ ...parsed.data, orgId: session.orgId })
  res.setHeader('cache-control', 'private, no-store')
  return res.status(200).json(page)
}
```

Never write `pages/api/[...path].ts` forwarding arbitrary paths. That publishes the backend under the service account.

## Mutations

No server actions here. Post to a named API route, then invalidate the client cache key or call `router.replace(router.asPath, undefined, { scroll: false })` to rerun `getServerSideProps` for the current route.

## Flicker fixes without RSC

- Move first-paint data into `getServerSideProps`. Delete the mount effect.
- Hydrate the client cache from props so the first client query resolves instantly:

```tsx
const { data } = useQuery({
  queryKey: ['contacts', q],
  queryFn: fetchContacts,
  initialData: props.contacts,      // no spinner on first render
  placeholderData: keepPreviousData,
})
```

- Reserve space in skeletons with fixed row heights and counts.
- Give images explicit `width` and `height`, or `fill` with a sized container.
- Guard hydration mismatches: anything depending on `window`, locale, or `Date.now()` renders the server value first, then updates after mount.

## Incremental migration to App Router

Both routers coexist in one project. Migrate by route, highest-value first.

1. Extract the API client into a `server-only` module shared by both routers.
2. Move the DTO mapping out of page files into that module.
3. Recreate one leaf route under `app/`. Verify parity, then delete the `pages/` version.
4. Move shared layout chrome once enough leaves have moved.
5. Convert API routes to `app/api/bff/*` handlers last. They work unchanged in the meantime.

Avoid duplicating the same path in both routers. `app/` wins the conflict and the dead `pages/` file misleads the next reader.
