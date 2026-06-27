# scripts/extract_season_features.py
import json
import pandas as pd

# Load season stats
with open("data/nhl/season_stats/all_players_202425.json") as f:
    all_players = json.load(f)

with open("data/nhl/season_stats/team_stats.json") as f:
    team_stats = json.load(f)

# Extract player features
player_features = []
for player_id, stats in all_players.items():
    player_features.append(
        {
            "player_id": int(player_id),
            "season_goals": stats.get("goals", 0),
            "season_assists": stats.get("assists", 0),
            "season_shooting_pct": stats.get("shootingPct", 0),
            "season_plus_minus": stats.get("plusMinus", 0),
            "season_games": stats.get("gamesPlayed", 0),
            "hot_streak": stats.get("goals", 0) > 20,  # Simple hot player indicator
        }
    )

# Extract team features
team_features = []
for team in team_stats.get("data", []):
    team_features.append(
        {
            "team_id": team["teamId"],
            "team_goals_per_game": team["goalsForPerGame"],
            "team_shooting_pct": team["shootingPct"],
            "team_save_pct": team["savePct"],
            "team_pp_pct": team["powerPlayPct"],
        }
    )

# Save
pd.DataFrame(player_features).to_csv("data/nhl/processed/season_player_features.csv", index=False)
pd.DataFrame(team_features).to_csv("data/nhl/processed/season_team_features.csv", index=False)

print(f"Extracted {len(player_features)} player season stats")
print(f"Extracted {len(team_features)} team stats")
