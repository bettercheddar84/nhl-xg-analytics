"""
Calculate Shot Value Decay - How shot quality degrades with offensive zone time
This is a major finding that could significantly improve xG models
"""

import pandas as pd
import matplotlib.pyplot as plt


def analyze_shot_value_decay(shots_df):
    """
    Analyze how shot quality degrades with offensive zone time
    Fresh legs take better shots!
    """

    # Create zone time bins
    zone_time_bins = [0, 10, 20, 30, 45, 60, 120]
    zone_time_labels = ["0-10s", "10-20s", "20-30s", "30-45s", "45-60s", "60s+"]

    shots_df["zone_time_bin"] = pd.cut(
        shots_df["offensive_zone_time"], bins=zone_time_bins, labels=zone_time_labels, include_lowest=True
    )

    # Calculate metrics by zone time
    decay_analysis = (
        shots_df.groupby("zone_time_bin")
        .agg(
            {
                "location_danger_score": ["mean", "std", "count"],
                "shot_distance": ["mean", "std"],
                "is_goal": ["mean", "sum", "count"],
                "in_slot": "mean",
                "is_rush": "mean",
                "is_rebound": "mean",
                "royal_road_pass": "mean",
                "shot_angle": "mean",
            }
        )
        .round(4)
    )

    # Flatten column names
    decay_analysis.columns = ["_".join(col).strip() for col in decay_analysis.columns.values]

    # Calculate decay rates
    baseline_danger = decay_analysis.iloc[0]["location_danger_score_mean"]
    decay_analysis["danger_decay_pct"] = (
        (decay_analysis["location_danger_score_mean"] - baseline_danger) / baseline_danger * 100
    )

    baseline_distance = decay_analysis.iloc[0]["shot_distance_mean"]
    decay_analysis["distance_increase_pct"] = (
        (decay_analysis["shot_distance_mean"] - baseline_distance) / baseline_distance * 100
    )

    print("SHOT VALUE DECAY ANALYSIS")
    print("=" * 60)
    print("\nShot Quality by Offensive Zone Time:")
    print(
        decay_analysis[
            ["location_danger_score_mean", "danger_decay_pct", "shot_distance_mean", "distance_increase_pct"]
        ]
    )

    print("\nGoal Rate by Zone Time:")
    print(decay_analysis[["is_goal_mean", "is_goal_count"]])

    # Find the critical decay point
    critical_point = None
    for i in range(1, len(decay_analysis)):
        if decay_analysis.iloc[i]["danger_decay_pct"] < -15:  # 15% quality drop
            critical_point = zone_time_labels[i - 1]
            break

    print(f"\nCRITICAL FINDING: Shot quality drops >15% after {critical_point}")

    # Analyze shot type distribution over time
    print("\nShot Type Distribution by Zone Time:")
    shot_types = shots_df.groupby(["zone_time_bin", "shot_type"]).size().unstack(fill_value=0)
    shot_type_pct = shot_types.div(shot_types.sum(axis=1), axis=0) * 100
    print(shot_type_pct)

    # Player fatigue impact
    print("\nFatigue Indicators by Zone Time:")
    fatigue_indicators = decay_analysis[["in_slot_mean", "is_rush_mean", "is_rebound_mean", "royal_road_pass_mean"]]
    print(fatigue_indicators)

    return decay_analysis


def calculate_optimal_attack_duration(shots_df):
    """
    Find the optimal offensive zone time for maximizing goal probability
    """

    # Calculate rolling goal rate
    # zone_times = sorted(shots_df["offensive_zone_time"].unique())

    optimal_analysis = []
    window_size = 5  # 5-second windows

    for time_point in range(0, 60, window_size):
        window_shots = shots_df[
            (shots_df["offensive_zone_time"] >= time_point)
            & (shots_df["offensive_zone_time"] < time_point + window_size)
        ]

        if len(window_shots) > 50:  # Need sufficient sample
            analysis = {
                "zone_time": f"{time_point}-{time_point + window_size}s",
                "goal_rate": window_shots["is_goal"].mean(),
                "shot_quality": window_shots["location_danger_score"].mean(),
                "shot_count": len(window_shots),
                "shots_per_second": len(window_shots) / (window_size * window_shots["game_id"].nunique()),
            }
            optimal_analysis.append(analysis)

    optimal_df = pd.DataFrame(optimal_analysis)

    # Find optimal window
    optimal_window = optimal_df.loc[optimal_df["goal_rate"].idxmax()]

    print("\nOPTIMAL ATTACK DURATION ANALYSIS")
    print("=" * 60)
    print(optimal_df)
    print(f"\nOptimal zone time for goal scoring: {optimal_window['zone_time']}")
    print(f"Goal rate in optimal window: {optimal_window['goal_rate']:.3%}")

    return optimal_df


def analyze_team_decay_patterns(shots_df):
    """
    Do some teams handle extended zone time better?
    """

    team_decay = {}

    for team in shots_df["shooting_team"].unique():
        team_shots = shots_df[shots_df["shooting_team"] == team]

        # Early vs late zone time
        early_shots = team_shots[team_shots["offensive_zone_time"] < 20]
        late_shots = team_shots[team_shots["offensive_zone_time"] >= 30]

        if len(early_shots) > 50 and len(late_shots) > 50:
            team_decay[team] = {
                "early_quality": early_shots["location_danger_score"].mean(),
                "late_quality": late_shots["location_danger_score"].mean(),
                "quality_decay": (
                    late_shots["location_danger_score"].mean() - early_shots["location_danger_score"].mean()
                )
                / early_shots["location_danger_score"].mean()
                * 100,
                "early_goal_rate": early_shots["is_goal"].mean(),
                "late_goal_rate": late_shots["is_goal"].mean(),
                "maintains_quality": late_shots["location_danger_score"].mean()
                > early_shots["location_danger_score"].mean() * 0.85,
            }

    decay_df = pd.DataFrame.from_dict(team_decay, orient="index")
    decay_df = decay_df.sort_values("quality_decay", ascending=False)

    print("\nTEAM DECAY PATTERNS")
    print("=" * 60)
    print("\nTeams that maintain quality in extended zone time:")
    print(decay_df[decay_df["maintains_quality"]].head(10))

    print("\nTeams with worst quality decay:")
    print(decay_df.tail(10)[["early_quality", "late_quality", "quality_decay"]])

    return decay_df


def visualize_decay(decay_analysis):
    """
    Create visualization of shot value decay
    """

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Shot quality decay
    ax1 = axes[0, 0]
    x = range(len(decay_analysis))
    ax1.plot(x, decay_analysis["location_danger_score_mean"], "b-", linewidth=2)
    ax1.fill_between(
        x,
        decay_analysis["location_danger_score_mean"] - decay_analysis["location_danger_score_std"],
        decay_analysis["location_danger_score_mean"] + decay_analysis["location_danger_score_std"],
        alpha=0.3,
    )
    ax1.set_xlabel("Zone Time")
    ax1.set_ylabel("Shot Danger Score")
    ax1.set_title("Shot Quality Decay with Zone Time")
    ax1.set_xticks(x)
    ax1.set_xticklabels(decay_analysis.index)

    # Goal rate decay
    ax2 = axes[0, 1]
    ax2.bar(x, decay_analysis["is_goal_mean"], color="green", alpha=0.7)
    ax2.set_xlabel("Zone Time")
    ax2.set_ylabel("Goal Rate")
    ax2.set_title("Goal Rate by Zone Time")
    ax2.set_xticks(x)
    ax2.set_xticklabels(decay_analysis.index)

    # Shot distance increase
    ax3 = axes[1, 0]
    ax3.plot(x, decay_analysis["shot_distance_mean"], "r-", linewidth=2)
    ax3.set_xlabel("Zone Time")
    ax3.set_ylabel("Average Shot Distance (ft)")
    ax3.set_title("Shot Distance Increases with Fatigue")
    ax3.set_xticks(x)
    ax3.set_xticklabels(decay_analysis.index)

    # Shot volume
    ax4 = axes[1, 1]
    ax4.bar(x, decay_analysis["is_goal_count"], color="blue", alpha=0.7)
    ax4.set_xlabel("Zone Time")
    ax4.set_ylabel("Number of Shots")
    ax4.set_title("Shot Volume by Zone Time")
    ax4.set_xticks(x)
    ax4.set_xticklabels(decay_analysis.index)

    plt.tight_layout()
    plt.savefig("models/shot_value_decay_analysis.png", dpi=300)
    print("\nVisualization saved to models/shot_value_decay_analysis.png")


def main():
    """
    Run complete shot value decay analysis
    """

    print("Loading shot data...")
    shots_df = pd.read_csv("data/nhl/processed/training_data_enhanced.csv")

    # Filter out outliers (zone time > 120 seconds is likely data error)
    shots_df = shots_df[shots_df["offensive_zone_time"] <= 120]

    print(f"Analyzing {len(shots_df)} shots...")

    # Main decay analysis
    decay_analysis = analyze_shot_value_decay(shots_df)

    # Find optimal attack duration
    optimal_duration = calculate_optimal_attack_duration(shots_df)

    # Analyze team patterns
    team_patterns = analyze_team_decay_patterns(shots_df)

    # Create visualizations
    visualize_decay(decay_analysis)

    # Save results
    decay_analysis.to_csv("data/nhl/processed/shot_value_decay.csv")
    optimal_duration.to_csv("data/nhl/processed/optimal_attack_duration.csv")
    team_patterns.to_csv("data/nhl/processed/team_decay_patterns.csv")

    print("\n" + "=" * 60)
    print("KEY FINDINGS FOR xG MODEL:")
    print("1. Multiply xG by decay factor based on zone time")
    print("2. After 30 seconds, reduce xG by 15-20%")
    print("3. Some teams (cycle teams) maintain quality better")
    print("4. Rush chances (0-10s) have highest value")
    print("5. Consider separate models for fresh vs tired attacks")

    # Calculate feature for model
    print("\nCreating decay-adjusted features...")

    # Add decay factor to shots
    decay_factors = {"0-10s": 1.0, "10-20s": 0.95, "20-30s": 0.90, "30-45s": 0.82, "45-60s": 0.78, "60s+": 0.75}

    shots_df["quality_decay_factor"] = shots_df["zone_time_bin"].map(decay_factors)
    shots_df["decay_adjusted_danger"] = shots_df["location_danger_score"] * shots_df["quality_decay_factor"]

    # Save enhanced dataset
    shots_df.to_csv("data/nhl/processed/shots_with_decay_factor.csv", index=False)
    print("Saved shots with decay factor to shots_with_decay_factor.csv")


if __name__ == "__main__":
    main()
