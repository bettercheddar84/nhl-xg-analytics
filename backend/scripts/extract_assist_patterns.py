import json
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_pre_goal_sequences(plays, goal_idx, window_seconds=30):
    """Extract all events in the window before a goal."""
    goal_play = plays[goal_idx]
    goal_time = parse_time(
        goal_play.get("timeInPeriod", "0:00"), goal_play.get("periodDescriptor", {}).get("number", 1)
    )

    pre_goal_events = []

    # Look back through events
    for i in range(goal_idx - 1, max(0, goal_idx - 50), -1):
        play = plays[i]
        play_time = parse_time(play.get("timeInPeriod", "0:00"), play.get("periodDescriptor", {}).get("number", 1))

        time_diff = goal_time - play_time
        if time_diff > window_seconds:
            break

        event_type = play.get("typeDescKey", "")
        if event_type in ["shot-on-goal", "missed-shot", "blocked-shot", "faceoff", "hit", "giveaway", "takeaway"]:
            pre_goal_events.append(
                {
                    "event_type": event_type,
                    "time_before_goal": time_diff,
                    "player_id": play.get("details", {}).get("playerId"),
                    "x_coord": play.get("details", {}).get("xCoord"),
                    "y_coord": play.get("details", {}).get("yCoord"),
                    "zone": play.get("details", {}).get("zoneCode"),
                }
            )

    return pre_goal_events


def calculate_passing_features(goal_data, pre_goal_events):
    """Calculate passing-related features from pre-goal events."""
    features = {
        "game_id": goal_data["game_id"],
        "goal_time": goal_data["goal_time"],
        "shooter_id": goal_data["shooter_id"],
        "assist1_id": goal_data.get("assist1_id"),
        "assist2_id": goal_data.get("assist2_id"),
        # Event counts in 30s window
        "shots_before_goal": sum(1 for e in pre_goal_events if "shot" in e["event_type"]),
        "hits_before_goal": sum(1 for e in pre_goal_events if e["event_type"] == "hit"),
        "giveaways_before_goal": sum(1 for e in pre_goal_events if e["event_type"] == "giveaway"),
        "takeaways_before_goal": sum(1 for e in pre_goal_events if e["event_type"] == "takeaway"),
        # Sequence timing
        "sequence_duration": max([e["time_before_goal"] for e in pre_goal_events], default=0),
        "events_per_second": len(pre_goal_events)
        / max(1, max([e["time_before_goal"] for e in pre_goal_events], default=1)),
        # Quick strike detection
        "quick_strike": 1 if len(pre_goal_events) < 3 else 0,
        "off_faceoff": (
            1 if any(e["event_type"] == "faceoff" and e["time_before_goal"] < 10 for e in pre_goal_events) else 0
        ),
        # Zone progression (simplified)
        "offensive_zone_events": sum(1 for e in pre_goal_events if e.get("zone") == "O"),
        "neutral_zone_events": sum(1 for e in pre_goal_events if e.get("zone") == "N"),
        # Rebound detection
        "is_rebound": (
            1
            if any(
                e["event_type"] in ["shot-on-goal", "missed-shot"] and e["time_before_goal"] < 3
                for e in pre_goal_events
            )
            else 0
        ),
        # Sustained pressure
        "sustained_pressure": 1 if sum(1 for e in pre_goal_events if "shot" in e["event_type"]) >= 3 else 0,
    }

    return features


def parse_time(time_str, period):
    """Convert MM:SS to game seconds."""
    try:
        if not time_str or time_str == "0:00":
            return 0
        minutes, seconds = time_str.split(":")
        return (period - 1) * 1200 + int(minutes) * 60 + int(seconds)
    except (ValueError, AttributeError):
        return 0


def main():
    # Load goals from shots data
    shots_df = pd.read_csv("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")
    goals_df = shots_df[shots_df["is_goal"] == 1].copy()

    logger.info(f"Processing {len(goals_df)} goals")

    all_features = []
    pbp_dir = Path("data/nhl/play_by_play")

    # Get unique game IDs from goals
    game_ids = goals_df["game_id"].unique()
    logger.info(f"Found {len(game_ids)} unique games with goals")

    processed_games = 0

    for game_id in game_ids:
        game_file = pbp_dir / f"{game_id}.json"

        if not game_file.exists():
            continue

        with open(game_file) as f:
            pbp = json.load(f)

        plays = pbp.get("plays", [])
        game_goals = goals_df[goals_df["game_id"] == game_id]

        for _, goal in game_goals.iterrows():
            # Find this goal in the play-by-play
            goal_idx = None
            goal_details = None

            for idx, play in enumerate(plays):
                if (
                    play.get("typeDescKey") == "goal"
                    and play.get("details", {}).get("scoringPlayerId") == goal["shooter_id"]
                ):

                    # Verify it's the right goal by checking time
                    play_time = parse_time(
                        play.get("timeInPeriod", "0:00"), play.get("periodDescriptor", {}).get("number", 1)
                    )

                    if abs(play_time - goal["game_seconds"]) < 5:  # Within 5 seconds
                        goal_idx = idx
                        goal_details = play.get("details", {})
                        break

            if goal_idx is not None and goal_details is not None:
                # Extract pre-goal sequence
                pre_goal_events = extract_pre_goal_sequences(plays, goal_idx)

                # Build goal data with assists
                goal_data = {
                    "game_id": game_id,
                    "goal_time": goal["game_seconds"],  # Use game_seconds
                    "shooter_id": goal["shooter_id"],
                    "assist1_id": goal_details.get("assist1PlayerId"),
                    "assist2_id": goal_details.get("assist2PlayerId"),
                }

                # Calculate features
                features = calculate_passing_features(goal_data, pre_goal_events)
                all_features.append(features)

        processed_games += 1
        if processed_games % 100 == 0:
            logger.info(f"Processed {processed_games} games")

    # Save results
    df = pd.DataFrame(all_features)
    df.to_csv("data/nhl/processed/goal_sequences_fixed.csv", index=False)

    logger.info(f"Extracted features for {len(df)} goals")
    logger.info(f"Goals with assists: {df['assist1_id'].notna().sum()}")
    logger.info(f"Goals with 2 assists: {df['assist2_id'].notna().sum()}")
    logger.info(f"Quick strikes: {df['quick_strike'].sum()}")
    logger.info(f"Rebounds: {df['is_rebound'].sum()}")
    logger.info(f"Off faceoff: {df['off_faceoff'].sum()}")


if __name__ == "__main__":
    main()
