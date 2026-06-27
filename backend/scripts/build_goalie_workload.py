import pandas as pd
from pathlib import Path
import logging
from typing import List
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def validate_columns(df: pd.DataFrame, required_cols: List[str]) -> None:
    """Validate that required columns exist in dataframe."""
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")


def classify_shot_danger(row: pd.Series) -> str:
    """Classify shot danger based on location and type."""
    distance = row.get("shot_distance", 0)
    angle = abs(row.get("shot_angle", 0))

    # High danger: close shots with good angle
    if distance < 15 and angle > 70:
        return "high"
    # Low danger: far shots or bad angles
    elif distance > 40 or angle < 20:
        return "low"
    else:
        return "medium"


def calculate_workload_metrics(shots_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate goalie workload metrics for all shots."""
    logger.info("Calculating goalie workload metrics for all shots...")

    # Sort by game and time
    shots_df = shots_df.sort_values(["game_id", "game_seconds"]).reset_index(drop=True)

    # Initialize tracking dictionaries
    goalie_trackers = {}

    # Initialize new columns
    workload_cols = [
        "saves_last_10s",
        "saves_last_30s",
        "saves_last_60s",
        "shots_faced_period",
        "shots_faced_game",
        "shot_rate_2min",
        "time_since_last_shot",
        "consecutive_saves",
        "save_pct_last_10",
        "danger_zone",
        "high_danger_save_pct",
        "goalie_cold_start",
        "fatigue_score",
    ]

    for col in workload_cols:
        if col == "danger_zone":
            shots_df[col] = ""  # String column
        else:
            shots_df[col] = 0.0

    # Process each shot
    for idx in range(len(shots_df)):
        if idx % 10000 == 0:
            logger.info(f"Processing shot {idx:,}/{len(shots_df):,} ({idx / len(shots_df) * 100:.1f}%)")

        row = shots_df.iloc[idx]
        game_id = row["game_id"]
        goalie_id = row["goalie_id"]
        shot_time = row["game_seconds"]
        period = int(row["period"]) if pd.notna(row["period"]) else 1
        is_goal = row["is_goal"]

        # Skip if no goalie or invalid period
        if pd.isna(goalie_id):
            continue

        # Skip overtime/shootout periods
        if period not in [1, 2, 3, 4]:
            continue

        # Initialize tracker for new goalie/game combination
        key = f"{game_id}_{goalie_id}"
        if key not in goalie_trackers:
            goalie_trackers[key] = {
                "shot_times": [],
                "shot_results": [],  # 0 for save, 1 for goal
                "period_shots": {1: 0, 2: 0, 3: 0, 4: 0},
                "consecutive_saves": 0,
                "last_shot_time": 0,
                "danger_shots": {
                    "high": {"shots": 0, "saves": 0},
                    "medium": {"shots": 0, "saves": 0},
                    "low": {"shots": 0, "saves": 0},
                },
            }

        tracker = goalie_trackers[key]

        # Classify danger
        danger = classify_shot_danger(row)
        shots_df.at[idx, "danger_zone"] = danger

        # Time since last shot
        if tracker["last_shot_time"] > 0:
            time_since = shot_time - tracker["last_shot_time"]
            shots_df.at[idx, "time_since_last_shot"] = time_since
            shots_df.at[idx, "goalie_cold_start"] = int(time_since > 300)  # 5+ minutes
        else:
            shots_df.at[idx, "time_since_last_shot"] = shot_time
            shots_df.at[idx, "goalie_cold_start"] = 1

        # Calculate saves in time windows
        recent_times = [t for t in tracker["shot_times"] if shot_time - t <= 60]
        recent_results = tracker["shot_results"][-len(recent_times) :]

        saves_60s = sum(1 for r in recent_results if r == 0)
        saves_30s = sum(1 for i, t in enumerate(recent_times) if shot_time - t <= 30 and recent_results[i] == 0)
        saves_10s = sum(1 for i, t in enumerate(recent_times) if shot_time - t <= 10 and recent_results[i] == 0)

        shots_df.at[idx, "saves_last_10s"] = saves_10s
        shots_df.at[idx, "saves_last_30s"] = saves_30s
        shots_df.at[idx, "saves_last_60s"] = saves_60s

        # Shot rate in last 2 minutes
        recent_2min = [t for t in tracker["shot_times"] if shot_time - t <= 120]
        shot_rate = len(recent_2min) / 2.0 if shot_time >= 120 else len(recent_2min) / (shot_time / 60.0)
        shots_df.at[idx, "shot_rate_2min"] = round(shot_rate, 3)

        # Period shots
        tracker["period_shots"][period] += 1
        shots_df.at[idx, "shots_faced_period"] = tracker["period_shots"][period]
        shots_df.at[idx, "shots_faced_game"] = len(tracker["shot_times"]) + 1

        # Save percentage on last 10 shots
        if len(tracker["shot_results"]) >= 10:
            last_10_results = tracker["shot_results"][-10:]
            save_pct = sum(1 for r in last_10_results if r == 0) / 10
            shots_df.at[idx, "save_pct_last_10"] = save_pct
        elif len(tracker["shot_results"]) > 0:
            save_pct = sum(1 for r in tracker["shot_results"] if r == 0) / len(tracker["shot_results"])
            shots_df.at[idx, "save_pct_last_10"] = save_pct

        # High danger save percentage
        danger_stats = tracker["danger_shots"][danger]
        if danger_stats["shots"] > 0:
            shots_df.at[idx, "high_danger_save_pct"] = danger_stats["saves"] / danger_stats["shots"]

        # Consecutive saves
        shots_df.at[idx, "consecutive_saves"] = tracker["consecutive_saves"]

        # Fatigue score (weighted combination)
        fatigue = saves_10s * 0.5 + saves_30s * 0.3 + saves_60s * 0.2 + shots_df.at[idx, "shots_faced_period"] * 0.05
        shots_df.at[idx, "fatigue_score"] = round(fatigue, 3)

        # Update tracker
        tracker["shot_times"].append(shot_time)
        tracker["shot_results"].append(int(is_goal))
        tracker["last_shot_time"] = shot_time
        tracker["danger_shots"][danger]["shots"] += 1

        if is_goal:
            tracker["consecutive_saves"] = 0
        else:
            tracker["consecutive_saves"] += 1
            tracker["danger_shots"][danger]["saves"] += 1

    return shots_df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add additional derived features."""
    # High intensity indicator
    df["high_intensity_saves"] = (df["saves_last_30s"] >= 3).astype(int)

    # Rest period indicator
    df["rest_period"] = (df["time_since_last_shot"] > 120).astype(int)

    # Sustained pressure
    df["sustained_pressure"] = (df["shot_rate_2min"] > 0.5).astype(int)

    # Shooter vs goalie quality differential (placeholder - needs player data)
    df["goalie_quality_rating"] = df["save_pct_last_10"]  # Simplified for now

    return df


def main():
    """Main execution function."""
    try:
        # Define file paths
        input_file = Path("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")
        output_dir = Path("data/nhl/processed")
        output_file = output_dir / "goalie_workload_all_shots.csv"

        # Check if input file exists
        if not input_file.exists():
            logger.error(f"Input file not found: {input_file}")
            sys.exit(1)

        logger.info("Loading shots data...")
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df):,} shots")

        # Validate required columns
        required_cols = [
            "game_id",
            "goalie_id",
            "game_seconds",
            "is_goal",
            "event_type",
            "shot_distance",
            "shot_angle",
            "period",
        ]
        validate_columns(df, required_cols)

        # Convert to numeric
        df["game_seconds"] = pd.to_numeric(df["game_seconds"], errors="coerce")
        df["goalie_id"] = pd.to_numeric(df["goalie_id"], errors="coerce")
        df["shot_distance"] = pd.to_numeric(df["shot_distance"], errors="coerce")
        df["shot_angle"] = pd.to_numeric(df["shot_angle"], errors="coerce")
        df["period"] = pd.to_numeric(df["period"], errors="coerce")

        # Drop invalid rows
        df = df.dropna(subset=["game_seconds"])

        # Filter to shots on goal and goals only
        valid_events = ["shot-on-goal", "goal"]
        shots_df = df[df["event_type"].isin(valid_events)].copy()
        logger.info(f"Filtered to {len(shots_df):,} shots on goal and goals")

        # Calculate workload metrics
        shots_df = calculate_workload_metrics(shots_df)

        # Add derived features
        logger.info("Adding derived features...")
        shots_df = add_derived_features(shots_df)

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save results
        shots_df.to_csv(output_file, index=False)
        logger.info(f"Saved goalie workload data to {output_file}")

        # Print summary statistics
        logger.info("\n=== Summary Statistics ===")
        logger.info(f"Total shots analyzed: {len(shots_df):,}")
        logger.info(f"Shots with valid goalie data: {shots_df['goalie_id'].notna().sum():,}")
        logger.info(f"Average fatigue score: {shots_df['fatigue_score'].mean():.2f}")
        logger.info(f"Shots after high intensity: {shots_df['high_intensity_saves'].sum():,}")
        logger.info(f"Cold start shots: {shots_df['goalie_cold_start'].sum():,}")
        logger.info(f"High danger shots: {(shots_df['danger_zone'] == 'high').sum():,}")

        # Feature list for reference
        goalie_features = [
            col
            for col in shots_df.columns
            if any(x in col for x in ["save", "goalie", "fatigue", "consecutive", "danger", "intensity"])
        ]
        logger.info(f"\nCreated {len(goalie_features)} goalie features: {goalie_features}")

        return shots_df

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    main()
