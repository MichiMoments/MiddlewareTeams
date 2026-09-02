"""Smoke test: list all joined Teams and their Channels with IDs."""
import logging
import sys

from teams_core.auth.provider import MsalTokenProvider
from teams_core.adapters.graph.client import GraphClient
from teams_core.config import TeamsConfig

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

cfg = TeamsConfig.from_env()
tokens = MsalTokenProvider(cfg)
client = GraphClient(cfg, tokens)

print("\n=== Teams del service account ===\n")
teams = list(client.paged("/me/joinedTeams"))

if not teams:
    print("No se encontraron Teams. El service account debe ser miembro de al menos un Team.")
    sys.exit(1)

for team in teams:
    name = team.get("displayName", "(sin nombre)")
    team_id = team["id"]
    print(f"  Team: {name}")
    print(f"    id: {team_id}")

    channels = list(client.paged(f"/teams/{team_id}/channels"))
    if not channels:
        print("    (sin canales)")
    else:
        for ch in channels:
            ch_name = ch.get("displayName", "(sin nombre)")
            ch_id = ch["id"]
            membership = ch.get("membershipType", "?")
            print(f"      Canal: {ch_name}  [{membership}]")
            print(f"        id: {ch_id}")
    print()

print("Lectura exitosa.")
