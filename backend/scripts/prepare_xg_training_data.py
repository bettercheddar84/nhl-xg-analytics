"""
Prepare complete training dataset for XG model
Includes ALL shots (goals and non-goals) with assist information where available
"""

import pandas as pd
import json
from pathlib import Path
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_player_lookup():
    """Create a player ID to name lookup from player files."""
    player_lookup = {}
    player_dir = Path("data/nhl/players")

    for player_file in player_dir.glob("*.json"):
        try:
            with open(player_file) as f:
                player_data = json.load(f)

            player_id = int(player_file.stem)
            first = player_data.get("firstName", {}).get("default", "")
            last = player_data.get("lastName", {}).get("default", "")
            full_name = f"{first} {last}".strip()

            # Also get position and other useful info
            player_lookup[player_id] = {
                "name": full_name,
                "position": player_data.get("position", ""),
                "shoots": player_data.get("shootsCatches", ""),
                "height": player_data.get("heightInInches", 0),
                "weight": player_data.get("weightInPounds", 0),
            }
        except Exception as e:
            logger.debug(f"Error loading {player_file}: {e}")

    logger.info(f"Loaded {len(player_lookup)} player records")
    return player_lookup


def add_player_info(df, player_lookup):
    """Add player names and details to the dataframe."""

    # Initialize string columns
    str_cols = ["shooter_name", "shooter_position", "shooter_shoots", "goalie_name", "goalie_catches"]
    for col in str_cols:
        df[col] = pd.NA

    # Initialize numeric columns
    num_cols = ["shooter_height", "shooter_weight", "goalie_height", "goalie_weight"]
    for col in num_cols:
        df[col] = np.nan

    # Add shooter info
    for player_id in df["shooter_id"].dropna().unique():
        if int(player_id) in player_lookup:
            player_info = player_lookup[int(player_id)]
            mask = df["shooter_id"] == player_id
            df.loc[mask, "shooter_name"] = player_info["name"]
            df.loc[mask, "shooter_position"] = player_info["position"]
            df.loc[mask, "shooter_shoots"] = player_info["shoots"]
            df.loc[mask, "shooter_height"] = player_info["height"]
            df.loc[mask, "shooter_weight"] = player_info["weight"]

    # Add goalie info
    for player_id in df["goalie_id"].dropna().unique():
        if int(player_id) in player_lookup:
            player_info = player_lookup[int(player_id)]
            mask = df["goalie_id"] == player_id
            df.loc[mask, "goalie_name"] = player_info["name"]
            df.loc[mask, "goalie_catches"] = player_info["shoots"]
            df.loc[mask, "goalie_height"] = player_info["height"]
            df.loc[mask, "goalie_weight"] = player_info["weight"]

    return df


def add_assist_info(df, sequences_df, player_lookup):
    """Add assist information to goals only."""

    # Separate goals and non-goals
    goals_df = df[df["is_goal"] == 1].copy()
    non_goals_df = df[df["is_goal"] == 0].copy()

    # Add a unique identifier for merging
    goals_df["shot_id"] = goals_df.index

    # Get available columns from sequences_df
    sequence_cols = ["game_id", "shooter_id", "goal_time", "assist1_id", "assist2_id"]
    optional_cols = [
        "quick_strike",
        "sustained_pressure",
        "off_faceoff",
        "shots_before_goal",
        "sequence_duration",
        "offensive_zone_time",
    ]

    # Add optional columns if they exist
    for col in optional_cols:
        if col in sequences_df.columns:
            sequence_cols.append(col)

    # Merge assist info with goals
    goals_with_assists = pd.merge(
        goals_df, sequences_df[sequence_cols], on=["game_id", "shooter_id"], how="left", suffixes=("", "_seq")
    )

    # Filter to keep only matching goals (within 5 seconds)
    time_match = abs(goals_with_assists["game_seconds"] - goals_with_assists["goal_time"]) < 5
    goals_with_assists = goals_with_assists[time_match].copy()

    # Drop duplicates keeping the best match (closest time)
    goals_with_assists["time_diff"] = abs(goals_with_assists["game_seconds"] - goals_with_assists["goal_time"])
    goals_with_assists = (
        goals_with_assists.sort_values("time_diff")
        .drop_duplicates(subset=["shot_id"], keep="first")
        .drop(columns=["time_diff", "goal_time", "shot_id"])
    )

    # Initialize assist columns
    assist_str_cols = [
        f"{prefix}_{attr}" for prefix in ["assist1", "assist2"] for attr in ["name", "position", "shoots"]
    ]
    for col in assist_str_cols:
        goals_with_assists[col] = pd.NA

    # Add assist player info
    for assist_col, prefix in [("assist1_id", "assist1"), ("assist2_id", "assist2")]:
        for player_id in goals_with_assists[assist_col].dropna().unique():
            if int(player_id) in player_lookup:
                player_info = player_lookup[int(player_id)]
                mask = goals_with_assists[assist_col] == player_id
                goals_with_assists.loc[mask, f"{prefix}_name"] = player_info["name"]
                goals_with_assists.loc[mask, f"{prefix}_position"] = player_info["position"]
                goals_with_assists.loc[mask, f"{prefix}_shoots"] = player_info["shoots"]

    # Add empty assist columns to non-goals
    assist_columns = [
        "assist1_id",
        "assist1_name",
        "assist1_position",
        "assist1_shoots",
        "assist2_id",
        "assist2_name",
        "assist2_position",
        "assist2_shoots",
        "quick_strike",
        "sustained_pressure",
        "off_faceoff",
        "shots_before_goal",
        "sequence_duration",
        "offensive_zone_time",
    ]

    for col in assist_columns:
        if col not in non_goals_df.columns:
            non_goals_df[col] = np.nan

    # Combine back together
    combined_df = pd.concat([goals_with_assists, non_goals_df], ignore_index=True)

    return combined_df


def create_advanced_features(df):
    """Create advanced features for all shots."""

    # Passing combinations (only for goals with assists)
    passing_combos = []
    for _, row in df.iterrows():
        if pd.notna(row.get("assist2_id")):
            combo = (
                f"{row.get('assist2_position', 'NA')}-"
                f"{row.get('assist1_position', 'NA')}-"
                f"{row.get('shooter_position', 'NA')}"
            )
        elif pd.notna(row.get("assist1_id")):
            combo = f"{row.get('assist1_position', 'NA')}-{row.get('shooter_position', 'NA')}"
        else:
            combo = f"Solo-{row.get('shooter_position', 'NA')}"
        passing_combos.append(combo)

    df["passing_combo"] = passing_combos

    # Handedness match (for goals with assists)
    handedness_matches = []
    for _, row in df.iterrows():
        assist1_shoots = row.get("assist1_shoots") if "assist1_shoots" in df.columns else None
        shooter_shoots = row.get("shooter_shoots") if "shooter_shoots" in df.columns else None

        if pd.notna(assist1_shoots) and pd.notna(shooter_shoots):
            match = assist1_shoots == shooter_shoots
        else:
            match = np.nan
        handedness_matches.append(match)

    df["shot_handedness_match"] = handedness_matches

    # Height advantages
    df["shooter_height_advantage"] = df["shooter_height"] - df["goalie_height"]

    # Fix situation flags based on strength_state
    if "strength_state" in df.columns:
        df["is_powerplay"] = df["strength_state"].isin([1451, 1461, 1351]).astype(int)
        df["is_shorthanded"] = df["strength_state"].isin([1541, 1531, 1641]).astype(int)
        df["empty_net"] = df["strength_state"].isin([1661, 1651, 1561]).astype(int)

    # Convert booleans to int for training
    bool_columns = [
        "is_goal",
        "is_powerplay",
        "is_shorthanded",
        "empty_net",
        "is_rebound",
        "quick_strike",
        "sustained_pressure",
        "off_faceoff",
    ]

    for col in bool_columns:
        if col in df.columns:
            # Convert boolean/object types properly
            if df[col].dtype == "object":
                df[col] = df[col].map({"True": 1, "False": 0, True: 1, False: 0})
            elif df[col].dtype != "int64":
                df[col] = df[col].fillna(0).astype(int)

    # Add situational indicators
    df["situation_5v5"] = ((df["is_powerplay"] == 0) & (df["is_shorthanded"] == 0) & (df["empty_net"] == 0)).astype(int)
    df["situation_pp"] = df["is_powerplay"].astype(int)
    df["situation_pk"] = df["is_shorthanded"].astype(int)
    df["situation_en"] = df["empty_net"].astype(int)

    return df


def main():
    logger.info("Creating comprehensive XG training data with ALL shots...")

    # Load data
    logger.info("Loading data files...")

    # 1. ALL shots (goals and non-goals)
    shots_df = pd.read_csv("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")

    # Ensure is_goal is numeric
    if shots_df["is_goal"].dtype == "bool":
        shots_df["is_goal"] = shots_df["is_goal"].astype(int)

    logger.info(f"Loaded {len(shots_df)} total shots")
    logger.info(f"Goals: {shots_df['is_goal'].sum()}, Non-goals: {(~shots_df['is_goal'].astype(bool)).sum()}")

    # 2. Goal sequences with assist IDs (for goals only)
    sequences_df = pd.read_csv("data/nhl/processed/goal_sequences_fixed.csv")

    # 3. Player lookup
    player_lookup = load_player_lookup()

    # Add basic player info to all shots
    logger.info("Adding player information to all shots...")
    shots_df = add_player_info(shots_df, player_lookup)

    # Add assist info to goals only
    logger.info("Adding assist information to goals...")
    shots_df = add_assist_info(shots_df, sequences_df, player_lookup)

    # Create advanced features
    logger.info("Creating advanced features...")
    shots_df = create_advanced_features(shots_df)

    # Save the complete dataset (overwrite original)
    output_file = "data/nhl/processed/training_data_enhanced.csv"
    shots_df.to_csv(output_file, index=False)

    # Debug: Check what values we have for situation columns
    logger.info("\nDebugging situation columns:")
    for col in ["strength_state", "is_powerplay", "is_shorthanded", "empty_net"]:
        if col in shots_df.columns:
            logger.info(f"{col}: value counts = {shots_df[col].value_counts().head()}")

    # Create summary
    logger.info("\nDataset Summary:")
    logger.info(f"Total shots: {len(shots_df)}")
    logger.info(f"Goals: {shots_df['is_goal'].sum()} ({shots_df['is_goal'].mean():.2%})")
    logger.info(f"Shots with shooter names: {shots_df['shooter_name'].notna().sum()}")
    logger.info(f"Goals with assist1: {(shots_df['is_goal'] & shots_df['assist1_id'].notna()).sum()}")
    logger.info(f"Goals with assist2: {(shots_df['is_goal'] & shots_df['assist2_id'].notna()).sum()}")
    logger.info("\nSituations:")
    logger.info(f"  5v5: {shots_df['situation_5v5'].sum()}")
    logger.info(f"  Powerplay: {shots_df['situation_pp'].sum()}")
    logger.info(f"  Penalty Kill: {shots_df['situation_pk'].sum()}")
    logger.info(f"  Empty Net: {shots_df['situation_en'].sum()}")

    # Feature columns for model
    feature_columns = [
        # Shot features
        "shot_distance",
        "shot_angle",
        "shot_type",
        # Player features
        "shooter_id",
        "goalie_id",
        "shooter_height_advantage",
        # Assist features (will be NaN for non-goals)
        "assist1_id",
        "assist2_id",
        "passing_combo",
        "shot_handedness_match",
        "quick_strike",
        "sustained_pressure",
        "off_faceoff",
        "shots_before_goal",
        "sequence_duration",
        "offensive_zone_time",
        # Game state
        "period",
        "time_in_period",
        "home_score",
        "away_score",
        "is_powerplay",
        "is_shorthanded",
        "empty_net",
        "is_rebound",
        # Situations
        "situation_5v5",
        "situation_pp",
        "situation_pk",
        "situation_en",
        # Target
        "is_goal",
    ]

    # Check which features are available
    available_features = [col for col in feature_columns if col in shots_df.columns]
    missing_features = [col for col in feature_columns if col not in shots_df.columns]

    logger.info(f"\nAvailable features: {len(available_features)}")
    if missing_features:
        logger.info(f"Missing features: {missing_features}")

    # Save a version with just required columns
    minimal_df = shots_df[available_features].copy()
    minimal_df.to_csv("data/nhl/processed/training_assists_simplified.csv", index=False)

    logger.info("\nSaved files:")
    logger.info(f"  - {output_file} (complete dataset with all shots)")
    logger.info("  - data/nhl/processed/training_assists_simplified.csv (model features only)")

    # Show sample
    logger.info("\nSample of data:")
    logger.info("Goals with assists:")
    sample_goals = shots_df[(shots_df["is_goal"] == 1) & shots_df["assist1_id"].notna()].head(2)
    for col in ["shooter_name", "assist1_name", "assist2_name", "passing_combo", "shot_distance"]:
        if col in sample_goals.columns:
            logger.info(f"  {col}: {sample_goals[col].values}")

    logger.info("\nNon-goals sample:")
    sample_saves = shots_df[shots_df["is_goal"] == 0].head(2)
    for col in ["shooter_name", "goalie_name", "shot_type", "shot_distance"]:
        if col in sample_saves.columns:
            logger.info(f"  {col}: {sample_saves[col].values}")


if __name__ == "__main__":
    main()
