# scripts/build_complete_dataset.py
import pandas as pd
from nhlpy import NHLClient
import json
from pathlib import Path
import time
import requests


def build_dataset():
    client = NHLClient()

    # Create directories
    Path("data/nhl/season_stats").mkdir(parents=True, exist_ok=True)

    print("=== Step 1: Fetching season stats ===")
    # Get all skaters and goalies for 2024-25
    skaters = client.stats.skater_stats_summary_simple(start_season="20242025", end_season="20242025")
    goalies = client.stats.goalie_stats_summary_simple(start_season="20242025", stats_type="summary")

    # Check if data is a dict or list
    skater_data = skaters if isinstance(skaters, list) else skaters.get("data", [])
    goalie_data = goalies if isinstance(goalies, list) else goalies.get("data", [])

    print(f"Found {len(skater_data)} skaters and {len(goalie_data)} goalies")

    # Save season stats
    with open("data/nhl/season_stats/skaters_202425.json", "w") as f:
        json.dump(skaters, f)
    with open("data/nhl/season_stats/goalies_202425.json", "w") as f:
        json.dump(goalies, f)

    print("\n=== Step 2: Processing shot data ===")
    # Load existing shot data
    df = pd.read_csv("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")
    print(f"Loaded {len(df)} shots")

    # Extract unique player IDs
    player_ids = set()
    for col in ["shooter_id", "goalie_id", "assist1_id", "assist2_id"]:
        player_ids.update(df[col].dropna().astype(int))
    print(f"Found {len(player_ids)} unique players in shot data")

    # Get unique game IDs
    game_ids = df["game_id"].unique()
    print(f"Found {len(game_ids)} unique games")

    print("\n=== Step 3: Fetching all player stats from shot data ===")
    all_player_stats = {}

    for i, player_id in enumerate(player_ids):
        if i % 100 == 0:
            print(f"Progress: {i}/{len(player_ids)} players")
            time.sleep(1)

        try:
            # Check cache first
            cache_file = Path(f"data/nhl/players/{player_id}.json")
            if cache_file.exists():
                with open(cache_file) as f:
                    data = json.load(f)
            else:
                # Get player landing page (has current season stats)
                response = requests.get(f"https://api-web.nhle.com/v1/player/{player_id}/landing")
                data = response.json()
                # Save to cache
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cache_file, "w") as f:
                    json.dump(data, f)

            # Extract current season stats
            current_season = data.get("featuredStats", {}).get("regularSeason", {}).get("subSeason", {})

            all_player_stats[player_id] = {
                "height": data.get("heightInInches"),
                "weight": data.get("weightInPounds"),
                "position": data.get("position"),
                "shoots": data.get("shootsCatches"),
                # Current season stats
                "goals": current_season.get("goals", 0),
                "assists": current_season.get("assists", 0),
                "plusMinus": current_season.get("plusMinus", 0),
                "shootingPct": current_season.get("shootingPctg", 0),
                "savePct": current_season.get("savePctg", 0) if data.get("position") == "G" else None,
                "gamesPlayed": current_season.get("gamesPlayed", 0),
            }
        except Exception:
            all_player_stats[player_id] = {}

    # Save all player stats
    with open("data/nhl/season_stats/all_players_202425.json", "w") as f:
        json.dump(all_player_stats, f)

    print("\n=== Data collection complete! ===")
    print("Files saved in data/nhl/season_stats/")
    print("- skaters_202425.json")
    print("- goalies_202425.json")
    print("- all_players_202425.json")

    return {
        "total_skaters": len(skater_data),
        "total_goalies": len(goalie_data),
        "total_players_in_shots": len(player_ids),
        "total_games": len(game_ids),
        "total_shots": len(df),
    }


if __name__ == "__main__":
    stats = build_dataset()
    print("\nSummary:", json.dumps(stats, indent=2))
