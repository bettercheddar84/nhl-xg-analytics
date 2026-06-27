import pandas as pd
import os
from autogluon.tabular import TabularPredictor
import torch

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# Verify GPU
torch.cuda.set_device(0)
print(f"GPU available: {torch.cuda.is_available()}")
print(f"GPU device: {torch.cuda.get_device_name(0)}")

# Load data
df = pd.read_csv("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")

# Define feature columns
exclude_cols = [
    "is_goal",
    "game_id",
    "shooter_id",  # LEAKING
    "goalie_id",  # LEAKING
    "shooter_name",
    "goalie_name",
    "assist1_name",
    "assist2_name",
    "assist1_id",
    "assist2_id",
    "blocker_id",
    "reason",
    "prev_shot_result",
    "event_type",
    "shot_type",
    "shooting_team_id",
    "home_team_id",
    "away_team_id",
    "venue",
    "prev_event_type",
    "prev_event_team",
]

# Check for leakage
print("Checking for data leakage...")
for col in df.columns:
    if col in exclude_cols:
        continue
    goal_nulls = df[df["is_goal"] == 1][col].isna().sum()
    non_goal_nulls = df[df["is_goal"] == 0][col].isna().sum()

    if goal_nulls == 0 and non_goal_nulls == len(df[df["is_goal"] == 0]):
        print(f"LEAKAGE: {col} only populated for goals")
    if non_goal_nulls == 0 and goal_nulls == len(df[df["is_goal"] == 1]):
        print(f"LEAKAGE: {col} only populated for non-goals")

# Create label
label = "is_goal"

# Split by date
train_data = df[df["game_date"] < "2025-03-01"]
test_data = df[df["game_date"] >= "2025-03-01"]

feature_cols = [col for col in df.columns if col not in exclude_cols]

# Train
predictor = TabularPredictor(label=label, path="models/autogluon", eval_metric="roc_auc").fit(
    train_data[feature_cols + [label]], presets="best_quality", time_limit=3600
)

# Evaluate
test_predictions = predictor.predict_proba(test_data[feature_cols])
print(predictor.leaderboard(test_data[feature_cols + [label]]))
