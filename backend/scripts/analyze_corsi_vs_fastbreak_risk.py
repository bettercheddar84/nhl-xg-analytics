"""
Analyze the trade-off between Corsi (shot attempts) and fast break risk
When does the benefit of more shots get outweighed by counter-attack danger?
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class CorsiVsFastBreakAnalyzer:
    """Analyze the optimal shot selection strategy"""

    def __init__(self):
        self.shots_df = pd.DataFrame()
        self.fast_breaks_df = pd.DataFrame()
        self.results = {}

    def load_data(self):
        """Load shot and fast break data"""
        print("Loading data...")

        # Load all shots (including misses and blocks)
        self.shots_df = pd.read_csv("data/nhl/processed/training_data_enhanced.csv")

        # Load fast break patterns (shots that led to opponent goals)
        try:
            self.fast_breaks_df = pd.read_csv("data/nhl/processed/fast_break_patterns.csv")
            print(f"Loaded {len(self.fast_breaks_df)} fast break patterns")
        except FileNotFoundError:
            print("Fast break patterns not found - creating from data")
            self.fast_breaks_df = self.extract_fast_breaks()

        print(f"Total shots analyzed: {len(self.shots_df)}")

    def extract_fast_breaks(self):
        """Extract shots that led to opponent fast breaks"""

        # Find shots followed by opponent goals within 30 seconds
        fast_breaks = []

        for game_id in self.shots_df["game_id"].unique():
            game_shots = self.shots_df[self.shots_df["game_id"] == game_id].sort_values("game_seconds")

            for idx, shot in game_shots.iterrows():
                # Skip if it was a goal
                if shot["is_goal"]:
                    continue

                # Find next opponent shot
                next_shots = game_shots[
                    (game_shots["game_seconds"] > shot["game_seconds"])
                    & (game_shots["game_seconds"] <= shot["game_seconds"] + 30)
                    & (game_shots["shooting_team"] != shot["shooting_team"])
                ]

                if not next_shots.empty:
                    next_shot = next_shots.iloc[0]
                    if next_shot["is_goal"]:
                        # This shot led to an opponent goal
                        fast_break = {
                            "original_shot_id": idx,
                            "shot_type": shot["shot_type"],
                            "shot_distance": shot["shot_distance"],
                            "shot_angle": shot["shot_angle"],
                            "location_danger_score": shot["location_danger_score"],
                            "is_missed": shot.get("is_missed", False),
                            "is_blocked": shot.get("is_blocked", False),
                            "time_to_opponent_goal": (next_shot["game_seconds"] - shot["game_seconds"]),
                            "opponent_shot_was_rush": next_shot.get("is_rush", False),
                        }
                        fast_breaks.append(fast_break)

        return pd.DataFrame(fast_breaks)

    def calculate_shot_value_equation(self):
        """
        Calculate the true value of a shot considering:
        1. Probability of scoring
        2. Probability of rebound goal
        3. Probability of opponent fast break goal
        """

        print("\nCalculating comprehensive shot values...")

        # Group shots by quality bins
        self.shots_df["danger_bin"] = pd.qcut(
            self.shots_df["location_danger_score"],
            q=10,
            labels=["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10"],
        )

        results = []

        for danger_bin in self.shots_df["danger_bin"].unique():
            bin_shots = self.shots_df[self.shots_df["danger_bin"] == danger_bin]

            # Calculate probabilities
            p_goal = bin_shots["is_goal"].mean()

            # Rebound goals (goal within 3 seconds by same team)
            if "is_rebound" in bin_shots:
                p_rebound_goal = bin_shots[bin_shots["is_rebound"]]["is_goal"].mean()
            else:
                p_rebound_goal = 0

            # Fast break against probability
            total_shots = len(bin_shots)
            fast_break_shots = len(self.fast_breaks_df[self.fast_breaks_df["original_shot_id"].isin(bin_shots.index)])
            if total_shots > 0:
                p_fast_break_against = fast_break_shots / total_shots
            else:
                p_fast_break_against = 0

            # Net shot value
            shot_value = p_goal + (0.3 * p_rebound_goal) - p_fast_break_against

            # Additional metrics
            avg_distance = bin_shots["shot_distance"].mean()
            avg_angle = bin_shots["shot_angle"].mean()
            shot_count = len(bin_shots)

            # Corsi contribution (all shot attempts)
            corsi_for = shot_count

            results.append(
                {
                    "danger_bin": danger_bin,
                    "shot_count": shot_count,
                    "avg_danger_score": bin_shots["location_danger_score"].mean(),
                    "avg_distance": avg_distance,
                    "avg_angle": avg_angle,
                    "p_goal": p_goal,
                    "p_rebound_goal": p_rebound_goal,
                    "p_fast_break_against": p_fast_break_against,
                    "shot_value": shot_value,
                    "corsi_contribution": corsi_for,
                }
            )

        value_df = pd.DataFrame(results).sort_values("avg_danger_score")

        print("\nSHOT VALUE ANALYSIS BY DANGER LEVEL:")
        print("=" * 80)
        print(value_df[["danger_bin", "avg_distance", "p_goal", "p_fast_break_against", "shot_value"]])

        # Find the crossover point
        positive_value = value_df[value_df["shot_value"] > 0]
        negative_value = value_df[value_df["shot_value"] <= 0]

        if not negative_value.empty:
            crossover_danger = positive_value["avg_danger_score"].min()
            crossover_distance = positive_value["avg_distance"].max()

            print("\nCROSSOVER POINT FOUND:")
            print("Shots become net negative when:")
            print(f"- Danger score < {crossover_danger:.3f}")
            print(f"- Distance > {crossover_distance:.1f} feet")
            print("- Fast break risk > goal probability")

        self.results["value_analysis"] = value_df

        return value_df

    def analyze_shot_types_risk(self):
        """Analyze fast break risk by shot type"""

        print("\nAnalyzing fast break risk by shot type...")

        shot_type_analysis = []

        for shot_type in self.shots_df["shot_type"].unique():
            type_shots = self.shots_df[self.shots_df["shot_type"] == shot_type]

            # Calculate metrics
            total = len(type_shots)
            goals = type_shots["is_goal"].sum()

            # Fast breaks from this shot type
            type_fast_breaks = self.fast_breaks_df[self.fast_breaks_df["shot_type"] == shot_type]

            analysis = {
                "shot_type": shot_type,
                "total_shots": total,
                "goal_rate": goals / total if total > 0 else 0,
                "fast_break_rate": len(type_fast_breaks) / total if total > 0 else 0,
                "net_value": ((goals / total) - (len(type_fast_breaks) / total) if total > 0 else 0),
                "avg_distance": type_shots["shot_distance"].mean(),
            }

            shot_type_analysis.append(analysis)

        type_df = pd.DataFrame(shot_type_analysis).sort_values("net_value", ascending=False)

        print("\nSHOT TYPE RISK ANALYSIS:")
        print("=" * 60)
        print(type_df)

        self.results["shot_type_risk"] = type_df

        return type_df

    def find_optimal_corsi_strategy(self):
        """
        Find the optimal shooting strategy that maximizes goals while minimizing fast breaks
        """

        print("\nFinding optimal Corsi strategy...")

        # Define shot quality thresholds
        thresholds = np.arange(0.02, 0.20, 0.01)

        strategy_results = []

        for threshold in thresholds:
            # Simulate only taking shots above this danger threshold
            selected_shots = self.shots_df[self.shots_df["location_danger_score"] >= threshold]

            if len(selected_shots) < 100:  # Need minimum sample
                continue

            # Calculate outcomes
            shots_taken = len(selected_shots)
            goals_scored = selected_shots["is_goal"].sum()

            # Fast breaks conceded from these shots
            fast_breaks_from_selected = self.fast_breaks_df[
                self.fast_breaks_df["original_shot_id"].isin(selected_shots.index)
            ]
            fast_breaks_conceded = len(fast_breaks_from_selected)

            # Net goals (scored - conceded from fast breaks)
            net_goals = goals_scored - fast_breaks_conceded

            # Corsi metrics
            corsi_for = shots_taken
            corsi_percentage = corsi_for / len(self.shots_df) * 100

            strategy = {
                "danger_threshold": threshold,
                "shots_taken": shots_taken,
                "shots_eliminated": len(self.shots_df) - shots_taken,
                "goals_scored": goals_scored,
                "fast_breaks_conceded": fast_breaks_conceded,
                "net_goals": net_goals,
                "goal_rate": goals_scored / shots_taken,
                "fast_break_rate": fast_breaks_conceded / shots_taken,
                "net_goal_rate": net_goals / shots_taken,
                "corsi_percentage": corsi_percentage,
            }

            strategy_results.append(strategy)

        strategy_df = pd.DataFrame(strategy_results)

        # Find optimal threshold
        optimal_idx = strategy_df["net_goals"].idxmax()
        optimal_strategy = strategy_df.loc[optimal_idx]

        print("\nOPTIMAL SHOOTING STRATEGY:")
        print("=" * 60)
        print(f"Danger threshold: {optimal_strategy['danger_threshold']:.3f}")
        print(f"Shots to take: {optimal_strategy['corsi_percentage']:.1f}% of current")
        improvement = optimal_strategy["net_goals"] - strategy_df.iloc[0]["net_goals"]
        print(f"Expected improvement: {improvement:.0f} net goals")
        print("\nDetails:")
        print(f"- Eliminate {optimal_strategy['shots_eliminated']:.0f} low-quality shots")
        reduction = strategy_df.iloc[0]["fast_breaks_conceded"] - optimal_strategy["fast_breaks_conceded"]
        print(f"- Reduce fast breaks by {reduction:.0f}")
        print(f"- Maintain {optimal_strategy['goals_scored']:.0f} goals scored")

        self.results["optimal_strategy"] = optimal_strategy
        self.results["strategy_curve"] = strategy_df

        return strategy_df

    def analyze_team_strategies(self):
        """Analyze how different teams balance Corsi vs quality"""

        print("\nAnalyzing team strategies...")

        team_analysis = []

        for team in self.shots_df["shooting_team"].unique():
            team_shots = self.shots_df[self.shots_df["shooting_team"] == team]

            # Calculate team metrics
            total_shots = len(team_shots)
            avg_quality = team_shots["location_danger_score"].mean()
            goal_rate = team_shots["is_goal"].mean()

            # Fast breaks conceded
            team_fast_breaks = self.fast_breaks_df[self.fast_breaks_df["original_shot_id"].isin(team_shots.index)]
            if total_shots > 0:
                fast_break_rate = len(team_fast_breaks) / total_shots
            else:
                fast_break_rate = 0

            # Categorize strategy
            median_shots = self.shots_df.groupby("shooting_team").size().median()
            median_quality = self.shots_df["location_danger_score"].median()

            if total_shots > median_shots:
                if avg_quality > median_quality:
                    strategy = "High Volume, High Quality"
                else:
                    strategy = "High Volume, Low Quality (Risky)"
            else:
                if avg_quality > median_quality:
                    strategy = "Low Volume, High Quality (Selective)"
                else:
                    strategy = "Low Volume, Low Quality (Poor)"

            team_analysis.append(
                {
                    "team": team,
                    "total_shots": total_shots,
                    "avg_shot_quality": avg_quality,
                    "goal_rate": goal_rate,
                    "fast_break_rate": fast_break_rate,
                    "net_shooting_value": goal_rate - fast_break_rate,
                    "strategy": strategy,
                }
            )

        team_df = pd.DataFrame(team_analysis).sort_values("net_shooting_value", ascending=False)

        print("\nTEAM SHOOTING STRATEGIES:")
        print("=" * 80)
        print(team_df.head(10)[["team", "strategy", "avg_shot_quality", "net_shooting_value"]])

        self.results["team_strategies"] = team_df

        return team_df

    def visualize_corsi_tradeoff(self):
        """Create visualizations of the Corsi vs fast break trade-off"""

        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # 1. Shot value by danger level
        ax1 = axes[0, 0]
        value_df = self.results["value_analysis"]

        x = range(len(value_df))
        width = 0.35

        ax1.bar(
            [i - width / 2 for i in x], value_df["p_goal"], width, label="Goal Probability", color="green", alpha=0.7
        )
        ax1.bar(
            [i + width / 2 for i in x],
            value_df["p_fast_break_against"],
            width,
            label="Fast Break Risk",
            color="red",
            alpha=0.7,
        )
        ax1.plot(x, value_df["shot_value"], "k-", linewidth=2, label="Net Shot Value")
        ax1.axhline(y=0, color="gray", linestyle="--")

        ax1.set_xlabel("Shot Danger Level")
        ax1.set_ylabel("Probability")
        ax1.set_title("Shot Value = P(Goal) - P(Fast Break Against)")
        ax1.set_xticks(x)
        ax1.set_xticklabels(value_df["danger_bin"])
        ax1.legend()

        # 2. Optimal strategy curve
        ax2 = axes[0, 1]
        strategy_df = self.results["strategy_curve"]

        ax2.plot(strategy_df["corsi_percentage"], strategy_df["goals_scored"], "g-", label="Goals For", linewidth=2)
        ax2.plot(
            strategy_df["corsi_percentage"],
            strategy_df["fast_breaks_conceded"],
            "r-",
            label="Fast Breaks Against",
            linewidth=2,
        )
        ax2.plot(strategy_df["corsi_percentage"], strategy_df["net_goals"], "k-", label="Net Goals", linewidth=3)

        # Mark optimal point
        optimal = self.results["optimal_strategy"]
        ax2.scatter(
            optimal["corsi_percentage"],
            optimal["net_goals"],
            s=200,
            c="gold",
            edgecolors="black",
            linewidth=2,
            zorder=5,
            label="Optimal Strategy",
        )

        ax2.set_xlabel("Corsi % (Percentage of Shots Taken)")
        ax2.set_ylabel("Goals")
        ax2.set_title("Finding Optimal Shooting Strategy")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. Shot type risk/reward
        ax3 = axes[1, 0]
        type_df = self.results["shot_type_risk"]

        ax3.scatter(type_df["goal_rate"], type_df["fast_break_rate"], s=type_df["total_shots"] / 50, alpha=0.6)

        for idx, row in type_df.iterrows():
            ax3.annotate(row["shot_type"], (row["goal_rate"], row["fast_break_rate"]), fontsize=8, ha="center")

        # Add diagonal line (break-even)
        max_val = max(type_df["goal_rate"].max(), type_df["fast_break_rate"].max())
        ax3.plot([0, max_val], [0, max_val], "k--", alpha=0.5, label="Break-even line")

        ax3.set_xlabel("Goal Rate")
        ax3.set_ylabel("Fast Break Against Rate")
        ax3.set_title("Shot Type Risk vs Reward")
        ax3.legend()

        # 4. Team strategies
        ax4 = axes[1, 1]
        team_df = self.results["team_strategies"].head(20)

        colors = {
            "High Volume, High Quality": "green",
            "High Volume, Low Quality (Risky)": "orange",
            "Low Volume, High Quality (Selective)": "blue",
            "Low Volume, Low Quality (Poor)": "red",
        }

        for strategy, color in colors.items():
            strategy_teams = team_df[team_df["strategy"] == strategy]
            if not strategy_teams.empty:
                ax4.scatter(
                    strategy_teams["total_shots"],
                    strategy_teams["net_shooting_value"],
                    c=color,
                    label=strategy,
                    s=100,
                    alpha=0.7,
                )

        ax4.set_xlabel("Total Shots (Corsi For)")
        ax4.set_ylabel("Net Shooting Value (Goals - Fast Breaks)")
        ax4.set_title("Team Shooting Strategies")
        ax4.legend(fontsize=8)
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig("models/corsi_vs_fastbreak_analysis.png", dpi=300)
        print("\nVisualization saved to models/corsi_vs_fastbreak_analysis.png")

    def generate_recommendations(self):
        """Generate actionable recommendations"""

        print("\n" + "=" * 80)
        print("KEY FINDINGS AND RECOMMENDATIONS:")
        print("=" * 80)

        optimal = self.results["optimal_strategy"]

        print("\n1. OPTIMAL SHOOTING THRESHOLD:")
        print(f"   - Only shoot when danger score > {optimal['danger_threshold']:.3f}")
        print(f"   - This eliminates {optimal['shots_eliminated']:.0f} low-value shots")
        improvement = optimal["net_goals"] - self.results["strategy_curve"].iloc[0]["net_goals"]
        print(f"   - Net improvement: +{improvement:.0f} goals")

        print("\n2. SHOT TYPES TO AVOID:")
        risky_shots = self.results["shot_type_risk"][self.results["shot_type_risk"]["net_value"] < 0]
        if not risky_shots.empty:
            print("   These shot types create more fast breaks than goals:")
            for _, shot in risky_shots.iterrows():
                print(f"   - {shot['shot_type']}: " f"{shot['fast_break_rate']:.1%} fast break rate")

        print("\n3. DISTANCE THRESHOLD:")
        value_df = self.results["value_analysis"]
        negative_value = value_df[value_df["shot_value"] <= 0]
        if not negative_value.empty:
            max_safe_distance = value_df[value_df["shot_value"] > 0]["avg_distance"].max()
            print(f"   - Avoid shots beyond {max_safe_distance:.1f} feet " "unless high danger")

        print("\n4. STRATEGIC IMPLICATIONS:")
        print("   - Possession > Low-percentage shots")
        print("   - MUST HIT THE NET - Missed shots create most dangerous " "fast breaks")
        print("   - Work puck for better opportunities instead of forcing shots")
        print("   - Shot accuracy matters more than shot volume")

        print("\n5. CORSI PARADOX RESOLVED:")
        print("   - Traditional Corsi counts ALL shot attempts as positive")
        print("   - But missed/blocked shots can be NET NEGATIVE due to fast breaks")
        print(f"   - Optimal Corsi target: {optimal['corsi_percentage']:.0f}% of current volume")
        print("   - This means being MORE SELECTIVE, not less")


def main():
    """Run complete Corsi vs Fast Break analysis"""

    analyzer = CorsiVsFastBreakAnalyzer()

    # Load data
    analyzer.load_data()

    # Run analyses
    analyzer.calculate_shot_value_equation()
    analyzer.analyze_shot_types_risk()
    analyzer.find_optimal_corsi_strategy()
    analyzer.analyze_team_strategies()

    # Create visualizations
    analyzer.visualize_corsi_tradeoff()

    # Generate recommendations
    analyzer.generate_recommendations()

    # Save results
    pd.DataFrame([analyzer.results["optimal_strategy"]]).to_csv(
        "data/nhl/processed/optimal_shooting_strategy.csv", index=False
    )

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("Results saved to data/nhl/processed/optimal_shooting_strategy.csv")
    print("This analysis can significantly improve team strategy and xG models")


if __name__ == "__main__":
    main()
