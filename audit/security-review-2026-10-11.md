# Security review: vercel-labs/skills

Reviewed on October 11, 2026, for the requested GitHub fork and local Codex skill installation. Source: [vercel-labs/skills at 13e4063a1cf913f5606d57d42ab83a86f5001e04](https://github.com/vercel-labs/skills/tree/13e4063a1cf913f5606d57d42ab83a86f5001e04), package version 1.7.2, MIT license.

## Decision

No overt malicious prompt injection or hidden payload was found in the reviewed source. The full CLI has material privacy, installation, and supply-chain risks. Install the separately named `skills/vercel-find-skills` Codex adaptation, using the exact reviewed fork commit. It preserves existing `find-skills`, uses a read-only standard-library catalog helper, and routes candidate installation through Codex's own pinned skill installer after source review.

The fork's `main` remains the upstream replica. The `codex-find-skills` branch adds this audit and the reviewed discovery skill. Existing CLI code is unchanged; its risks are avoided by the installed skill, not repaired in the CLI.

## Scope and evidence

- Scanned all 138 upstream tracked files, including three `SKILL.md` packages, one `AGENTS.md`, one README, three GitHub workflows, and five `.factory` files.
- Read the skill instructions and maintenance automation instructions; inspected relevant installer, archive, subprocess, credential, network, manifest, lockfile, and build paths in parallel independent reviews.
- Zero tracked symlinks, binary/NUL files, unexpected hidden Unicode controls, large encoded blobs, or common private-key/credential signatures found. These checks are heuristic and do not establish complete absence of malicious behavior.
- All three upstream skill folders and the adaptation passed Codex's official `quick_validate.py`. This checks structure, not security.
- Queried npm's public advisory endpoint for all 156 exact locked package records, without installing dependencies. The saved [advisory snapshot](dependency-advisories.json) contains 12 advisory records across eight packages, representing 11 distinct GHSA IDs.
- Did not execute upstream code, dependency lifecycle scripts, build, repository tests, npm CLI distribution, or maintenance automations. Historical commits, hosted-service internals, and npm bundle equivalence were not audited.

## Findings

| Finding | Evidence at reviewed source | Practical effect |
| --- | --- | --- |
| Source-copy installation follows symlinks | `src/installer.ts:538-547`, `cp` with `dereference: true` and `recursive: true` | A malicious cloned/local skill can cause readable local files outside the repository to be copied into an installed skill. No automatic upload was identified in this path. Reject source symlinks or check resolved containment. |
| Well-known v0.2 artifacts have unbounded allocation paths | `src/providers/wellknown.ts:506-511,705-717` | Fetch reads the complete response without byte limit/timeout; tar.gz expands through unbounded `gunzipSync` before extracted-size checks. A provider controlling artifact and digest can exhaust memory. The separate direct-archive downloader has limits and rejects links/traversal. |
| Search telemetry defaults on | `src/telemetry.ts:41-45,86-88,143-175`; `src/find.ts:343-348` | Search query and event metadata reach `www.skills.sh/tele/t`. `DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` disables these events and audit requests. Search itself still sends query terms to `/api/search`. |
| Upstream skill recommends mutable executable npm downloads | `skills/find-skills/SKILL.md:23,27-29,56,100` | Unpinned `npx skills` can run code outside the audited commit; `-g -y` permits broad global installation. The adaptation uses a read-only helper and Codex's reviewed installer. |
| Build fetches an extra unpinned executable dependency | `scripts/generate-licenses.ts:54`; `package.json:17,21` | `npx license-checker --json` is reached by build/prepublish and is not pinned in the manifest/lockfile. Source installation also has `prepare: husky`. No build was run. |
| Snapshot cache adds hosted-service trust | `src/blob.ts:473-477,567,666-669,682-696` | Cache content and hashes come from skills.sh rather than independent GitHub blob verification. Explicit refs disable this fast path. No evidence of a compromised cache was found. |
| Adoption is used as a safety proxy | `skills/find-skills/SKILL.md:45,69-71` | Stars and installs cannot establish safety; the adaptation requires inspecting exact source. |
| Fork retains upstream maintenance configuration | `.factory/config.yml:3-4`; `.factory/workflows/triage/workflow.md:13-24` | Identity `github:quuu` and mention instructions remain in the replicated source. These automations were not activated or installed as local skills. |
| Release tooling and instruction CI have gaps | `.github/workflows/ci.yml:5-10`; publish/CI action references | Markdown changes skip general CI; checkout/setup-node use mutable version tags. Some other actions use commit pins. Release uses provenance, but registry attestations and environment protections were not verified. |

Git retains trusted caller configuration and enables many simple-git unsafe categories (`src/git.ts:196-225`), while restricting transports and disabling LFS downloads. Credential helpers, SSH commands, filters, and configured hooks may execute local programs; this is inherited configuration behavior, not evidence of downloaded malicious instructions. Tokens are read from explicit environment variables, and stored GitHub CLI tokens are not extracted.

## Dependency advisories

These are affected versions in the committed lockfile, not proof that every vulnerability is reachable in the CLI. The source review identified no arbitrary attacker-controlled clone argument flow, no push or interpret-trailers sink, and no tar member-selection list. Development-tool advisories are distinct from CLI runtime exposure.

| Locked package | Advisory | Reachability qualification |
| --- | --- | --- |
| `simple-git@3.36.0` | [GHSA-x6jw-m9v5-85vh](https://github.com/advisories/GHSA-x6jw-m9v5-85vh), critical; [GHSA-g4wm-2vf7-vfgr](https://github.com/advisories/GHSA-g4wm-2vf7-vfgr), high; [GHSA-858h-whjf-mvg5](https://github.com/advisories/GHSA-858h-whjf-mvg5), high | Attacker-controlled config/custom arguments or push behavior required; relevant sink not established. Preserve and review the intentional unsafe configuration policy during any upgrade. |
| `@simple-git/argv-parser@1.1.1` | [GHSA-v5rq-49vh-5v5c](https://github.com/advisories/GHSA-v5rq-49vh-5v5c), critical | Requires attacker-controlled editor environment and an editor-launching Git command; not identified in the clone workflow. |
| `tar@7.5.20` | [GHSA-r292-9mhp-454m](https://github.com/isaacs/node-tar/security/advisories/GHSA-r292-9mhp-454m), high | Requires a nonempty member-selection list; current `tar.x` supplies options only. Patched 7.5.21. |
| `vitest@4.1.10`, `@vitest/mocker@4.1.10` | [GHSA-82fw-gwwq-j7x9](https://github.com/advisories/GHSA-82fw-gwwq-j7x9), moderate | Development server file-read issue; not an installed CLI runtime dependency. |
| `nanoid@3.3.15` | [GHSA-28wg-ghj8-5hjv](https://github.com/advisories/GHSA-28wg-ghj8-5hjv), high; [GHSA-2v37-7h3g-55p8](https://github.com/advisories/GHSA-2v37-7h3g-55p8), high | Transitive development tooling; no direct source use identified. |
| `postcss@8.5.16` | [GHSA-r28c-9q8g-f849](https://github.com/advisories/GHSA-r28c-9q8g-f849), high; [GHSA-fxqj-rqcc-2cmp](https://github.com/advisories/GHSA-fxqj-rqcc-2cmp), moderate | Transitive development tooling; no direct CLI source use identified. |
| `source-map-js@1.2.1` | [GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q), high | Transitive development tooling; no direct source use identified. |

## Adaptation verification

The installed package consists of `SKILL.md`, `scripts/search.py`, `references/provenance.md`, and the original MIT `LICENSE`. Python standard library only; no npm dependency stack. Search requests have a 15-second socket timeout and a 2 MiB response cap, restrict redirects to HTTPS skills.sh hosts, send no authorization header, and print escaped JSON. The helper returns GitHub-shaped sources and never installs search results.

Independent review and mocked checks covered sorting, owner filtering, hostile metadata, malformed/oversized responses, redirect restrictions, and absence of an authorization header. A live generic search for `react performance --owner vercel-labs` returned Vercel catalog results. Every newly discovered skill still requires its own source review. Catalog requests expose generic search terms to skills.sh, which may log normal requests.

The npm distribution was not installed or audited. Its generated `dist/cli.mjs` is absent from the source checkout, so this review does not certify its published bundle. Future updates to either source or installed skills require fresh review.
