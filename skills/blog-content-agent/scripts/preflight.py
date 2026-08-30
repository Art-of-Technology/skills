#!/usr/bin/env python3
"""
Preflight check. Run before any expensive work.

Validates the product config, confirms required environment variables are set,
scans the config for literal secrets (which must live in env vars, not the file),
and prints a state summary so topic rotation and dedup have ground truth.

Usage:
    python scripts/preflight.py [path/to/product-config.json]

Exit codes:
    0  ready to run
    1  validation failed, do not proceed
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

KNOWN_PLATFORMS = {"generic-rest", "wordpress", "ghost", "devto", "markdown-file"}
REMOTE_PLATFORMS = {"generic-rest", "wordpress", "ghost", "devto"}

# Hard-fail patterns. These mean a live secret is sitting in the config file.
SECRET_PATTERNS = [
    (re.compile(r"Bearer\s+\S+"), "bearer token"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"), "API key (sk-...)"),
    (re.compile(r"\bak_live_[A-Za-z0-9]{12,}"), "live API key (ak_live_...)"),
    (re.compile(r"\bblog_[A-Za-z0-9]{16,}"), "blog API key (blog_...)"),
    (re.compile(r"hooks\.slack\.com/services/\S+"), "Slack webhook URL"),
    (re.compile(r"discord(?:app)?\.com/api/webhooks/\S+"), "Discord webhook URL"),
]
# Soft-warn pattern: a bare high-entropy token as a whole value.
TOKEN_LIKE = re.compile(r"^[A-Za-z0-9_\-]{32,}$")


def slugify(text):
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "product"


def walk_strings(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def scan_secrets(config, raw_text):
    errors, warnings = [], []
    for pattern, label in SECRET_PATTERNS:
        if pattern.search(raw_text):
            errors.append(f"Config contains a {label}. Move it to an environment variable and reference its name in the secrets block.")
    for path, value in walk_strings(config):
        # env-var-name fields and the note are expected to hold strings; skip.
        if path.startswith("secrets."):
            continue
        if path.endswith("Env"):
            continue
        if TOKEN_LIKE.match(value) and any(c.isdigit() for c in value) and any(c.isalpha() for c in value):
            warnings.append(f"Field '{path}' looks like a raw token. Confirm it is not a secret.")
    return errors, warnings


def required_env_vars(config):
    secrets = config.get("secrets", {})
    platform = config.get("platform", {})
    required = {}
    if platform.get("type") in REMOTE_PLATFORMS:
        name = secrets.get("blogApiKeyEnv")
        if name:
            required[name] = "blog publish auth"
    if config.get("banner", {}).get("enabled"):
        name = secrets.get("bannerApiKeyEnv")
        if name:
            required[name] = "banner image generation"
    if config.get("notify", {}).get("enabled"):
        name = secrets.get("notifyUrlEnv")
        if name:
            required[name] = "publish notification"
    return required


def state_path(config, config_file):
    configured = config.get("state", {}).get("path")
    if configured:
        return Path(configured)
    name = slugify(config.get("product", {}).get("name", "product"))
    return Path(config_file).resolve().parent / "state" / f"{name}.json"


def show_state(path):
    if not path.exists():
        print(f"  state: none yet at {path} (first run)")
        return
    try:
        state = json.loads(path.read_text())
    except Exception as e:
        print(f"  state: WARN could not parse {path}: {e}")
        return
    posts = state.get("posts", [])
    print(f"  state: {path}")
    print(f"    last category : {state.get('lastCategory', 'none')}")
    print(f"    posts on record: {len(posts)}")
    recent = posts[-5:]
    for p in recent:
        print(f"      - [{p.get('category','?')}] {p.get('slug','?')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config", nargs="?", default="product-config.json")
    args = ap.parse_args()

    cfg_file = Path(args.config)
    print(f"Preflight: {cfg_file}")
    if not cfg_file.exists():
        print(f"FAIL: config not found at {cfg_file}")
        sys.exit(1)

    raw = cfg_file.read_text()
    try:
        config = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"FAIL: config is not valid JSON: {e}")
        sys.exit(1)

    errors, warnings = [], []

    # Required product fields.
    product = config.get("product", {})
    if not product.get("name"):
        errors.append("product.name is required.")
    if not product.get("repo") and not product.get("repoPath"):
        errors.append("Set product.repo or product.repoPath so the repo brief can be built.")

    # Platform.
    ptype = config.get("platform", {}).get("type")
    if ptype not in KNOWN_PLATFORMS:
        errors.append(f"platform.type '{ptype}' is unknown. Use one of: {', '.join(sorted(KNOWN_PLATFORMS))}.")
    else:
        if ptype in REMOTE_PLATFORMS and not config["platform"].get("publishUrl"):
            errors.append(f"platform.publishUrl is required for type '{ptype}'.")
        if ptype == "markdown-file" and not config["platform"].get("publishUrl"):
            errors.append("platform.publishUrl must point to the local posts directory for markdown-file.")

    # Secret scan.
    sec_errors, sec_warnings = scan_secrets(config, raw)
    errors += sec_errors
    warnings += sec_warnings

    # Env vars.
    for name, purpose in required_env_vars(config).items():
        if not os.environ.get(name):
            errors.append(f"Environment variable '{name}' is not set (needed for {purpose}).")
    if product.get("repo") and not product.get("repoPath"):
        token_env = config.get("secrets", {}).get("repoTokenEnv")
        if token_env and not os.environ.get(token_env):
            warnings.append(f"'{token_env}' not set. Fine for public repos, required for private ones.")

    # Report.
    for w in warnings:
        print(f"  WARN: {w}")
    if errors:
        print()
        for e in errors:
            print(f"  FAIL: {e}")
        print("\nPreflight failed. Fix the above before running.")
        sys.exit(1)

    print("  config: valid")
    print("  env   : required variables present")
    show_state(state_path(config, args.config))
    print("\nPreflight passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
