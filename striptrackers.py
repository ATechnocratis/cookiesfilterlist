#!/usr/bin/env python3
"""
Convert Firefox StripOnShare lists into a uBlock Origin filter list.

Uses the syntax:
  *$removeparam=param                  (global)
  ||domain.example^$removeparam=param  (domain-specific)

Sources:
  https://github.com/mozilla-firefox/firefox/blob/main/toolkit/components/antitracking/StripOnShareLists/MPL2/StripOnShare.json
  https://github.com/mozilla-firefox/firefox/blob/main/toolkit/components/antitracking/StripOnShareLists/LGPL/StripOnShareLGPL.json
"""

import json
import urllib.request
from datetime import datetime, timezone
from collections import defaultdict

URLS = [
    "https://raw.githubusercontent.com/mozilla-firefox/firefox/main/toolkit/components/antitracking/StripOnShareLists/MPL2/StripOnShare.json",
    "https://raw.githubusercontent.com/mozilla-firefox/firefox/main/toolkit/components/antitracking/StripOnShareLists/LGPL/StripOnShareLGPL.json",
]

def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url) as resp:
        return json.load(resp)

def collect_rules(data: dict) -> tuple[set[str], dict[str, set[str]]]:
    """
    Returns:
      global_params : set of parameter names that apply everywhere
      domain_params : dict  domain -> set of parameter names
    """
    global_params: set[str] = set()
    domain_params: dict[str, set[str]] = defaultdict(set)

    for name, rule in data.items():
        params = set(rule.get("queryParams", []))
        if not params:
            continue

        is_global = rule.get("isGlobal", False) or name == "global"

        if is_global:
            global_params.update(params)
            continue

        # exact hosts
        for host in rule.get("hosts", []):
            domain_params[host].update(params)

        # schemeless sites (eTLD+1 style)
        for site in rule.get("schemelessSites", []):
            domain_params[site].update(params)

    return global_params, domain_params

def main():
    all_global: set[str] = set()
    all_domain: dict[str, set[str]] = defaultdict(set)

    for url in URLS:
        print(f"Fetching {url} …")
        data = fetch_json(url)
        g, d = collect_rules(data)
        all_global.update(g)
        for domain, params in d.items():
            all_domain[domain].update(params)

    lines = [
        "! Title: Firefox StripOnShare → uBlock Origin",
        f"! Last modified: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "! Expires: 7 days",
        "! Homepage: https://github.com/mozilla-firefox/firefox/tree/main/toolkit/components/antitracking/StripOnShareLists",
        "! Description: Auto-generated from Firefox's Copy Clean Link / Strip-on-Share lists",
        "!",
        "! === Global parameters ===",
    ]

    for param in sorted(all_global, key=str.lower):
        safe = param.replace(",", "\\,")
        lines.append(f"*$removeparam={safe}")

    lines.append("!")
    lines.append("! === Domain-specific parameters ===")

    for domain in sorted(all_domain, key=str.lower):
        params = sorted(all_domain[domain], key=str.lower)
        for param in params:
            safe = param.replace(",", "\\,")
            lines.append(f"||{domain}^$removeparam={safe}")

    output = "\n".join(lines) + "\n"

    outfile = "firefox-strip-on-share.txt"
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\nWrote {len(all_global)} global + {sum(len(p) for p in all_domain.values())} domain-specific rules")
    print(f"→ {outfile}")

if __name__ == "__main__":
    main()