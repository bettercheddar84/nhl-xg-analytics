"""
Extract comprehensive shot consequences for every shot
Tracks what happens after shots: rebounds, fast breaks, zone clears, etc.
This is the key differentiator for advanced xG modeling
"""

import pandas as pd
import json
from typing import Dict, List
import glob
from tqdm import tqdm


def load_play_by_play_data(game_id: str) -> List[Dict]:
    """Load play-by-play data for a specific game"""
    try:
        with open(f"data/nhl/play_by_play/{game_id}.json", "r") as f:
            data = json.load(f)
        return data.get("plays", [])
    except FileNotFoundError:
        return []


def extract_event_chain(plays: List[Dict], shot_time: int, window: int = 15) -> Dict:
    """Extract chain of events after a shot within time window"""

    shot_idx = None
    for i, play in enumerate(plays):
        if play.get("timeInPeriod") == shot_time:
            shot_idx = i
            break

    if shot_idx is None:
        return {}

    # Get events in next 15 seconds
    future_events = []
    shot_period = plays[shot_idx].get("period")

    for i in range(shot_idx + 1, min(shot_idx + 50, len(plays))):
        event = plays[i]
        # Check if still in same period
        if event.get("period") != shot_period:
            break

        # Calculate time difference
        time_diff = event.get("timeInPeriod", 0) - shot_time
        if time_diff > window:
            break

        future_events.append(
            {
                "type": event.get("typeDescKey"),
                "time_since_shot": time_diff,
                "team": event.get("eventOwnerTeamId"),
                "zone": event.get("zoneCode"),
                "details": event.get("details", {}),
            }
        )

    return analyze_event_chain(future_events, plays[shot_idx])


def analyze_event_chain(events: List[Dict], shot_event: Dict) -> Dict:
    """Analyze the chain of events to extract meaningful consequences"""

    shooting_team = shot_event.get("eventOwnerTeamId")
    shot_zone = shot_event.get("zoneCode", "O")  # Offensive zone

    consequences = {
        "zone_cleared": False,
        "zone_clear_time": None,
        "opponent_shot_time": None,
        "opponent_shot_danger": None,
        "rebound_shot_time": None,
        "rebound_shot_team": None,
        "possession_changes": 0,
        "offensive_zone_time_after": 0,
        "led_to_penalty": False,
        "led_to_goal_for": False,
        "led_to_goal_against": False,
        "next_whistle_time": None,
        "next_whistle_reason": None,
    }

    last_event_time = 0
    current_zone = shot_zone
    possession_team = shooting_team

    for event in events:
        event_type = event["type"]
        event_team = event.get("team")
        event_time = event["time_since_shot"]

        # Track zone changes
        if event.get("zone") and event["zone"] != current_zone:
            if current_zone == "O" and not consequences["zone_cleared"]:
                consequences["zone_cleared"] = True
                consequences["zone_clear_time"] = event_time
            current_zone = event["zone"]

        # Track possession changes
        if event_team and event_team != possession_team:
            consequences["possession_changes"] += 1
            possession_team = event_team

        # Track opponent shots
        if event_type in ["shot-on-goal", "missed-shot", "blocked-shot"] and event_team != shooting_team:
            if consequences["opponent_shot_time"] is None:
                consequences["opponent_shot_time"] = event_time
                # Estimate danger based on event details
                details = event.get("details", {})
                shot_type = details.get("shotType", "unknown")
                consequences["opponent_shot_danger"] = estimate_shot_danger(shot_type, details)

        # Track rebounds
        if event_type in ["shot-on-goal", "goal"] and event_time < 3:
            consequences["rebound_shot_time"] = event_time
            consequences["rebound_shot_team"] = event_team

        # Track goals
        if event_type == "goal":
            if event_team == shooting_team:
                consequences["led_to_goal_for"] = True
            else:
                consequences["led_to_goal_against"] = True

        # Track penalties
        if event_type == "penalty":
            consequences["led_to_penalty"] = True

        # Track whistles
        if event_type in ["stoppage", "penalty", "goal"] and consequences["next_whistle_time"] is None:
            consequences["next_whistle_time"] = event_time
            consequences["next_whistle_reason"] = event_type

        # Track offensive zone time
        if current_zone == "O" and possession_team == shooting_team:
            consequences["offensive_zone_time_after"] += event_time - last_event_time

        last_event_time = event_time

    return consequences


def estimate_shot_danger(shot_type: str, details: Dict) -> str:
    """Estimate danger level of a shot based on type and details"""

    high_danger_types = ["deflection", "tip-in", "wrap-around"]
    low_danger_types = ["slap-shot", "wrist-shot"]

    if shot_type in high_danger_types:
        return "high"
    elif shot_type in low_danger_types:
        # Check for additional context
        if details.get("xCoord", 100) < 25:  # Close to net
            return "medium"
        return "low"
    return "medium"


def calculate_shot_value_metrics(shot_df: pd.DataFrame, consequences_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate expanded shot value metrics"""

    # Merge consequences with shots
    enhanced_df = shot_df.merge(consequences_df, on=["game_id", "shot_time"], how="left")

    # Calculate shot value components
    enhanced_df["rebound_value"] = 0
    enhanced_df.loc[enhanced_df["rebound_shot_team"] == enhanced_df["shooting_team"], "rebound_value"] = 0.15

    enhanced_df["fast_break_cost"] = 0
    enhanced_df.loc[
        (enhanced_df["opponent_shot_time"] < 10) & (enhanced_df["opponent_shot_danger"].isin(["high", "medium"])),
        "fast_break_cost",
    ] = -0.20

    enhanced_df["possession_value"] = enhanced_df["offensive_zone_time_after"] / 30  # Normalize

    # Calculate total shot value
    enhanced_df["expanded_shot_value"] = (
        enhanced_df["is_goal"]
        + enhanced_df["rebound_value"]
        + enhanced_df["fast_break_cost"]
        + enhanced_df["possession_value"] * 0.1
    )

    # Add specific risk metrics
    enhanced_df["creates_odd_man_rush"] = (
        (enhanced_df["opponent_shot_time"] < 5) & (enhanced_df["possession_changes"] <= 2)
    ).astype(int)

    enhanced_df["maintains_pressure"] = (enhanced_df["offensive_zone_time_after"] > 10).astype(int)

    return enhanced_df


def process_all_games(shots_df: pd.DataFrame) -> pd.DataFrame:
    """Process all games to extract shot consequences"""

    all_consequences = []
    games = shots_df["game_id"].unique()

    print(f"Processing {len(games)} games...")

    for game_id in tqdm(games):
        # Load play-by-play data
        plays = load_play_by_play_data(game_id)
        if not plays:
            continue

        # Get shots from this game
        game_shots = shots_df[shots_df["game_id"] == game_id]

        for _, shot in game_shots.iterrows():
            consequences = extract_event_chain(plays, shot["time_in_period"], window=15)

            consequences["game_id"] = game_id
            consequences["shot_time"] = shot["game_seconds"]
            consequences["shot_type"] = shot["shot_type"]
            consequences["shot_result"] = "goal" if shot["is_goal"] else "save"

            all_consequences.append(consequences)

    return pd.DataFrame(all_consequences)


def create_risk_profiles(enhanced_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create player and team risk profiles based on shot consequences"""

    # Player risk profiles
    player_risk = (
        enhanced_df.groupby("shooter_id")
        .agg(
            {
                "creates_odd_man_rush": "mean",
                "fast_break_cost": "mean",
                "rebound_value": "mean",
                "maintains_pressure": "mean",
                "expanded_shot_value": "mean",
            }
        )
        .round(3)
    )

    player_risk["risk_rating"] = player_risk["creates_odd_man_rush"] * -1 + player_risk["fast_break_cost"] * 2

    player_risk["shot_selection_quality"] = player_risk["expanded_shot_value"] - player_risk["risk_rating"]

    # Team risk profiles
    team_risk = (
        enhanced_df.groupby("shooting_team")
        .agg(
            {
                "zone_cleared": "mean",
                "zone_clear_time": "mean",
                "opponent_shot_time": "mean",
                "possession_changes": "mean",
            }
        )
        .round(3)
    )

    return player_risk, team_risk


def main():
    """Main processing pipeline"""

    print("Loading shot data...")
    shots_df = pd.read_csv("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")

    # Filter to games we have play-by-play data for
    available_games = [f.split("/")[-1].replace(".json", "") for f in glob.glob("data/nhl/play_by_play/*.json")]
    shots_df = shots_df[shots_df["game_id"].astype(str).isin(available_games)]

    print(f"Processing {len(shots_df)} shots from {len(available_games)} games...")

    # Extract consequences for all shots
    consequences_df = process_all_games(shots_df)

    # Save raw consequences
    consequences_df.to_csv("data/nhl/processed/shot_consequences_all.csv", index=False)

    # Calculate enhanced metrics
    enhanced_df = calculate_shot_value_metrics(shots_df, consequences_df)

    # Create risk profiles
    player_risk, team_risk = create_risk_profiles(enhanced_df)

    # Save results
    enhanced_df.to_csv("data/nhl/processed/shots_with_consequences.csv", index=False)
    player_risk.to_csv("data/nhl/processed/player_shot_risk_profiles.csv")
    team_risk.to_csv("data/nhl/processed/team_shot_risk_profiles.csv")

    # Print summary statistics
    print("\nShot Consequence Summary:")
    print(f"Shots leading to opponent shot within 10s: {(enhanced_df['opponent_shot_time'] < 10).mean():.1%}")
    print(f"Shots creating odd-man rushes: {enhanced_df['creates_odd_man_rush'].mean():.1%}")
    print(f"Shots maintaining offensive pressure: {enhanced_df['maintains_pressure'].mean():.1%}")
    print(f"Average expanded shot value: {enhanced_df['expanded_shot_value'].mean():.3f}")

    # Show high-risk shooters
    print("\nHighest Risk Shooters (creates fast breaks):")
    high_risk = player_risk.nlargest(10, "creates_odd_man_rush")
    print(high_risk[["creates_odd_man_rush", "fast_break_cost", "shot_selection_quality"]])

    # Show best shot selection
    print("\nBest Shot Selection (value vs risk):")
    best_selection = player_risk.nlargest(10, "shot_selection_quality")
    print(best_selection[["shot_selection_quality", "expanded_shot_value", "risk_rating"]])


if __name__ == "__main__":
    main()
