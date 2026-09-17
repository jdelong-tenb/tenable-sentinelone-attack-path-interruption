# Tenable + SentinelOne Attack Path Interruption

A Claude Code skill that cross-references a live Tenable One Attack Path Analysis (APA) toxic path against SentinelOne's real-time alert stream, and — only with explicit confirmation — can trigger SentinelOne network isolation on a path host showing active lateral-movement behavior.

## What it does

Tenable One's Attack Path Analysis maps toxic combinations — chains of exposures an attacker could actually walk. SentinelOne's EDR sees attacker behavior live but has no idea which hosts it's watching sit on one of those paths. This skill:

1. **Pulls a toxic path** from Tenable's Hexa MCP (APA domain) — the hop-by-hop host list
2. **Checks SentinelOne** for active alerts, and optionally deeper telemetry correlation via PowerQuery, on each path host
3. **Reports path-aware risk** — the same alert means something very different on a crown-jewel path vs. an isolated dev box
4. **Only with explicit confirmation**, isolates a specific host on the network via SentinelOne's Management Console API

This is a community-built skill, not official guidance from Tenable or SentinelOne. **Containment is consequential**: isolation stays in effect until someone manually reverses it. The skill will not isolate anything without you naming the host and confirming.

## Community & Support

This repository is a community-driven, open source project designed to streamline the deployment and use of SentinelOne and Tenable integrations. While not a formal SentinelOne product, this repository is maintained in partnership with SentinelOne and supported by the open source developer community.

## Prerequisites

- Claude Code (or another skill-compatible client) with:
  - Tenable's Hexa MCP connected **with Attack Path Analysis (APA) domain access** — plain Tenable One inventory access is not sufficient for Phase 1
  - SentinelOne's [`purple-mcp`](https://github.com/Sentinel-One/purple-mcp) server connected, for Phase 2
  - For Phase 3 (containment): SentinelOne's [`s1-secops-mcp`](https://github.com/Sentinel-One/ai-siem/tree/main/mcp/s1-secops-mcp) server, which — unlike `purple-mcp` — has write access to the Management Console API. If that's not configured, `scripts/isolate_agent.py` falls back to a direct authenticated call using your own SentinelOne API token.

## How to run

1. Copy or symlink this directory into your Claude Code skills path:
   ```bash
   cp -r tenable-sentinelone-attack-path-interruption ~/.claude/skills/
   ```
2. Ensure the Hexa MCP (APA domain) and `purple-mcp` connections are set up; connect `s1-secops-mcp` too if you want Phase 3 (containment) available through MCP rather than the fallback script.
3. In a Claude Code session, say something like:
   - "Is anything actually happening on this attack path right now?"
   - "Check SentinelOne for activity on these exposed hosts"
   - "Isolate this host, it's on a toxic path"

The skill activates automatically from its description, or you can invoke it explicitly.

`scripts/isolate_agent.py` is the fallback containment call for Phase 3, used only when `s1-secops-mcp` isn't configured. **It is scaffolding, not a verified working call** — confirm the exact endpoint path against SentinelOne's current published API reference before pointing it at a real tenant. The same caveat applies to the endpoint path passed to `s1-secops-mcp`'s `s1_api_post`.

## What it produces

- A toxic path with per-hop SentinelOne activity overlaid (alerts, and optionally PowerQuery-derived telemetry correlation)
- A clear risk statement tying the two together (e.g. "this host is hop 3 of path X, and SentinelOne has an active alert on it right now")
- Only when explicitly confirmed: a containment action, with post-call verification that isolation actually took effect

## Known limitations

See [SKILL.md Known Limitations](SKILL.md#known-limitations) — most importantly: `purple-mcp` is entirely read-only, so containment always goes through the separate `s1-secops-mcp` server (or the fallback script) instead, and SentinelOne's documented API has no true per-asset network fencing (isolation is full-agent, not partial).

## License

MIT — see [LICENSE](LICENSE).
