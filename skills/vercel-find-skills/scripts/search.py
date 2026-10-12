#!/usr/bin/env python3
"""Read-only GitHub skill discovery through the public skills.sh search API."""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://www.skills.sh/api/search"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
OWNER_PATTERN = re.compile(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,38})\Z")
REPO_PATTERN = re.compile(r"[a-zA-Z0-9_.-]{1,100}\Z")


class CatalogRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urllib.parse.urlparse(newurl)
        if (
            target.scheme != "https"
            or target.hostname not in {"skills.sh", "www.skills.sh"}
            or target.username is not None
            or target.password is not None
            or target.port not in {None, 443}
        ):
            raise ValueError("Catalog redirected outside the allowed HTTPS hosts")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def search(query, owner=None):
    params = {"q": query, "limit": "20"}
    if owner:
        params["owner"] = owner
    request = urllib.request.Request(
        API_URL + "?" + urllib.parse.urlencode(params),
        headers={"Accept": "application/json", "User-Agent": "codex-vercel-find-skills/1.0"},
    )
    opener = urllib.request.build_opener(CatalogRedirects())
    with opener.open(request, timeout=15) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError("Catalog response exceeded 2 MiB")
    payload = json.loads(body)
    if not isinstance(payload, dict) or not isinstance(payload.get("skills"), list):
        raise ValueError("Unexpected catalog response format")

    results = []
    skipped = 0
    for item in payload["skills"][:200]:
        if not isinstance(item, dict):
            skipped += 1
            continue
        source, name = item.get("source"), item.get("name")
        parts = source.split("/") if isinstance(source, str) else []
        if (
            len(parts) != 2
            or not OWNER_PATTERN.fullmatch(parts[0])
            or not REPO_PATTERN.fullmatch(parts[1])
            or parts[1] in {".", ".."}
            or not isinstance(name, str)
            or not name.strip()
            or len(name) > 200
            or name in {".", ".."}
            or any(ord(char) < 32 or ord(char) == 127 or char in "/\\" for char in name)
            or (owner and parts[0].lower() != owner.lower())
        ):
            skipped += 1
            continue
        count = item.get("installs")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            count = 0
        catalog_path = "/".join(urllib.parse.quote(part, safe="") for part in [*parts, name])
        results.append({
            "skill": name,
            "source": source,
            "installs": count,
            "repository_url": "https://github.com/" + source,
            "catalog_url": "https://www.skills.sh/" + catalog_path,
        })
    results.sort(key=lambda item: item["installs"], reverse=True)
    return {"query": query, "owner": owner, "results": results[:20], "skipped_results": skipped}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="+", help="Public task keywords sent to skills.sh")
    parser.add_argument("--owner", help="Limit results to a GitHub owner")
    args = parser.parse_args()
    query = " ".join(args.query).strip()
    if not query or len(query) > 200 or any(ord(char) < 32 or ord(char) == 127 for char in query):
        parser.error("Query must contain 1-200 printable characters")
    if args.owner and not OWNER_PATTERN.fullmatch(args.owner):
        parser.error("--owner must be a valid GitHub owner")
    try:
        result = search(query, args.owner)
    except (urllib.error.URLError, OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
