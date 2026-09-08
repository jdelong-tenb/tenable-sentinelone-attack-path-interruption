#!/usr/bin/env python3
"""
Containment scaffold for the tenable-sentinelone-attack-path-interruption
skill's Phase 3. Calls SentinelOne's Management Console REST API directly —
NOT through purple-mcp, which is read-only and has no isolation tool.

*** NOT LIVE-VERIFIED. CONFIRM BEFORE USE. ***
The endpoint path and body shape below (POST /web/api/v2.1/agents/actions/disconnect)
reflect SentinelOne's publicly documented network-isolation action as of this
writing. Confirm the exact path, auth header, and body shape against your
tenant's current API reference (https://<your-console>/api-doc/overview)
before running this against anything real — SentinelOne's API can and does
change versions. This script defaults to a dry run and requires --confirm
plus the exact agent ID to do anything.

Usage:
    export SENTINELONE_CONSOLE_URL="https://<your-console>.sentinelone.net"
    export SENTINELONE_API_TOKEN="..."
    python3 isolate_agent.py <agent_id> --reason "hop 3 of toxic path X, active alert <id>"
    python3 isolate_agent.py <agent_id> --reason "..." --confirm   # actually calls the API
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def isolate(console_url, api_token, agent_id):
    url = f"{console_url.rstrip('/')}/web/api/v2.1/agents/actions/disconnect"
    body = json.dumps({"filter": {"ids": [agent_id]}}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"ApiToken {api_token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("agent_id", help="SentinelOne agent ID to isolate (from search_inventory_items, not the Tenable asset ID)")
    parser.add_argument("--reason", required=True, help="Attack-path justification — logged and printed, never optional")
    parser.add_argument("--confirm", action="store_true", help="Actually call the API. Without this flag, the script only prints what it would do.")
    args = parser.parse_args()

    console_url = os.environ.get("SENTINELONE_CONSOLE_URL")
    api_token = os.environ.get("SENTINELONE_API_TOKEN")

    print(f"Target agent: {args.agent_id}")
    print(f"Reason: {args.reason}")

    if not args.confirm:
        print("\nDry run only (pass --confirm to actually isolate). No API call made.")
        sys.exit(0)

    if not console_url or not api_token:
        print("SENTINELONE_CONSOLE_URL and SENTINELONE_API_TOKEN must both be set.", file=sys.stderr)
        sys.exit(1)

    print("\n*** Calling SentinelOne isolation endpoint — this is NOT silently reversible. ***")
    try:
        result = isolate(console_url, api_token, args.agent_id)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"\nFAILED — HTTP {e.code}: {body[:500]}", file=sys.stderr)
        print(
            "Unknown whether isolation took effect. Verify the agent's connectivity "
            "status directly in the SentinelOne console before assuming anything.",
            file=sys.stderr,
        )
        sys.exit(1)
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"\nFAILED — network error calling SentinelOne: {e}", file=sys.stderr)
        print(
            "Unknown whether isolation took effect. Verify the agent's connectivity "
            "status directly in the SentinelOne console before assuming anything.",
            file=sys.stderr,
        )
        sys.exit(1)
    except ValueError as e:
        print(f"\nFAILED — could not parse SentinelOne's response: {e}", file=sys.stderr)
        print(
            "The API call was sent, but the response was not valid JSON. Verify the "
            "agent's connectivity status directly in the SentinelOne console — do not "
            "assume the call had no effect.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(json.dumps(result, indent=2))
    print(
        "\nDo not treat this response alone as proof of isolation. Re-check the "
        "agent's network connectivity status (e.g. via list_inventory_items / "
        "search_inventory_items) before reporting containment as complete."
    )


if __name__ == "__main__":
    main()
