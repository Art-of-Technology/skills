# Platform Adapters

Pick the adapter matching `platform.type` in the config. Each adapter covers two operations: search existing posts (for dedup in Step 2) and publish (Step 8). Read auth tokens from the env var named in `secrets`, never from the config file.

## Common rules

- Slug is kebab-case from the title.
- On a duplicate-slug error, append `-2` (then `-3`, etc.) and retry once.
- Capture the returned slug or URL to build the final link.
- Send the cover image field only if a banner was produced.

---

## generic-rest

A custom blog API. Use the fields from the config: `platform.publishUrl`, `platform.searchUrl`, `platform.authHeaderName`, `platform.authScheme`.

Search:

```bash
curl "$SEARCH_URL?q=KEYWORD" \
  -H "$AUTH_HEADER_NAME: $AUTH_SCHEME $BLOG_API_KEY"
```

Publish:

```bash
curl -X POST "$PUBLISH_URL" \
  -H "$AUTH_HEADER_NAME: $AUTH_SCHEME $BLOG_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "TITLE",
    "content": "MARKDOWN",
    "slug": "kebab-slug",
    "authorName": "AUTHOR",
    "status": "published",
    "coverImageUrl": "BANNER_URL_OR_OMIT"
  }'
```

Map field names to whatever the target API expects. If it has no search endpoint, dedup against its public sitemap at `{site}/sitemap.xml`.

---

## wordpress

WordPress REST API. Auth with an application password as HTTP Basic.

Search:

```bash
curl "https://SITE/wp-json/wp/v2/posts?search=KEYWORD&per_page=20" \
  -u "$WP_USER:$WP_APP_PASSWORD"
```

Publish (convert markdown to HTML first):

```bash
curl -X POST "https://SITE/wp-json/wp/v2/posts" \
  -u "$WP_USER:$WP_APP_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "TITLE",
    "slug": "kebab-slug",
    "content": "<p>HTML BODY</p>",
    "status": "publish"
  }'
```

For a cover image, upload to `/wp-json/wp/v2/media` first, then set `featured_media` to the returned id.

---

## ghost

Ghost Admin API. Auth is a JWT signed from the Admin API key (`id:secret`). Posts accept Lexical or HTML; send markdown wrapped as HTML via the `html` source flag.

Search:

```bash
curl "https://SITE/ghost/api/admin/posts/?filter=title:~'KEYWORD'" \
  -H "Authorization: Ghost $JWT"
```

Publish:

```bash
curl -X POST "https://SITE/ghost/api/admin/posts/?source=html" \
  -H "Authorization: Ghost $JWT" \
  -H "Content-Type: application/json" \
  -d '{"posts":[{"title":"TITLE","slug":"kebab-slug","html":"<p>BODY</p>","status":"published","feature_image":"BANNER_URL_OR_NULL"}]}'
```

Generate the JWT from `$GHOST_ADMIN_KEY` (format `id:secret`) using HS256 with a 5-minute expiry and audience `/admin/`.

---

## devto

Dev.to (Forem) API. Markdown native via the `body_markdown` field. No slug control; Dev.to derives it.

Search your own posts:

```bash
curl "https://dev.to/api/articles/me" -H "api-key: $DEVTO_API_KEY"
```

Publish:

```bash
curl -X POST "https://dev.to/api/articles" \
  -H "api-key: $DEVTO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"article":{"title":"TITLE","published":true,"body_markdown":"MARKDOWN","main_image":"BANNER_URL_OR_NULL","tags":["tag1","tag2"]}}'
```

---

## markdown-file

No remote platform. Write the post as a markdown file with frontmatter into the folder at `platform.publishUrl` (a local path). Common for static-site blogs (Hugo, Astro, Next, Jekyll).

Dedup: list existing filenames and titles in that folder.

Publish:

```bash
cat > "$POSTS_DIR/kebab-slug.md" <<'EOF'
---
title: "TITLE"
slug: kebab-slug
date: 2026-01-01
cover: BANNER_URL_OR_OMIT
---

MARKDOWN BODY
EOF
```

Match the frontmatter keys to the static-site generator the project uses (check the repo's existing posts for the exact schema).
