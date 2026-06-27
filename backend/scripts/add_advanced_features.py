import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_royal_road_pass(df):
    """
    Detect cross-slot passes (royal road passes).
    These are passes that cross from one side of the ice to the other
    through the slot area, creating high-danger scoring chances.
    """
    # Check if pass crossed the center line (x coordinates have opposite signs)
    crossed_center = df["prev_event_x"] * df["x_coord"] < 0

    # Check if pass went through the slot (y coordinate near center)
    through_slot = df["prev_event_y"].abs() < 20

    # Royal road pass is when both conditions are met
    df["royal_road_pass"] = (crossed_center & through_slot).astype(int)

    # Also calculate the pass angle change
    df["pass_angle_change"] = (
        np.abs(np.arctan2(df["y_coord"], df["x_coord"]) - np.arctan2(df["prev_event_y"], df["prev_event_x"]))
        * 180
        / np.pi
    )

    return df


def calculate_momentum_features(df):
    """
    Calculate game momentum indicators.
    Requires sorting by game_id and time first.
    """
    # Sort by game and time
    df = df.sort_values(["game_id", "game_seconds"])

    # Calculate rolling windows per game
    for window_seconds in [60, 300, 600]:  # 1min, 5min, 10min
        window_name = f"{window_seconds // 60}min"

        # Goals in last X minutes
        df[f"goals_last_{window_name}"] = df.groupby("game_id")["is_goal"].transform(
            lambda x: x.rolling(window=window_seconds, min_periods=1).sum()
        )

        # Shots in last X minutes (momentum indicator)
        df[f"shots_last_{window_name}"] = df.groupby("game_id")["is_goal"].transform(
            lambda x: x.rolling(window=window_seconds, min_periods=1).count()
        )

    # Shot differential momentum (team's shots vs opponent's in last 5 min)
    # This would require team-specific grouping
    df["shot_momentum_ratio"] = df["shots_last_5min"] / df["shots_last_5min"].shift(1).fillna(1)

    return df


def calculate_rush_quality(df):
    """
    Enhanced rush detection and quality scoring.
    """
    # Use existing rush flag but add quality metrics
    if "is_rush" in df.columns:
        # Speed-weighted rush quality
        if "speed_from_prev" in df.columns:
            df["rush_quality_score"] = df["is_rush"] * df["speed_from_prev"] / 30.0  # Normalize to 0-1
        else:
            df["rush_quality_score"] = df["is_rush"].astype(float)

        # Zone entry time for rushes
        if "time_since_zone_entry" in df.columns:
            df["quick_zone_to_shot"] = ((df["time_since_zone_entry"] < 5) & (df["time_since_zone_entry"] > 0)).astype(
                int
            )

    return df


def calculate_shot_danger_zone(df):
    """
    Create detailed danger zones beyond just high/medium/low.
    """
    # Define danger zones based on location
    df["in_slot"] = ((df["x_coord"].abs() < 30) & (df["y_coord"].abs() < 20)).astype(int)

    df["in_crease"] = ((df["x_coord"] > 80) & (df["x_coord"] < 89) & (df["y_coord"].abs() < 10)).astype(int)

    df["from_point"] = ((df["x_coord"] < 30) & (df["y_coord"].abs() > 30)).astype(int)

    # Combine with angle for danger score
    df["location_danger_score"] = (
        df["in_crease"] * 0.9
        + df["in_slot"] * 0.7
        + (1 - df["from_point"]) * 0.3
        + (df["shot_angle"] > 30).astype(int) * 0.2
    )

    return df


def calculate_pre_shot_pressure(df):
    """
    Estimate defensive pressure based on pre-shot events.
    """
    # Quick shots after offensive events suggest less pressure
    df["low_pressure_shot"] = (
        (df["time_since_prev_event"] < 2) & (df["prev_event_type"].isin(["shot-on-goal", "missed-shot", "faceoff"]))
    ).astype(int)

    # Shots after defensive events suggest more pressure
    df["high_pressure_shot"] = (
        (df["time_since_prev_event"] < 5) & (df["prev_event_type"].isin(["blocked-shot", "takeaway"]))
    ).astype(int)

    return df


def main():
    logger.info("Adding advanced features to training data...")

    # Load ALL shots data
    shots_df = pd.read_csv("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")

    # Load the goal sequences with verified assists
    goals_df = pd.read_csv("data/nhl/processed/goal_sequences_fixed.csv")

    # Merge assists data into shots (only goals will have assist info)
    df = pd.merge(
        shots_df,
        goals_df[
            [
                "game_id",
                "shooter_id",
                "goal_time",
                "assist1_id",
                "assist2_id",
                "shots_before_goal",
                "hits_before_goal",
                "sequence_duration",
                "quick_strike",
                "off_faceoff",
                "offensive_zone_events",
                "is_rebound",
                "sustained_pressure",
            ]
        ],
        left_on=["game_id", "shooter_id", "game_seconds"],
        right_on=["game_id", "shooter_id", "goal_time"],
        how="left",
    )

    # Drop duplicate goal_time column
    df = df.drop(columns=["goal_time"])

    # Rename assist columns if they have suffixes
    if "assist1_id_y" in df.columns:
        df = df.rename(columns={"assist1_id_y": "assist1_id_from_pbp", "assist2_id_y": "assist2_id_from_pbp"})

    initial_shape = df.shape
    logger.info(f"Loaded {initial_shape[0]} rows with {initial_shape[1]} columns")
    assist_col = "assist1_id_from_pbp" if "assist1_id_from_pbp" in df.columns else "assist1_id"
    logger.info(
        f"Found {df[assist_col].notna().sum() if assist_col in df.columns else 0} shots with assist data (goals)"
    )

    # Apply feature engineering
    logger.info("Calculating royal road passes...")
    df = calculate_royal_road_pass(df)

    logger.info("Calculating momentum features...")
    df = calculate_momentum_features(df)

    logger.info("Calculating rush quality...")
    df = calculate_rush_quality(df)

    logger.info("Calculating shot danger zones...")
    df = calculate_shot_danger_zone(df)

    logger.info("Calculating pre-shot pressure...")
    df = calculate_pre_shot_pressure(df)

    # Create situation-specific flags for hierarchical modeling
    df["situation"] = "ES"  # Even strength default
    df.loc[df["is_powerplay"] == 1, "situation"] = "PP"
    df.loc[df["is_shorthanded"] == 1, "situation"] = "SH"
    df.loc[df["empty_net"] == 1, "situation"] = "EN"

    # Save enhanced dataset
    output_file = "data/nhl/processed/training_data_enhanced.csv"
    df.to_csv(output_file, index=False)

    # Report on new features
    final_shape = df.shape
    logger.info(f"\nEnhanced dataset: {final_shape[0]} rows with {final_shape[1]} columns")
    logger.info(f"Added {final_shape[1] - initial_shape[1]} new features")

    # Feature statistics
    logger.info("\nFeature Statistics:")
    logger.info(
        f"Royal road passes: {df['royal_road_pass'].sum()} ({df['royal_road_pass'].mean() * 100:.1f}% of shots)"
    )
    logger.info(f"Goals from royal road: {df[df['royal_road_pass'] == 1]['is_goal'].mean() * 100:.1f}%")
    logger.info(f"Goals without royal road: {df[df['royal_road_pass'] == 0]['is_goal'].mean() * 100:.1f}%")

    logger.info("\nShots by situation:")
    for situation in ["ES", "PP", "SH", "EN"]:
        situation_df = df[df["situation"] == situation]
        logger.info(f"  {situation}: {len(situation_df)} shots, {situation_df['is_goal'].mean() * 100:.1f}% goals")

    logger.info("\nDanger zones:")
    logger.info(f"  In slot: {df['in_slot'].sum()} shots, {df[df['in_slot'] == 1]['is_goal'].mean() * 100:.1f}% goals")
    logger.info(
        f"  In crease: {df['in_crease'].sum()} shots, {df[df['in_crease'] == 1]['is_goal'].mean() * 100:.1f}% goals"
    )
    logger.info(
        f"  From point: {df['from_point'].sum()} shots, {df[df['from_point'] == 1]['is_goal'].mean() * 100:.1f}% goals"
    )

    # Also create a version with just essential features for modeling
    essential_features = [
        # Identifiers
        "game_id",
        "shooter_id",
        "goalie_id",
        # Basic shot features
        "shot_distance",
        "shot_angle",
        "shot_type",
        "x_coord",
        "y_coord",
        # Advanced geometric features
        "royal_road_pass",
        "pass_angle_change",
        "location_danger_score",
        "in_slot",
        "in_crease",
        "from_point",
        # Momentum features
        "goals_last_1min",
        "goals_last_5min",
        "shots_last_5min",
        "shot_momentum_ratio",
        # Rush and pressure
        "is_rush",
        "rush_quality_score",
        "quick_zone_to_shot",
        "low_pressure_shot",
        "high_pressure_shot",
        # Pre-shot sequence
        "is_rebound",
        "quick_strike",
        "sustained_pressure",
        "off_faceoff",
        "shots_before_goal",
        "sequence_duration",
        # Player quality
        "shooter_position",
        "assist1_position",
        "assist2_position",
        "passing_combo",
        "shooter_height_advantage",
        # Game state
        "period",
        "time_in_period",
        "home_score",
        "away_score",
        "is_powerplay",
        "is_shorthanded",
        "empty_net",
        "situation",
        # Target
        "is_goal",
    ]

    # Only include features that exist
    essential_features = [f for f in essential_features if f in df.columns]

    essential_df = df[essential_features].copy()
    essential_df.to_csv("data/nhl/processed/training_data_model_ready.csv", index=False)

    logger.info(f"\nCreated model-ready dataset with {len(essential_features)} features")
    logger.info("Saved to: data/nhl/processed/training_data_model_ready.csv")


if __name__ == "__main__":
    main()
