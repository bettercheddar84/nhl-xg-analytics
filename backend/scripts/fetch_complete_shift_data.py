# scripts/fetch_complete_shift_data.py
import requests
import json
import pandas as pd
from pathlib import Path
import time

# Create directories
Path("data/nhl/shifts").mkdir(parents=True, exist_ok=True)

with open("data/nhl/shifts/2024020008.json") as f:
    data = json.load(f)
    print(data["data"][0])

# Load all shots
df = pd.read_csv("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")
all_shots = df
unique_games = all_shots["game_id"].unique()

print(f"Processing shifts for {len(unique_games)} games, {len(all_shots)} total shots")

# First, fetch all shift data if not already cached
for i, game_id in enumerate(unique_games):
    if i % 50 == 0:
        print(f"Fetching shifts: {i}/{len(unique_games)}")

    shift_file = Path(f"data/nhl/shifts/{game_id}.json")
    if not shift_file.exists():
        url = f"https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id}"
        response = requests.get(url)
        shifts = response.json()

        with open(shift_file, "w") as f:
            json.dump(shifts, f)

        time.sleep(0.5)  # Rate limiting

# Process all shots with on-ice players
shot_contexts = []
games_processed = 0

for game_id in unique_games:
    if games_processed % 100 == 0:
        print(f"Processing shots: {games_processed}/{len(unique_games)} games")

    # Load shifts for this game
    with open(f"data/nhl/shifts/{game_id}.json") as f:
        game_shifts = json.load(f)

    # Get all shots from this game
    game_shots = all_shots[all_shots["game_id"] == game_id]

    for _, shot in game_shots.iterrows():
        offensive_on_ice = []
        defensive_on_ice = []

        for shift in game_shifts.get("data", []):
            try:
                # Convert MM:SS to seconds
                start_min, start_sec = shift["startTime"].split(":")
                end_min, end_sec = shift["endTime"].split(":")
                period = shift["period"]

                start_time = (period - 1) * 1200 + int(start_min) * 60 + int(start_sec)
                end_time = (period - 1) * 1200 + int(end_min) * 60 + int(end_sec)

                # Check if player was on ice during shot
                if start_time <= shot["game_seconds"] <= end_time:
                    if shift["teamId"] == shot["shooting_team_id"]:
                        offensive_on_ice.append(shift["playerId"])
                    else:
                        defensive_on_ice.append(shift["playerId"])

            except (ValueError, KeyError):
                continue

        shot_contexts.append(
            {
                "game_id": shot["game_id"],
                "shot_time": shot["game_seconds"],
                "shooter_id": shot["shooter_id"],
                "is_goal": shot["is_goal"],
                "offensive_on_ice": offensive_on_ice,
                "defensive_on_ice": defensive_on_ice,
            }
        )

    games_processed += 1

# Save processed data
pd.DataFrame(shot_contexts).to_csv("data/nhl/shifts/shots_with_on_ice.csv", index=False)
print(f"Processed {len(shot_contexts)} shots with on-ice players")
