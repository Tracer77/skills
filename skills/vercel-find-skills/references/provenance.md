# Source and review

Based on Vercel's [find-skills](https://github.com/vercel-labs/skills/blob/13e4063a1cf913f5606d57d42ab83a86f5001e04/skills/find-skills/SKILL.md) at commit `13e4063a1cf913f5606d57d42ab83a86f5001e04`, reviewed on October 11, 2026. Vercel's MIT license is included as `../LICENSE`.

The source repository's 138 tracked files were statically scanned, and its skill instructions, network behavior, installer paths, dependency manifests, and maintenance workflows were reviewed. No overt malicious prompt injection, hidden payload, symlink, or common credential signature was found. This is a snapshot review, not a guarantee about future revisions, hosted services, npm packages, or newly discovered skills.

The upstream CLI enables telemetry by default and recommends unpinned executable npm downloads. Its source-copy installer can follow symlinks outside the source tree (`src/installer.ts:538-547`). Its well-known v0.2 artifact provider reads remote artifacts and decompresses tar.gz without allocation limits (`src/providers/wellknown.ts:506-511,716-717`); the separate direct-archive downloader does enforce limits. Dependency advisories and build-time unpinned `license-checker` execution add supply-chain concerns.

This Codex adaptation keeps Vercel's task-based discovery approach and public catalog but replaces npm execution with a bounded, read-only Python search helper. The helper uses the same `/api/search` endpoint as upstream `src/find.ts`. Queries still reach skills.sh, which can log ordinary requests; no separate telemetry event is sent. Only GitHub-shaped results are returned. Catalog results and popularity counts remain untrusted evidence.

Installation uses the reviewed commit through Codex's own skill installer and requires inspecting the candidate's contents. The upstream CLI and maintenance automations are not part of this installed skill. The separately named folder preserves any pre-existing `find-skills`.
