# scripts/fetch_play_by_play.py
import json
import pandas as pd
from pathlib import Path
import time
from nhlpy import NHLClient
import logging
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def parse_time_to_seconds(time_str: str, period: int) -> int:
    """Convert MM:SS time string to total game seconds."""
    try:
        if isinstance(time_str, str) and ":" in time_str:
            minutes, seconds = time_str.split(":")
            return (period - 1) * 1200 + int(minutes) * 60 + int(seconds)
        return 0
    except (ValueError, AttributeError):
        return 0


def extract_passing_sequence(plays: List[Dict], goal_play_idx: int, goal_details: Dict) -> Dict:
    """Extract passing sequence leading to a goal."""
    passes = []
    total_pass_distance = 0
    goal_time = goal_details["game_seconds"]
    goal_team_id = goal_details.get("shooting_team_id")

    # Debug: Print nearby events
    logger.debug(f"\nAnalyzing goal at index {goal_play_idx}")
    for i in range(max(0, goal_play_idx - 5), min(len(plays), goal_play_idx + 1)):
        play = plays[i]
        event_type = play.get("typeDescKey", "unknown")
        event_team = play.get("details", {}).get("eventOwnerTeamId", "unknown")
        logger.debug(f"  [{i}] {event_type} by team {event_team}")

    # Look back through plays (up to 30 seconds or 50 events)
    for j in range(goal_play_idx - 1, max(0, goal_play_idx - 50), -1):
        prev_play = plays[j]
        prev_type = prev_play.get("typeDescKey", "").lower()
        prev_details = prev_play.get("details", {})

        # Calculate time of this event
        prev_period = prev_play.get("periodDescriptor", {}).get("number", 1)
        prev_time_str = prev_play.get("timeInPeriod", "0:00")
        prev_time = parse_time_to_seconds(prev_time_str, prev_period)

        # Stop if more than 30 seconds before goal
        if goal_time - prev_time > 30:
            break

        # Check for events that break possession
        if prev_type in ["takeaway", "giveaway", "blocked-shot", "faceoff", "stoppage"]:
            break

        # Check if it's the opposing team's event
        prev_team = prev_details.get("eventOwnerTeamId")
        if prev_team and goal_team_id and prev_team != goal_team_id:
            # Skip opponent events but don't break - they might have incomplete passes
            continue

        # Look for pass-like events (NHL API doesn't always use "pass" in typeDescKey)
        # Sometimes passes are recorded as zone entries, plays, or just have coordinates
        is_potential_pass = (
            "pass" in prev_type
            or prev_type in ["play", "zone-entry"]
            or (prev_details.get("xCoord") is not None and prev_details.get("playerId") is not None)
        )

        if is_potential_pass:
            # Try to get coordinates - API might use different field names
            x_start = prev_details.get("xCoord")
            y_start = prev_details.get("yCoord")

            # End coordinates might be in different fields
            x_end = (
                prev_details.get("xCoordOff")
                or prev_details.get("xCoordEnd")
                or prev_details.get("secondaryXCoord")
                or x_start
            )
            y_end = (
                prev_details.get("yCoordOff")
                or prev_details.get("yCoordEnd")
                or prev_details.get("secondaryYCoord")
                or y_start
            )

            # Calculate pass distance if we have valid coordinates
            distance = 0
            if x_start is not None and x_end is not None:
                distance = ((x_end - x_start) ** 2 + ((y_end or y_start) - (y_start or 0)) ** 2) ** 0.5
                total_pass_distance += distance

            passes.append(
                {
                    "player_id": prev_details.get("playerId"),
                    "time": prev_time,
                    "x_start": x_start,
                    "y_start": y_start,
                    "x_end": x_end,
                    "y_end": y_end,
                    "distance": distance,
                    "event_type": prev_type,
                }
            )

            logger.debug(f"    Found pass: {prev_type} at {prev_time_str}")

    # Calculate sequence metrics
    total_passes = len(passes)
    sequence_duration = goal_time - passes[-1]["time"] if passes else 0
    avg_pass_distance = total_pass_distance / total_passes if total_passes > 0 else 0

    # Identify pass types
    cross_ice_passes = 0
    forward_passes = 0

    for p in passes:
        if p["y_start"] is not None and p["y_end"] is not None:
            if abs(p["y_end"] - p["y_start"]) > 20:
                cross_ice_passes += 1
        if p["x_start"] is not None and p["x_end"] is not None:
            if p["x_end"] - p["x_start"] > 10:
                forward_passes += 1

    # Determine sequence type
    quick_strike = 1 if total_passes <= 2 else 0  # 0-2 passes = quick strike
    sustained_pressure = 1 if total_passes >= 5 and sequence_duration > 15 else 0

    return {
        "total_passes": total_passes,
        "sequence_duration": round(sequence_duration, 1),
        "avg_pass_distance": round(avg_pass_distance, 1),
        "total_pass_distance": round(total_pass_distance, 1),
        "cross_ice_passes": cross_ice_passes,
        "forward_passes": forward_passes,
        "passes_per_second": round(total_passes / sequence_duration, 3) if sequence_duration > 0 else 0,
        "quick_strike": quick_strike,
        "sustained_pressure": sustained_pressure,
    }


def main():
    """Main execution function."""
    try:
        # Create directories
        Path("data/nhl/play_by_play").mkdir(parents=True, exist_ok=True)
        Path("data/nhl/processed").mkdir(parents=True, exist_ok=True)

        # Load existing shots to get game IDs
        logger.info("Loading shots data...")
        shots_df = pd.read_csv("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")
        goals_df = shots_df[shots_df["is_goal"] == 1].copy()

        # Get unique game IDs that have goals
        game_ids = goals_df["game_id"].unique()
        logger.info(f"Found {len(game_ids)} games with goals")

        # Process games
        client = NHLClient()
        passing_data = []
        games_to_process = len(game_ids)

        for i, game_id in enumerate(game_ids[:games_to_process]):
            if i % 10 == 0:
                logger.info(f"Processing game {i}/{games_to_process}")
                time.sleep(1)  # Rate limiting

            try:
                # Check if we already have this game's data
                pbp_file = Path(f"data/nhl/play_by_play/{game_id}.json")

                if pbp_file.exists():
                    logger.debug(f"Loading existing play-by-play for game {game_id}")
                    with open(pbp_file) as f:
                        pbp = json.load(f)
                else:
                    # Fetch play-by-play
                    pbp = client.game_center.play_by_play(str(game_id))

                    # Save raw data
                    with open(pbp_file, "w") as f:
                        json.dump(pbp, f)

                # Extract passing sequences for goals
                plays = pbp.get("plays", [])

                # Find all goals in this game
                game_goals = goals_df[goals_df["game_id"] == game_id]

                for _, goal in game_goals.iterrows():
                    goal_time = goal["game_seconds"]
                    goal_period = goal["period"]

                    # Find the goal play in play-by-play
                    goal_play_idx = None

                    for idx, play in enumerate(plays):
                        if (
                            play.get("typeDescKey") == "goal"
                            and play.get("periodDescriptor", {}).get("number") == goal_period
                        ):

                            # Convert play time to seconds
                            play_time_str = play.get("timeInPeriod", "0:00")
                            play_time = parse_time_to_seconds(play_time_str, goal_period)

                            # Check if times match (within 5 seconds)
                            if abs(play_time - goal_time) < 5:
                                goal_play_idx = idx
                                break

                    if goal_play_idx is None:
                        logger.warning(
                            f"Could not find goal play for {goal['shooter_name']} " f"at {goal_time}s in game {game_id}"
                        )
                        # Add empty sequence
                        passing_data.append(
                            {
                                "game_id": game_id,
                                "goal_time": goal_time,
                                "shooter_id": goal["shooter_id"],
                                "total_passes": 0,
                                "sequence_duration": 0,
                                "avg_pass_distance": 0,
                                "total_pass_distance": 0,
                                "cross_ice_passes": 0,
                                "forward_passes": 0,
                                "passes_per_second": 0,
                                "quick_strike": 1,  # Unassisted = quick strike
                                "sustained_pressure": 0,
                            }
                        )
                        continue

                    # Extract passing sequence
                    sequence_data = extract_passing_sequence(plays, goal_play_idx, goal.to_dict())

                    passing_data.append(
                        {"game_id": game_id, "goal_time": goal_time, "shooter_id": goal["shooter_id"], **sequence_data}
                    )

                    if sequence_data["total_passes"] > 0:
                        logger.debug(
                            f"Goal by {goal['shooter_name']}: "
                            f"{sequence_data['total_passes']} passes in "
                            f"{sequence_data['sequence_duration']}s"
                        )

            except Exception as e:
                logger.error(f"Error processing game {game_id}: {e}")
                continue

        # Create DataFrame and save
        df = pd.DataFrame(passing_data)
        output_file = Path("data/nhl/processed/passing_sequences.csv")
        df.to_csv(output_file, index=False)

        logger.info(f"\nCreated passing data for {len(df)} goals")
        logger.info(f"Average passes per goal: {df['total_passes'].mean():.2f}")
        logger.info(
            f"Quick strike goals (≤2 passes): {df['quick_strike'].sum()} "
            f"({df['quick_strike'].sum() / len(df) * 100:.1f}%)"
        )
        logger.info(
            f"Sustained pressure goals (≥5 passes): {df['sustained_pressure'].sum()} "
            f"({df['sustained_pressure'].sum() / len(df) * 100:.1f}%)"
        )
        logger.info(
            f"Unassisted goals (0 passes): {len(df[df['total_passes'] == 0])} "
            f"({len(df[df['total_passes'] == 0]) / len(df) * 100:.1f}%)"
        )

        # Distribution of passes
        logger.info("\nPass distribution:")
        pass_counts = df["total_passes"].value_counts().sort_index()
        for passes, count in pass_counts.head(10).items():
            logger.info(f"  {passes} passes: {count} goals ({count / len(df) * 100:.1f}%)")

        return df

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    # Set logging level from environment variable if needed
    import os

    if os.getenv("DEBUG"):
        logging.getLogger().setLevel(logging.DEBUG)

    main()
