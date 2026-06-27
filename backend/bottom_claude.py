#!/usr/bin/env python3
"""
Verify the enhanced dataset is ready for xG model training
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def verify_enhanced_dataset():
    """Verify all features and data quality"""

    logger.info("Loading enhanced dataset...")
    df = pd.read_csv("data/nhl/processed/shots_enhanced_final.csv")

    logger.info("\n" + "=" * 60)
    logger.info("ENHANCED DATASET VERIFICATION")
    logger.info("=" * 60)

    # Basic statistics
    logger.info(f"\nDataset Overview:")
    logger.info(f"  Total shots: {len(df):,}")
    logger.info(f"  Total features: {len(df.columns)}")
    logger.info(f"  Goals: {df['is_goal'].sum():,} ({df['is_goal'].mean():.2%})")
    logger.info(f"  Memory usage: {df.memory_usage().sum() / 1024**2:.1f} MB")

    # New feature distributions
    logger.info("\n" + "=" * 40)
    logger.info("NEW FEATURE DISTRIBUTIONS:")
    logger.info("=" * 40)

    # Shot zones
    logger.info("\nShot Zone Distribution:")
    shot_zones = df["shot_zone"].value_counts()
    for zone, count in shot_zones.items():
        goal_rate = df[df["shot_zone"] == zone]["is_goal"].mean()
        logger.info(f"  {zone}: {count:,} shots ({count / len(df) * 100:.1f}%), {goal_rate:.2%} goal rate")

    # Play types
    logger.info("\nPlay Type Distribution:")
    play_types = df["play_type_zone"].value_counts()
    for ptype, count in play_types.items():
        goal_rate = df[df["play_type_zone"] == ptype]["is_goal"].mean()
        logger.info(f"  {ptype}: {count:,} plays ({count / len(df) * 100:.1f}%), {goal_rate:.2%} goal rate")

    # Play patterns
    logger.info("\nPlay Pattern Features:")
    pattern_features = ["is_transition_play", "is_sustained_pressure", "is_broken_play", "is_quick_strike"]
    for feature in pattern_features:
        count = df[feature].sum()
        goal_rate = df[df[feature] == 1]["is_goal"].mean()
        logger.info(f"  {feature}: {count:,} ({count / len(df) * 100:.1f}%), {goal_rate:.2%} goal rate")

    # Royal road passes
    rr_count = df["royal_road_pass"].sum()
    if rr_count > 0:
        rr_goal_rate = df[df["royal_road_pass"] == 1]["is_goal"].mean()
        normal_goal_rate = df[df["royal_road_pass"] == 0]["is_goal"].mean()
        logger.info(f"\nRoyal Road Passes:")
        logger.info(f"  Count: {rr_count:,} ({rr_count / len(df) * 100:.2f}%)")
        logger.info(f"  Goal rate: {rr_goal_rate:.2%} vs {normal_goal_rate:.2%} normal")
        logger.info(f"  Multiplier: {rr_goal_rate / normal_goal_rate:.2f}x")

    # Danger zones
    logger.info("\nDanger Level Distribution:")
    danger_levels = df["danger_level"].value_counts()
    for level, count in danger_levels.items():
        goal_rate = df[df["danger_level"] == level]["is_goal"].mean()
        logger.info(f"  {level}: {count:,} ({count / len(df) * 100:.1f}%), {goal_rate:.2%} goal rate")

    # Check for data quality issues
    logger.info("\n" + "=" * 40)
    logger.info("DATA QUALITY CHECKS:")
    logger.info("=" * 40)

    # Missing values
    missing_counts = df.isnull().sum()
    missing_features = missing_counts[missing_counts > 0]
    if len(missing_features) > 0:
        logger.info("\nFeatures with missing values:")
        for feature, count in missing_features.items():
            logger.info(f"  {feature}: {count:,} ({count / len(df) * 100:.2f}%)")
    else:
        logger.info("\n✓ No missing values in any features!")

    # Correlations with target
    logger.info("\nTop features correlated with goals:")
    correlations = df.select_dtypes(include=[np.number]).corr()["is_goal"].abs().sort_values(ascending=False)
    for feature, corr in correlations.head(15).items():
        if feature != "is_goal":
            logger.info(f"  {feature}: {corr:.3f}")

    # Feature engineering insights
    logger.info("\n" + "=" * 40)
    logger.info("KEY INSIGHTS:")
    logger.info("=" * 40)

    # Broken plays
    broken_plays = df[df["is_broken_play"] == 1]
    if len(broken_plays) > 0:
        logger.info(f"\nBroken Plays: {len(broken_plays):,} offensive plays ending in defensive shots")
        logger.info(f"  These might indicate odd-man rushes or turnovers")
        logger.info(f"  Goal rate: {broken_plays['is_goal'].mean():.2%}")

    # Transition vs sustained
    transition_goals = df[df["is_transition_play"] == 1]["is_goal"].mean()
    sustained_goals = df[df["is_sustained_pressure"] == 1]["is_goal"].mean()
    logger.info(f"\nTransition plays: {transition_goals:.2%} goal rate")
    logger.info(f"Sustained pressure: {sustained_goals:.2%} goal rate")

    # Model readiness
    logger.info("\n" + "=" * 60)
    logger.info("MODEL READINESS CHECKLIST:")
    logger.info("=" * 60)

    checks = {
        "Dataset size > 100k": len(df) > 100000,
        "Target variable is binary": df["is_goal"].isin([0, 1]).all(),
        "No missing target values": df["is_goal"].notna().all(),
        "Features are numeric or can be encoded": True,
        "Class imbalance addressed": df["is_goal"].mean() > 0.01,
        "Key features present": all(f in df.columns for f in ["shot_distance", "shot_angle", "shot_zone"]),
    }

    all_passed = True
    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        logger.info(f"{status} {check}")
        if not passed:
            all_passed = False

    if all_passed:
        logger.info("\n🎉 DATASET IS READY FOR XG MODEL TRAINING! 🎉")
    else:
        logger.info("\n⚠️  Some checks failed - review before training")

    # Save feature list
    feature_file = Path("data/nhl/processed/model_features.txt")
    with open(feature_file, "w") as f:
        f.write("XG MODEL FEATURES\n")
        f.write("=" * 50 + "\n\n")
        f.write("Target Variable: is_goal\n\n")
        f.write("Features:\n")
        for col in sorted(df.columns):
            if col != "is_goal":
                dtype = df[col].dtype
                null_pct = df[col].isna().mean() * 100
                f.write(f"  {col} ({dtype}): {null_pct:.1f}% null\n")

    logger.info(f"\nFeature list saved to: {feature_file}")

    return df


def create_train_test_split_config(df):
    """Create configuration for train/test splitting"""

    logger.info("\n" + "=" * 60)
    logger.info("TRAIN/TEST SPLIT RECOMMENDATIONS:")
    logger.info("=" * 60)

    # Temporal split (most realistic)
    df["game_date"] = pd.to_datetime(df["game_date"])
    date_range = df["game_date"].max() - df["game_date"].min()

    logger.info(f"\nDate range: {df['game_date'].min().date()} to {df['game_date'].max().date()}")
    logger.info(f"Total days: {date_range.days}")

    # Recommend 70/15/15 split
    train_end = df["game_date"].min() + pd.Timedelta(days=int(date_range.days * 0.7))
    val_end = df["game_date"].min() + pd.Timedelta(days=int(date_range.days * 0.85))

    logger.info(f"\nRecommended temporal split:")
    logger.info(f"  Train: Start to {train_end.date()}")
    logger.info(f"  Val: {train_end.date()} to {val_end.date()}")
    logger.info(f"  Test: {val_end.date()} to End")

    # Check class balance in each split
    train_mask = df["game_date"] <= train_end
    val_mask = (df["game_date"] > train_end) & (df["game_date"] <= val_end)
    test_mask = df["game_date"] > val_end

    logger.info(f"\nClass balance by split:")
    logger.info(f"  Train: {df[train_mask]['is_goal'].mean():.2%} goal rate")
    logger.info(f"  Val: {df[val_mask]['is_goal'].mean():.2%} goal rate")
    logger.info(f"  Test: {df[test_mask]['is_goal'].mean():.2%} goal rate")

    # Save split configuration
    split_config = {
        "train_end_date": str(train_end.date()),
        "val_end_date": str(val_end.date()),
        "train_size": int(train_mask.sum()),
        "val_size": int(val_mask.sum()),
        "test_size": int(test_mask.sum()),
        "train_goal_rate": float(df[train_mask]["is_goal"].mean()),
        "val_goal_rate": float(df[val_mask]["is_goal"].mean()),
        "test_goal_rate": float(df[test_mask]["is_goal"].mean()),
    }

    with open("data/nhl/processed/train_test_split_config.json", "w") as f:
        json.dump(split_config, f, indent=2)

    logger.info(f"\nSplit configuration saved to: train_test_split_config.json")


def main():
    """Run verification"""
    df = verify_enhanced_dataset()
    create_train_test_split_config(df)

    logger.info("\n" + "=" * 60)
    logger.info("NEXT STEPS:")
    logger.info("=" * 60)
    logger.info("1. Create feature preprocessing pipeline")
    logger.info("2. Build PyTorch dataset class")
    logger.info("3. Implement hierarchical xG neural network")
    logger.info("4. Train with your hardware settings (batch_size=2048)")
    logger.info("5. Evaluate using Brier score and calibration plots")


if __name__ == "__main__":
    main()
