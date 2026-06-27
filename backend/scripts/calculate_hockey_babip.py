"""
Calculate Hockey BABIP (Batting Average on Balls In Play)
Shooting percentage on shots that actually hit the net (excludes misses and blocks)
This identifies players who consistently beat goalies WHEN they hit the net
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def calculate_player_babip(shots_df):
    """
    Calculate BABIP for all players
    BABIP = Goals / Shots on Goal (excludes misses and blocks)
    """

    # Get all shooters
    shooters = shots_df["shooter_id"].unique()

    babip_stats = []

    for shooter_id in shooters:
        player_shots = shots_df[shots_df["shooter_id"] == shooter_id]

        if len(player_shots) < 20:  # Need minimum shots
            continue

        # Get player name
        player_name = (
            player_shots["shooter_name"].iloc[0] if "shooter_name" in player_shots.columns else f"Player_{shooter_id}"
        )

        # Count shot outcomes
        total_shots = len(player_shots)
        goals = player_shots["is_goal"].sum()

        # Shots by type (if available in your data)
        shots_on_goal = (
            player_shots[player_shots["event_type"].isin(["shot-on-goal", "goal"])]
            if "event_type" in player_shots.columns
            else player_shots[
                player_shots["is_goal"] | ~player_shots.get("is_blocked", False) & ~player_shots.get("is_missed", False)
            ]
        )

        # Alternative calculation using shot results
        if "reason" in player_shots.columns:
            # Some datasets have 'reason' for non-goals
            blocked_shots = player_shots[player_shots["reason"] == "blocked"]
            shots_on_goal = player_shots[~player_shots["reason"].isin(["missed-net", "blocked"])]
        else:
            # Use proxy indicators
            if "blocker_id" in player_shots.columns:
                blocked_shots = player_shots[player_shots["blocker_id"].notna()]
            else:
                blocked_shots = pd.DataFrame()  # Empty

            # Estimate misses from shot location
            # Shots from bad angles that didn't score are likely misses
            potential_misses = player_shots[(player_shots["is_goal"] == 0) & (abs(player_shots["shot_angle"]) > 60)]

            shots_on_goal = player_shots[
                player_shots["is_goal"]
                | (~player_shots.index.isin(blocked_shots.index) & ~player_shots.index.isin(potential_misses.index))
            ]

        sog_count = len(shots_on_goal)

        # Calculate statistics
        shooting_pct = goals / total_shots if total_shots > 0 else 0
        babip = goals / sog_count if sog_count > 0 else 0
        sog_pct = sog_count / total_shots if total_shots > 0 else 0

        # Shot quality metrics
        avg_distance = player_shots["shot_distance"].mean()
        avg_angle = player_shots["shot_angle"].mean()
        avg_danger = (
            player_shots["location_danger_score"].mean() if "location_danger_score" in player_shots.columns else 0
        )

        babip_stats.append(
            {
                "player_id": shooter_id,
                "player_name": player_name,
                "total_shots": total_shots,
                "shots_on_goal": sog_count,
                "goals": goals,
                "shooting_pct": shooting_pct,
                "babip": babip,
                "sog_pct": sog_pct,
                "avg_shot_distance": avg_distance,
                "avg_shot_angle": avg_angle,
                "avg_shot_danger": avg_danger,
                "babip_vs_shooting": babip - shooting_pct,
            }
        )

    babip_df = pd.DataFrame(babip_stats)

    # Calculate league averages
    league_shooting_pct = shots_df["is_goal"].mean()
    league_babip = babip_df["babip"].mean()
    league_sog_pct = babip_df["sog_pct"].mean()

    print("HOCKEY BABIP ANALYSIS")
    print("=" * 60)
    print("\nLeague Averages:")
    print(f"Overall Shooting %: {league_shooting_pct:.1%}")
    print(f"BABIP (Goals/Shots on Goal): {league_babip:.1%}")
    print(f"Shots on Goal %: {league_sog_pct:.1%}")
    print(f"\nThis confirms: ~{league_babip:.0%} of shots ON GOAL go in vs ~{league_shooting_pct:.0%} of ALL shots!")

    # Find interesting players
    min_shots = 50
    qualified = babip_df[babip_df["total_shots"] >= min_shots]

    print(f"\nTop 10 BABIP Leaders (min {min_shots} shots):")
    print(qualified.nlargest(10, "babip")[["player_name", "babip", "shooting_pct", "total_shots", "avg_shot_distance"]])

    print(f"\nWorst BABIP (min {min_shots} shots):")
    print(
        qualified.nsmallest(10, "babip")[["player_name", "babip", "shooting_pct", "total_shots", "avg_shot_distance"]]
    )

    # Find lucky/unlucky shooters
    qualified["babip_luck"] = qualified["babip"] - league_babip
    qualified["expected_goals"] = qualified["shots_on_goal"] * league_babip
    qualified["goals_above_expected"] = qualified["goals"] - qualified["expected_goals"]

    print("\nLuckiest Shooters (High BABIP vs League Average):")
    print(qualified.nlargest(10, "babip_luck")[["player_name", "babip", "babip_luck", "goals_above_expected"]])

    print("\nUnluckiest Shooters (Low BABIP vs League Average):")
    print(qualified.nsmallest(10, "babip_luck")[["player_name", "babip", "babip_luck", "goals_above_expected"]])

    return babip_df, league_babip


def analyze_babip_by_shot_type(shots_df):
    """
    BABIP varies dramatically by shot type
    """

    if "shot_type" not in shots_df.columns:
        print("\nNo shot type data available")
        return None

    shot_type_babip = {}

    for shot_type in shots_df["shot_type"].unique():
        type_shots = shots_df[shots_df["shot_type"] == shot_type]

        # Estimate shots on goal
        if "event_type" in type_shots.columns:
            sog = type_shots[type_shots["event_type"].isin(["shot-on-goal", "goal"])]
        else:
            # Estimate - remove obvious misses (bad angles with no goal)
            sog = type_shots[
                type_shots["is_goal"] | ((abs(type_shots["shot_angle"]) < 45) & (type_shots["shot_distance"] < 40))
            ]

        if len(sog) > 20:
            shot_type_babip[shot_type] = {
                "total_shots": len(type_shots),
                "shots_on_goal": len(sog),
                "goals": type_shots["is_goal"].sum(),
                "shooting_pct": type_shots["is_goal"].mean(),
                "babip": sog["is_goal"].mean() if len(sog) > 0 else 0,
                "sog_pct": len(sog) / len(type_shots),
            }

    babip_by_type = pd.DataFrame.from_dict(shot_type_babip, orient="index")
    babip_by_type = babip_by_type.sort_values("babip", ascending=False)

    print("\nBABIP BY SHOT TYPE:")
    print("=" * 60)
    print(babip_by_type)

    return babip_by_type


def analyze_babip_stability(shots_df, babip_df):
    """
    Is BABIP a stable/predictive stat or mostly luck?
    Split season and compare first half to second half
    """

    # Split by game date
    if "game_date" in shots_df.columns:
        shots_df["game_date"] = pd.to_datetime(shots_df["game_date"])
        midpoint = shots_df["game_date"].median()

        first_half = shots_df[shots_df["game_date"] < midpoint]
        second_half = shots_df[shots_df["game_date"] >= midpoint]

        # Calculate BABIP for each half
        first_babip = calculate_player_babip(first_half)[0]
        second_babip = calculate_player_babip(second_half)[0]

        # Merge and compare
        comparison = first_babip.merge(
            second_babip[["player_id", "babip"]], on="player_id", suffixes=("_first", "_second")
        )

        # Only players with 25+ shots in each half
        qualified = comparison[(comparison["total_shots_first"] >= 25) & (comparison["total_shots"] >= 25)]

        if len(qualified) > 10:
            correlation = qualified["babip_first"].corr(qualified["babip_second"])

            print("\nBABIP STABILITY ANALYSIS:")
            print("=" * 60)
            print(f"Correlation between first half and second half BABIP: {correlation:.3f}")

            if correlation > 0.5:
                print("BABIP shows some stability - likely a skill!")
            elif correlation > 0.3:
                print("BABIP has moderate stability - mix of skill and luck")
            else:
                print("BABIP is mostly luck/variance")

            # Find consistent performers
            qualified["babip_consistency"] = abs(qualified["babip_first"] - qualified["babip_second"])

            print("\nMost Consistent BABIP (similar both halves):")
            print(
                qualified.nsmallest(10, "babip_consistency")[
                    ["player_name", "babip_first", "babip_second", "babip_consistency"]
                ]
            )


def visualize_babip_distribution(babip_df):
    """
    Visualize BABIP distribution and relationships
    """

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # BABIP distribution
    ax1 = axes[0, 0]
    qualified = babip_df[babip_df["total_shots"] >= 50]
    ax1.hist(qualified["babip"], bins=20, alpha=0.7, color="blue", edgecolor="black")
    ax1.axvline(
        qualified["babip"].mean(), color="red", linestyle="--", label=f'League Avg: {qualified["babip"].mean():.1%}'
    )
    ax1.set_xlabel("BABIP")
    ax1.set_ylabel("Number of Players")
    ax1.set_title("BABIP Distribution (min 50 shots)")
    ax1.legend()

    # BABIP vs Shooting %
    ax2 = axes[0, 1]
    ax2.scatter(qualified["shooting_pct"], qualified["babip"], alpha=0.6)
    ax2.plot([0, 0.25], [0, 0.25], "r--", label="Equal line")
    ax2.set_xlabel("Overall Shooting %")
    ax2.set_ylabel("BABIP")
    ax2.set_title("BABIP vs Shooting % (Higher BABIP = Good finisher)")
    ax2.legend()

    # BABIP vs Shot Distance
    ax3 = axes[1, 0]
    ax3.scatter(qualified["avg_shot_distance"], qualified["babip"], alpha=0.6)
    ax3.set_xlabel("Average Shot Distance")
    ax3.set_ylabel("BABIP")
    ax3.set_title("BABIP vs Shot Distance")

    # Top/Bottom BABIP players
    ax4 = axes[1, 1]
    top_10 = qualified.nlargest(10, "babip")
    bottom_10 = qualified.nsmallest(10, "babip")

    y_pos = np.arange(10)
    ax4.barh(y_pos, top_10["babip"].values, alpha=0.7, color="green", label="Top 10")
    ax4.barh(y_pos + 10.5, bottom_10["babip"].values, alpha=0.7, color="red", label="Bottom 10")
    ax4.set_yticks(list(y_pos) + list(y_pos + 10.5))
    ax4.set_yticklabels(list(top_10["player_name"].values) + list(bottom_10["player_name"].values), fontsize=8)
    ax4.set_xlabel("BABIP")
    ax4.set_title("Top and Bottom BABIP Players")
    ax4.legend()

    plt.tight_layout()
    plt.savefig("models/babip_analysis.png", dpi=300)
    print("\nVisualization saved to models/babip_analysis.png")


def main():
    """
    Run complete BABIP analysis
    """

    print("Loading shot data...")
    shots_df = pd.read_csv("data/nhl/processed/training_data_enhanced.csv")

    print(f"Analyzing BABIP for {shots_df['shooter_id'].nunique()} unique shooters...")

    # Calculate BABIP for all players
    babip_df, league_babip = calculate_player_babip(shots_df)

    # Analyze by shot type
    babip_by_type = analyze_babip_by_shot_type(shots_df)

    # Check stability
    analyze_babip_stability(shots_df, babip_df)

    # Create visualizations
    visualize_babip_distribution(babip_df)

    # Save results
    babip_df.to_csv("data/nhl/processed/player_babip_stats.csv", index=False)
    if babip_by_type is not None:
        babip_by_type.to_csv("data/nhl/processed/babip_by_shot_type.csv")

    print("\n" + "=" * 60)
    print("KEY FINDINGS FOR xG MODEL:")
    print(f"1. League BABIP is ~{league_babip:.0%} vs ~{shots_df['is_goal'].mean():.0%} overall")
    print("2. Some players consistently outperform BABIP (finishing skill)")
    print("3. Shot type dramatically affects BABIP")
    print("4. Use BABIP as a feature to identify good/bad finishers")
    print("5. Adjust xG based on shooter's historical BABIP")

    # Add BABIP to shot data
    print("\nAdding BABIP features to shots...")
    shots_df = shots_df.merge(
        babip_df[["player_id", "babip", "babip_luck", "sog_pct"]],
        left_on="shooter_id",
        right_on="player_id",
        how="left",
    )

    # Fill missing with league average
    shots_df["babip"] = shots_df["babip"].fillna(league_babip)
    shots_df["babip_multiplier"] = shots_df["babip"] / league_babip

    # Save enhanced dataset
    shots_df.to_csv("data/nhl/processed/shots_with_babip.csv", index=False)
    print("Saved shots with BABIP features to shots_with_babip.csv")


if __name__ == "__main__":
    main()
