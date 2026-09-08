# Tenable + SentinelOne Attack Path Interruption

A Claude Code skill that cross-references a live Tenable One Attack Path Analysis (APA) toxic path against SentinelOne's real-time alert stream, and — only with explicit confirmation — can trigger SentinelOne network isolation on a path host showing active lateral-movement behavior.

## What it does

Tenable One's Attack Path Analysis maps toxic combinations — chains of exposures an attacker could actually walk. SentinelOne's EDR sees attacker behavior live but has no idea which hosts it's watching sit on one of those paths. This skill:

1. **Pulls a toxic path** from Tenable's Hexa MCP (APA domain) — the hop-by-hop host list
2. **Checks SentinelOne** for active alerts, and optionally deeper telemetry correlation via PowerQuery, on each path host
3. **Reports path-aware risk** — the same alert means something very different on a crown-jewel path vs. an isolated dev box
4. **Only with explicit confirmation**, calls SentinelOne's Management Console REST API to network-isolate a specific host

This is a community-built skill, not official guidance from Tenable or SentinelOne. **Containment is consequential**: isolation stays in effect until someone manually reverses it. The skill will not isolate anything without you naming the host and confirming.

## Prerequisites

- Claude Code (or another skill-compatible client) with:
  - Tenable's Hexa MCP connected **with Attack Path Analysis (APA) domain access** — plain Tenable One inventory access is not sufficient for Phase 1
  - SentinelOne's [`purple-mcp`](https://github.com/Sentinel-One/purple-mcp) server connected, for Phase 2
  - Your own SentinelOne API token with write scope for the console REST API, for Phase 3 (`purple-mcp` itself cannot isolate anything)

## How to run

1. Copy or symlink this directory into your Claude Code skills path:
   ```bash
   cp -r tenable-sentinelone-attack-path-interruption ~/.claude/skills/
   ```
2. Ensure the Hexa MCP (APA domain) and `purple-mcp` connections are both set up.
3. In a Claude Code session, say something like:
   - "Is anything actually happening on this attack path right now?"
   - "Check SentinelOne for activity on these exposed hosts"
   - "Isolate this host, it's on a toxic path"

The skill activates automatically from its description, or you can invoke it explicitly.

`scripts/isolate_agent.py` is the containment call used in Phase 3. **It is scaffolding, not a verified working call** — confirm the exact endpoint path against SentinelOne's current published API reference before pointing it at a real tenant.

## What it produces

- A toxic path with per-hop SentinelOne activity overlaid (alerts, and optionally PowerQuery-derived telemetry correlation)
- A clear risk statement tying the two together (e.g. "this host is hop 3 of path X, and SentinelOne has an active alert on it right now")
- Only when explicitly confirmed: a containment action, with post-call verification that isolation actually took effect

## Known limitations

See [SKILL.md Known Limitations](SKILL.md#known-limitations) — most importantly: `purple-mcp` is entirely read-only, so containment always requires a separate direct API call outside the MCP connection, and SentinelOne's documented API has no true per-asset network fencing (isolation is full-agent, not partial).

## License

MIT — see [LICENSE](LICENSE).
