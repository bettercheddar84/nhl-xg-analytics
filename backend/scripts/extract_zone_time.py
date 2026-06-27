import json
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_zone_time(plays, goal_idx, goal_team_id):
    """Calculate offensive zone possession time before goal."""
    goal_play = plays[goal_idx]
    goal_time = parse_time(
        goal_play.get("timeInPeriod", "0:00"), goal_play.get("periodDescriptor", {}).get("number", 1)
    )

    zone_time = 0
    last_offensive_event = goal_time

    # Look back 60 seconds
    for i in range(goal_idx - 1, max(0, goal_idx - 100), -1):
        play = plays[i]
        play_time = parse_time(play.get("timeInPeriod", "0:00"), play.get("periodDescriptor", {}).get("number", 1))

        if goal_time - play_time > 60:
            break

        event_team = play.get("details", {}).get("eventOwnerTeamId")
        zone = play.get("details", {}).get("zoneCode")

        # Offensive zone event by scoring team
        if event_team == goal_team_id and zone == "O":
            zone_time += last_offensive_event - play_time
            last_offensive_event = play_time
        # Defensive zone event or neutral zone faceoff - reset
        elif zone in ["D", "N"]:
            last_offensive_event = play_time

    return zone_time


def parse_time(time_str, period):
    """Convert MM:SS to game seconds."""
    try:
        minutes, seconds = time_str.split(":")
        return (period - 1) * 1200 + int(minutes) * 60 + int(seconds)
    except (ValueError, AttributeError):
        return 0


def main():
    # Load goals
    goals_df = pd.read_csv("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")
    goals_df = goals_df[goals_df["is_goal"] == 1].copy()

    zone_times = []
    pbp_dir = Path("data/nhl/play_by_play")

    # Process available games
    for game_file in pbp_dir.glob("*.json"):
        game_id = int(game_file.stem)

        with open(game_file) as f:
            pbp = json.load(f)

        plays = pbp.get("plays", [])
        game_goals = goals_df[goals_df["game_id"] == game_id]

        for _, goal in game_goals.iterrows():
            # Find goal in plays
            goal_idx = None
            for idx, play in enumerate(plays):
                if (
                    play.get("typeDescKey") == "goal"
                    and play.get("details", {}).get("scoringPlayerId") == goal["shooter_id"]
                ):
                    goal_idx = idx
                    break

            if goal_idx:
                zone_time = calculate_zone_time(plays, goal_idx, goal["shooting_team_id"])
                zone_times.append(
                    {"game_id": game_id, "shooter_id": goal["shooter_id"], "offensive_zone_time": zone_time}
                )

    # Save
    df = pd.DataFrame(zone_times)
    df.to_csv("data/nhl/processed/offensive_zone_times.csv", index=False)
    logger.info(f"Extracted zone time for {len(df)} goals")
    logger.info(f"Average zone time before goal: {df['offensive_zone_time'].mean():.1f}s")


if __name__ == "__main__":
    main()
