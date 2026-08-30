#!/usr/bin/env python3
"""
State management for topic rotation and idempotent publishing.

State lives at config.state.path, or state/<product-slug>.json next to the config.
It records every published post with a content hash, so a re-run of the same job
does not publish a duplicate, and so category rotation has ground truth.

Subcommands:
    show    Print the current state (last category, recent posts).
    check   Decide if a draft is safe to publish.
    record  Append a published post and update rotation.

Examples:
    python scripts/state.py show   --config product-config.json
    python scripts/state.py check  --config product-config.json --slug my-post --content-file draft.md
    python scripts/state.py record --config product-config.json --slug my-post --title "My Post" \
        --category how-to --content-file draft.md --url https://site/blog/my-post

check exit codes:
    0  NEW                 slug and content are new, publish it
    3  DUPLICATE_CONTENT   identical content already published, skip
    4  SLUG_EXISTS         slug taken by different content, publish under the suggested slug
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def slugify(text):
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "product"


def load_config(path):
    return json.loads(Path(path).read_text())


def state_path(config, config_file):
    configured = config.get("state", {}).get("path")
    if configured:
        return Path(configured)
    name = slugify(config.get("product", {}).get("name", "product"))
    return Path(config_file).resolve().parent / "state" / f"{name}.json"


def load_state(path):
    if path.exists():
        return json.loads(path.read_text())
    return {"product": None, "lastCategory": None, "categoryHistory": [], "posts": []}


def content_hash(content_file):
    text = Path(content_file).read_text()
    normalized = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def next_free_slug(slug, taken):
    if slug not in taken:
        return slug
    n = 2
    while f"{slug}-{n}" in taken:
        n += 1
    return f"{slug}-{n}"


def cmd_show(config, sp):
    state = load_state(sp)
    posts = state.get("posts", [])
    print(json.dumps({
        "statePath": str(sp),
        "lastCategory": state.get("lastCategory"),
        "categoryHistory": state.get("categoryHistory", [])[-10:],
        "postCount": len(posts),
        "recentPosts": [
            {"slug": p.get("slug"), "title": p.get("title"), "category": p.get("category")}
            for p in posts[-8:]
        ],
    }, indent=2))


def cmd_check(config, sp, args):
    state = load_state(sp)
    posts = state.get("posts", [])
    h = content_hash(args.content_file)
    by_slug = {p["slug"]: p for p in posts}

    if any(p.get("contentHash") == h for p in posts):
        print("DUPLICATE_CONTENT: identical content already published. Skip.")
        sys.exit(3)

    if args.slug in by_slug:
        suggested = next_free_slug(args.slug, set(by_slug))
        print(f"SLUG_EXISTS: '{args.slug}' is taken by different content. Use slug '{suggested}'.")
        sys.exit(4)

    print(f"NEW: safe to publish '{args.slug}'.")
    sys.exit(0)


def cmd_record(config, sp, args):
    state = load_state(sp)
    state["product"] = config.get("product", {}).get("name")
    state.setdefault("posts", [])
    state.setdefault("categoryHistory", [])
    state["posts"].append({
        "slug": args.slug,
        "title": args.title,
        "category": args.category,
        "contentHash": content_hash(args.content_file),
        "url": args.url,
        "publishedAt": datetime.now(timezone.utc).isoformat(),
    })
    state["lastCategory"] = args.category
    state["categoryHistory"].append(args.category)
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Recorded '{args.slug}' [{args.category}]. State at {sp}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_show = sub.add_parser("show")
    p_show.add_argument("--config", default="product-config.json")

    p_check = sub.add_parser("check")
    p_check.add_argument("--config", default="product-config.json")
    p_check.add_argument("--slug", required=True)
    p_check.add_argument("--content-file", required=True)

    p_record = sub.add_parser("record")
    p_record.add_argument("--config", default="product-config.json")
    p_record.add_argument("--slug", required=True)
    p_record.add_argument("--title", required=True)
    p_record.add_argument("--category", required=True)
    p_record.add_argument("--content-file", required=True)
    p_record.add_argument("--url", default="")

    args = ap.parse_args()
    config = load_config(args.config)
    sp = state_path(config, args.config)

    if args.cmd == "show":
        cmd_show(config, sp)
    elif args.cmd == "check":
        cmd_check(config, sp, args)
    elif args.cmd == "record":
        cmd_record(config, sp, args)


if __name__ == "__main__":
    main()
