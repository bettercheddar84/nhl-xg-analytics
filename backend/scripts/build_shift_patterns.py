import json
import pandas as pd
from pathlib import Path
import numpy as np
import ast
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def identify_position_by_shift_length(avg_shift_length):
    """
    Identify player position based on average shift length
    Goalies typically play 20+ minutes (1200+ seconds) per game in long stretches
    Skaters average 45-90 seconds per shift
    """
    if avg_shift_length > 300:  # 5+ minutes average
        return 'G'  # Goalie
    elif avg_shift_length < 60:  # Under 1 minute
        return 'F'  # Forward (shorter shifts)
    elif avg_shift_length < 90:  # 1-1.5 minutes
        return 'D'  # Defenseman (slightly longer shifts)
    else:
        return 'U'  # Unknown

print("Building player shift pattern analysis with proper goalie handling...")

# Load goals with on-ice players
goals_df = pd.read_csv("data/nhl/shifts/goals_with_on_ice_fixed.csv")

# Convert string representation of lists to actual lists
goals_df["offensive_on_ice"] = goals_df["offensive_on_ice"].apply(ast.literal_eval)
goals_df["defensive_on_ice"] = goals_df["defensive_on_ice"].apply(ast.literal_eval)

# Dictionary to store shift data for each player
player_shift_data = {}
player_total_shifts = {}  # Track all shifts to identify goalies

# Helper function to extract player ID from string like "Connor McDavid (8478402)"
def extract_player_id(player_string):
    if "(" in player_string and ")" in player_string:
        return int(player_string.split("(")[-1].strip(")"))
    return None

# First pass: collect ALL shift data to identify positions
print("First pass: Collecting all shift data to identify positions...")
processed_games = set()

for idx, (goal_idx, goal) in enumerate(goals_df.iterrows()):
    game_id = goal["game_id"]
    
    if game_id in processed_games:
        continue
        
    if len(processed_games) % 100 == 0:
        print(f"Processed {len(processed_games)} games for position identification")
    
    try:
        with open(f"data/nhl/shifts/{game_id}.json") as f:
            shifts = json.load(f)["data"]
            
        for shift in shifts:
            player_id = shift["playerId"]
            
            # Calculate shift length
            start_min, start_sec = shift["startTime"].split(":")
            end_min, end_sec = shift["endTime"].split(":")
            start_time = int(start_min) * 60 + int(start_sec)
            end_time = int(end_min) * 60 + int(end_sec)
            shift_length = end_time - start_time
            
            if player_id not in player_total_shifts:
                player_total_shifts[player_id] = []
            
            player_total_shifts[player_id].append(shift_length)
            
        processed_games.add(game_id)
            
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        continue

# Calculate average shift lengths and identify positions
print("Identifying player positions based on shift lengths...")
player_positions = {}

for player_id, shifts in player_total_shifts.items():
    if shifts:
        avg_shift = np.mean(shifts)
        position = identify_position_by_shift_length(avg_shift)
        player_positions[player_id] = {
            'position': position,
            'avg_shift_length': avg_shift,
            'total_shifts': len(shifts)
        }

# Count positions
position_counts = pd.Series([p['position'] for p in player_positions.values()]).value_counts()
print(f"\nPosition distribution:")
print(f"Goalies: {position_counts.get('G', 0)}")
print(f"Forwards: {position_counts.get('F', 0)}")
print(f"Defensemen: {position_counts.get('D', 0)}")
print(f"Unknown: {position_counts.get('U', 0)}")

# Second pass: Process goals with position awareness
print("\nSecond pass: Processing goals with position awareness...")

for idx, (goal_idx, goal) in enumerate(goals_df.iterrows()):
    if idx % 1000 == 0:
        print(f"Processing goal {idx}/{len(goals_df)}")

    game_id = goal["game_id"]
    goal_time = goal["goal_time"]

    # Load shift data for this game
    try:
        with open(f"data/nhl/shifts/{game_id}.json") as f:
            shifts = json.load(f)["data"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        continue

    # Process offensive players (scored)
    for player_str in goal["offensive_on_ice"]:
        player_id = extract_player_id(player_str)
        if player_id and player_positions.get(player_id, {}).get('position') != 'G':  # Skip goalies
            if player_id not in player_shift_data:
                player_shift_data[player_id] = {
                    "shifts_when_scoring": [], 
                    "shifts_when_scored_on": [],
                    "position": player_positions.get(player_id, {}).get('position', 'U')
                }

            # Find this player's shift at goal time
            for shift in shifts:
                if shift["playerId"] == player_id:
                    # Convert times to seconds
                    start_min, start_sec = shift["startTime"].split(":")
                    end_min, end_sec = shift["endTime"].split(":")
                    start_time = (shift["period"] - 1) * 1200 + int(start_min) * 60 + int(start_sec)
                    end_time = (shift["period"] - 1) * 1200 + int(end_min) * 60 + int(end_sec)

                    if start_time <= goal_time <= end_time:
                        shift_length = end_time - start_time
                        time_at_goal = goal_time - start_time
                        player_shift_data[player_id]["shifts_when_scoring"].append({
                            "shift_length": shift_length, 
                            "time_at_goal": time_at_goal
                        })
                        break

    # Process defensive players (scored on)
    for player_str in goal["defensive_on_ice"]:
        player_id = extract_player_id(player_str)
        if player_id and player_positions.get(player_id, {}).get('position') != 'G':  # Skip goalies
            if player_id not in player_shift_data:
                player_shift_data[player_id] = {
                    "shifts_when_scoring": [], 
                    "shifts_when_scored_on": [],
                    "position": player_positions.get(player_id, {}).get('position', 'U')
                }

            # Find this player's shift at goal time
            for shift in shifts:
                if shift["playerId"] == player_id:
                    # Convert times to seconds
                    start_min, start_sec = shift["startTime"].split(":")
                    end_min, end_sec = shift["endTime"].split(":")
                    start_time = (shift["period"] - 1) * 1200 + int(start_min) * 60 + int(start_sec)
                    end_time = (shift["period"] - 1) * 1200 + int(end_min) * 60 + int(end_sec)

                    if start_time <= goal_time <= end_time:
                        shift_length = end_time - start_time
                        time_at_goal = goal_time - start_time
                        player_shift_data[player_id]["shifts_when_scored_on"].append({
                            "shift_length": shift_length,
                            "time_at_goal": time_at_goal
                        })
                        break

# Calculate aggregated metrics for SKATERS ONLY
shift_patterns = []
goalie_patterns = []

for player_id, data in player_shift_data.items():
    scoring_shifts = data["shifts_when_scoring"]
    scored_on_shifts = data["shifts_when_scored_on"]
    position = data.get("position", "U")

    # Calculate averages
    if scoring_shifts:
        avg_shift_scoring = np.mean([s["shift_length"] for s in scoring_shifts])
        avg_time_at_goal_scoring = np.mean([s["time_at_goal"] for s in scoring_shifts])
        goals_for = len(scoring_shifts)
    else:
        avg_shift_scoring = 0
        avg_time_at_goal_scoring = 0
        goals_for = 0

    if scored_on_shifts:
        avg_shift_scored_on = np.mean([s["shift_length"] for s in scored_on_shifts])
        avg_time_at_goal_scored_on = np.mean([s["time_at_goal"] for s in scored_on_shifts])
        goals_against = len(scored_on_shifts)
    else:
        avg_shift_scored_on = 0
        avg_time_at_goal_scored_on = 0
        goals_against = 0

    pattern_data = {
        "player_id": player_id,
        "position": position,
        "goals_for_on_ice": goals_for,
        "goals_against_on_ice": goals_against,
        "avg_shift_length_scoring": avg_shift_scoring,
        "avg_shift_length_scored_on": avg_shift_scored_on,
        "avg_time_into_shift_scoring": avg_time_at_goal_scoring,
        "avg_time_into_shift_scored_on": avg_time_at_goal_scored_on,
        "goal_differential_on_ice": goals_for - goals_against,
    }
    
    shift_patterns.append(pattern_data)

# Process goalies separately from position data
goalie_data = []
for player_id, pos_data in player_positions.items():
    if pos_data['position'] == 'G':
        goalie_data.append({
            'player_id': player_id,
            'position': 'G',
            'avg_shift_length': pos_data['avg_shift_length'],
            'total_shifts': pos_data['total_shifts'],
            'avg_minutes_per_game': pos_data['avg_shift_length'] * pos_data['total_shifts'] / (60 * len(processed_games))
        })

# Create DataFrames
skater_df = pd.DataFrame(shift_patterns)
goalie_df = pd.DataFrame(goalie_data)

# Add shift efficiency metrics for skaters
skater_df["shift_length_differential"] = skater_df["avg_shift_length_scoring"] - skater_df["avg_shift_length_scored_on"]
skater_df["fatigue_factor_scoring"] = skater_df["avg_time_into_shift_scoring"] / skater_df["avg_shift_length_scoring"]
skater_df["fatigue_factor_scored_on"] = skater_df["avg_time_into_shift_scored_on"] / skater_df["avg_shift_length_scored_on"]

# Replace inf/nan with 0
skater_df = skater_df.replace([np.inf, -np.inf], 0).fillna(0)
goalie_df = goalie_df.fillna(0)

# Create output directory
Path("data/nhl/processed").mkdir(parents=True, exist_ok=True)

# Save separate files
skater_df.to_csv("data/nhl/processed/skater_shift_patterns.csv", index=False)
goalie_df.to_csv("data/nhl/processed/goalie_shift_patterns.csv", index=False)

print(f"\nCreated shift patterns for {len(skater_df)} skaters")
print(f"Average shift when scoring: {skater_df['avg_shift_length_scoring'].mean():.1f} seconds")
print(f"Average shift when scored on: {skater_df['avg_shift_length_scored_on'].mean():.1f} seconds")
print(f"Players with positive goal differential: {(skater_df['goal_differential_on_ice'] > 0).sum()}")

print(f"\nIdentified {len(goalie_df)} goalies")
print(f"Average goalie shift length: {goalie_df['avg_shift_length'].mean():.1f} seconds")

# Also save a combined file with is_goalie flag for backward compatibility
combined_df = pd.concat([
    skater_df.assign(is_goalie=False),
    goalie_df.assign(is_goalie=True, 
                     avg_shift_length_scoring=goalie_df['avg_shift_length'],
                     avg_shift_length_scored_on=goalie_df['avg_shift_length'])
], ignore_index=True)

combined_df.to_csv("data/nhl/processed/player_shift_patterns.csv", index=False)

print("\nDATA LEAK PREVENTION:")
print("- Goalies identified and separated based on shift length > 300s")
print("- Skater fatigue metrics calculated only for non-goalies")
print("- Goalie workload should be handled in build_goalie_workload.py")
print(f"- Files created: skater_shift_patterns.csv, goalie_shift_patterns.csv")