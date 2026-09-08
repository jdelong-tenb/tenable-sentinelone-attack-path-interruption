---
name: tenable-sentinelone-attack-path-interruption
description: Cross-references a live Tenable One Attack Path Analysis (APA) toxic path against SentinelOne's real-time alert stream, and — with explicit user confirmation — triggers SentinelOne network isolation on a path host showing active lateral-movement behavior. Invoke when someone says things like "is anything actually happening on this attack path right now," "check SentinelOne for activity on these exposed hosts," or "isolate this host, it's on a toxic path."
---

# Tenable + SentinelOne Attack Path Interruption

## Why this exists

Tenable One's Attack Path Analysis (APA) maps toxic combinations — chains of exposures an attacker could actually walk across the environment. SentinelOne's EDR sees attacker behavior in real time but has no idea which of the hosts it's watching sit on one of those toxic paths. The same lateral-movement alert is a background-noise ticket on an isolated dev box and an active-breach emergency on a host that's step three of a known path to a crown-jewel asset. This skill adds that path context to live SentinelOne activity, and — only with explicit confirmation — can contain the host directly.

This is a community-built skill, not official guidance from either vendor. **Containment is consequential and not silently reversible**: an isolated host stays isolated until someone manually reconnects it. Always confirm the specific host and the specific path justification with the user before calling the isolate action — never isolate automatically based on a match alone.

## Phase 1 — Pull the toxic path

Requires Tenable's Hexa MCP with **Attack Path Analysis (APA) domain access** — this is a different surface from general Tenable One inventory/finding search. Plain `tenable_one_search_assets` / `tenable_one_search_findings` do not expose attack-path graph data. Confirm the user's Tenable MCP connection actually exposes an APA-domain tool before promising this works; if it doesn't, say so rather than trying to approximate a path from findings data.

Retrieve the path's node list: each hop's hostname/IP and the exposure or technique connecting it to the next hop.

**Example user prompts:**
- "Pull the toxic path to [crown jewel asset]"
- "What hosts are on our highest-risk attack path right now?"

## Phase 2 — Check SentinelOne for live activity on path nodes

For each host in the path, resolve it to a SentinelOne asset with `mcp__purple-mcp__search_inventory_items` (filter by name/IP — see the host-matching caveats in the companion asset-reconciliation skill; a wrong resolution here means checking, or later isolating, the wrong machine). Then call `mcp__purple-mcp__search_alerts` filtered to that asset with status `NEW`/`IN_PROGRESS`, ordered by `detectedAt` descending.

Alert-level filters only surface what SentinelOne already classified as an alert. For higher-confidence lateral-movement correlation across adjacent path hops (e.g. anomalous SMB/RDP/WMI activity between two path nodes that hasn't necessarily fired its own alert), use `purple_ai()` to generate a PowerQuery over the relevant time window and run it via `mcp__purple-mcp__powerquery`. Don't hand-write PowerQuery syntax — always generate it through `purple_ai()`.

**Example user prompts:**
- "Is SentinelOne seeing anything on host 3 of this path?"
- "Check for lateral movement between these two path hops in the last 24 hours"

## Phase 3 — Interrupt

**`purple-mcp` cannot isolate anything — it is read-only.** Containment requires a direct authenticated call to SentinelOne's Management Console REST API, using the user's own SentinelOne API token (a different credential than whatever purple-mcp uses). See `scripts/isolate_agent.py` — the exact endpoint path must be confirmed against SentinelOne's current published API reference before this script is used against a real tenant; it is scaffolding, not a verified working call.

Before calling it:
1. Name the specific host and its SentinelOne asset ID back to the user.
2. State which toxic path and which hop justifies isolating it.
3. Get explicit confirmation — never isolate on a match alone.

After the call, confirm the isolation actually took effect (check the returned agent network-connectivity status), not just that the API returned success.

**Example user prompts:**
- "Isolate that host"
- "Confirm it's actually isolated now"

## MCP tools used

- Tenable Hexa MCP's APA-domain tool (exact tool name varies by deployment — check the user's Tenable MCP tool list for an attack-path–specific tool rather than assuming a name) — path retrieval
- `mcp__purple-mcp__search_inventory_items` — resolve a Tenable hostname/IP to a SentinelOne asset ID
- `mcp__purple-mcp__search_alerts` — active alerts on path-node assets
- `mcp__purple-mcp__powerquery` + `purple_ai()` — telemetry correlation across path hops beyond alert-level data
- SentinelOne Management Console REST API (direct call, not MCP) — the isolation action itself; see `scripts/isolate_agent.py`

## Known limitations

- **purple-mcp cannot isolate anything — this is the main thing to know going in.** SentinelOne's public MCP server is read-only end to end. The interruption step is a direct REST call the user's own tenant and API token must support; it is not available through the MCP connection at all.
- **Requires Hexa MCP's APA domain specifically**, not just any Tenable MCP connection. If that domain isn't enabled, this skill can still check SentinelOne activity on named hosts, but can't independently retrieve the toxic path.
- **No true per-asset network fencing exists in SentinelOne's documented API today** — its Firewall Control API scopes to account/site/group, not individual assets, as of this writing (confirm against SentinelOne's current API reference — this can change, same as the isolation endpoint below). "Isolate" here means full network isolation of the agent (an existing, working action), not a scoped virtual patch on one asset. Don't oversell this as partial/surgical containment.
- **Host resolution carries the same best-effort hostname/IP matching risk as asset reconciliation.** A wrong Tenable-to-SentinelOne match means checking — or isolating — the wrong machine. Treat an ambiguous match as a stop, not a guess, especially before Phase 3.
- **Isolation confirmation must be earned, not assumed.** A successful HTTP status from the isolate call is not proof the agent is actually network-isolated — check its reported connectivity state afterward.
