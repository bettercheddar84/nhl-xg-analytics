import pandas as pd
import json
from pathlib import Path
import logging

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


def main():
    logger.info("Creating comprehensive training data with assists...")

    # Load all data sources
    logger.info("Loading data files...")

    # 1. Goal sequences with assist IDs
    sequences_df = pd.read_csv("data/nhl/processed/goal_sequences_fixed.csv")

    # 2. Original shots data (has all the features)
    shots_df = pd.read_csv("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")
    goals_df = shots_df[shots_df["is_goal"] == 1].copy()

    # 3. Player lookup
    player_lookup = load_player_lookup()

    # Merge sequences with original goal data
    # Match on game_id, shooter_id, and approximate time
    merged_df = pd.merge(goals_df, sequences_df, on=["game_id", "shooter_id"], how="left", suffixes=("", "_seq"))

    # Filter to keep only matching goals (within 5 seconds)
    merged_df = merged_df[abs(merged_df["game_seconds"] - merged_df["goal_time"]) < 5].copy()

    # Remove duplicate columns
    cols_to_drop = [col for col in merged_df.columns if col.endswith("_seq")]
    merged_df = merged_df.drop(columns=cols_to_drop)

    # Add player names and info for shooter
    logger.info("Adding player information...")

    for player_id in merged_df["shooter_id"].unique():
        if pd.notna(player_id) and int(player_id) in player_lookup:
            player_info = player_lookup[int(player_id)]
            mask = merged_df["shooter_id"] == player_id
            merged_df.loc[mask, "shooter_name_verified"] = player_info["name"]
            merged_df.loc[mask, "shooter_position"] = player_info["position"]
            merged_df.loc[mask, "shooter_shoots"] = player_info["shoots"]
            merged_df.loc[mask, "shooter_height"] = player_info["height"]
            merged_df.loc[mask, "shooter_weight"] = player_info["weight"]

    # Add assist player names and info
    for assist_col, prefix in [("assist1_id", "assist1"), ("assist2_id", "assist2")]:
        for player_id in merged_df[assist_col].dropna().unique():
            if int(player_id) in player_lookup:
                player_info = player_lookup[int(player_id)]
                mask = merged_df[assist_col] == player_id
                merged_df.loc[mask, f"{prefix}_name_verified"] = player_info["name"]
                merged_df.loc[mask, f"{prefix}_position"] = player_info["position"]
                merged_df.loc[mask, f"{prefix}_shoots"] = player_info["shoots"]

    # Add goalie info
    for player_id in merged_df["goalie_id"].dropna().unique():
        if int(player_id) in player_lookup:
            player_info = player_lookup[int(player_id)]
            mask = merged_df["goalie_id"] == player_id
            merged_df.loc[mask, "goalie_name_verified"] = player_info["name"]
            merged_df.loc[mask, "goalie_catches"] = player_info["shoots"]  # Same field for goalies
            merged_df.loc[mask, "goalie_height"] = player_info["height"]
            merged_df.loc[mask, "goalie_weight"] = player_info["weight"]

    # Create passing pattern features
    logger.info("Creating passing pattern features...")

    # Passing combinations
    passing_combos = []
    for _, row in merged_df.iterrows():
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

    merged_df["passing_combo"] = passing_combos

    # Handedness patterns
    handedness_matches = []
    for _, row in merged_df.iterrows():
        if pd.notna(row.get("assist1_shoots")):
            match = row["shooter_shoots"] == row["assist1_shoots"]
        else:
            match = None
        handedness_matches.append(match)

    merged_df["shot_handedness_match"] = handedness_matches

    # Height advantages
    merged_df["shooter_height_advantage"] = merged_df["shooter_height"] - merged_df["goalie_height"]

    # Save the enhanced dataset
    output_file = "data/nhl/processed/training_data_with_assists.csv"
    merged_df.to_csv(output_file, index=False)

    # Create a summary
    logger.info("\nDataset Summary:")
    logger.info(f"Total goals with enhanced data: {len(merged_df)}")
    logger.info(f"Goals with verified shooter names: {merged_df['shooter_name_verified'].notna().sum()}")
    logger.info(f"Goals with assist1 names: {merged_df['assist1_name_verified'].notna().sum()}")
    logger.info(f"Goals with assist2 names: {merged_df['assist2_name_verified'].notna().sum()}")
    logger.info(f"Goals with passing combos: {len(merged_df['passing_combo'].unique())} unique patterns")

    # Show example records
    logger.info("\nExample goals with full assist information:")
    sample = merged_df[merged_df["assist2_name_verified"].notna()].head(3)

    for _, row in sample.iterrows():
        logger.info(f"\nGoal: {row['shooter_name_verified']} ({row['shooter_position']})")
        logger.info(f"  Assist 1: {row['assist1_name_verified']} ({row['assist1_position']})")
        logger.info(f"  Assist 2: {row['assist2_name_verified']} ({row['assist2_position']})")
        logger.info(f"  Passing combo: {row['passing_combo']}")
        logger.info(f"  Quick strike: {row['quick_strike']}, Rebound: {row['is_rebound']}")

    # Also create a simplified version with just key features for training
    key_features = [
        "game_id",
        "shooter_id",
        "shooter_name_verified",
        "shooter_position",
        "assist1_id",
        "assist1_name_verified",
        "assist1_position",
        "assist2_id",
        "assist2_name_verified",
        "assist2_position",
        "goalie_id",
        "goalie_name_verified",
        "shot_distance",
        "shot_angle",
        "shot_type",
        "passing_combo",
        "shot_handedness_match",
        "shooter_height_advantage",
        "quick_strike",
        "is_rebound",
        "sustained_pressure",
        "off_faceoff",
        "shots_before_goal",
        "sequence_duration",
        "offensive_zone_time",
        "is_powerplay",
        "is_shorthanded",
        "empty_net",
        "home_score",
        "away_score",
        "period",
        "time_in_period",
    ]

    # Only include columns that exist
    key_features = [col for col in key_features if col in merged_df.columns]

    simplified_df = merged_df[key_features].copy()
    simplified_df.to_csv("data/nhl/processed/training_assists_simplified.csv", index=False)

    logger.info("\nCreated training files:")
    logger.info(f"  - {output_file} (full dataset)")
    logger.info("  - data/nhl/processed/training_assists_simplified.csv (key features only)")


if __name__ == "__main__":
    main()
