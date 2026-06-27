"""
Player-Specific Shot Decision Analyzer
Helps individual players understand their personal shot selection impact
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List


class PlayerShotAnalyzer:
    """Analyze individual player shot decisions and outcomes"""

    def __init__(self):
        self.shots_df = None

    def load_data(self):
        """Load shot data"""
        self.shots_df = pd.read_csv("data/nhl/processed/training_data_enhanced.csv")

    def analyze_player(self, player_id: int, player_name: str = "") -> Dict:
        """Comprehensive analysis for individual player"""

        if self.shots_df is None:
            return {"error": "Data not loaded"}

        player_shots = self.shots_df[self.shots_df["shooter_id"] == player_id]

        if len(player_shots) < 20:
            return {"error": "Not enough shots for analysis"}

        print("\nPLAYER SHOT DECISION ANALYSIS")
        print(f"Player: {player_name or f'ID {player_id}'}")
        print("=" * 60)

        # 1. Personal shooting tendencies
        tendencies = self.analyze_tendencies(player_shots)

        # 2. Situational decision making
        situations = self.analyze_situations(player_shots)

        # 3. Shot quality progression
        progression = self.analyze_progression(player_shots)

        # 4. Personal recommendations
        recommendations = self.generate_personal_recommendations(player_shots, tendencies, situations.get("stats", []))

        return {
            "tendencies": tendencies,
            "situations": situations,
            "progression": progression,
            "recommendations": recommendations,
        }

    def analyze_tendencies(self, player_shots: pd.DataFrame) -> Dict:
        """Analyze player's shooting tendencies"""

        # Calculate zones where player shoots from
        player_shots["zone"] = pd.cut(
            player_shots["shot_distance"], bins=[0, 15, 30, 45, 100], labels=["Slot", "Mid-range", "Point", "Deep"]
        )

        zone_stats = []
        for zone in ["Slot", "Mid-range", "Point", "Deep"]:
            zone_shots = player_shots[player_shots["zone"] == zone]
            if len(zone_shots) > 0:
                zone_stats.append(
                    {
                        "zone": zone,
                        "shots": len(zone_shots),
                        "goals": zone_shots["is_goal"].sum(),
                        "shooting_pct": zone_shots["is_goal"].mean(),
                        "avg_xg": (
                            zone_shots["location_danger_score"].mean() if "location_danger_score" in zone_shots else 0
                        ),
                        "miss_rate": (
                            (zone_shots["event_type"] == "missed-shot").mean() if "event_type" in zone_shots else 0
                        ),
                    }
                )

        print("\nSHOOTING ZONES:")
        zone_df = pd.DataFrame(zone_stats)
        print(zone_df.to_string(index=False))

        # Identify problem areas
        problem_zones = []
        for stat in zone_stats:
            if stat["shooting_pct"] < stat["avg_xg"] * 0.7:  # Underperforming xG by 30%+
                problem_zones.append(stat["zone"])

        # Shot type preferences
        shot_types = player_shots["shot_type"].value_counts()
        primary_shot = shot_types.index[0] if len(shot_types) > 0 else "Unknown"

        return {
            "zone_stats": zone_stats,
            "problem_zones": problem_zones,
            "primary_shot_type": primary_shot,
            "shot_distribution": shot_types.to_dict(),
        }

    def analyze_situations(self, player_shots: pd.DataFrame) -> Dict:
        """Analyze decision making in different game situations"""

        situations = {
            "Leading": player_shots[player_shots["score_differential"] > 0],
            "Tied": player_shots[player_shots["score_differential"] == 0],
            "Trailing": player_shots[player_shots["score_differential"] < 0],
            "Late & Close": player_shots[
                (player_shots["time_remaining"] < 300) & (abs(player_shots["score_differential"]) <= 1)
            ],
        }

        print("\nSITUATIONAL PERFORMANCE:")
        print("-" * 40)

        situation_stats = []
        for name, shots in situations.items():
            if len(shots) > 5:
                avg_quality = shots["location_danger_score"].mean() if "location_danger_score" in shots else 0
                shooting_pct = shots["is_goal"].mean()

                # Key insight: Does player force shots when trailing?
                avg_distance = shots["shot_distance"].mean()

                situation_stats.append(
                    {
                        "situation": name,
                        "shots": len(shots),
                        "avg_distance": avg_distance,
                        "avg_quality": avg_quality,
                        "shooting_pct": shooting_pct,
                        "forced_shots": avg_distance > 40,  # Forcing from distance
                    }
                )

                print(f"{name}: {len(shots)} shots, {avg_distance:.1f}ft avg, {shooting_pct:.1%} success")

        return {"stats": situation_stats}

    def analyze_progression(self, player_shots: pd.DataFrame) -> Dict:
        """Analyze if player's shot selection is improving over time"""

        # Sort by game date
        player_shots_sorted = player_shots.sort_values("game_id")

        # Split into early and recent
        midpoint = len(player_shots_sorted) // 2
        early_shots = player_shots_sorted.iloc[:midpoint]
        recent_shots = player_shots_sorted.iloc[midpoint:]

        print("\nSHOT SELECTION EVOLUTION:")
        print("-" * 40)

        early_stats = {
            "avg_distance": early_shots["shot_distance"].mean(),
            "avg_quality": early_shots["location_danger_score"].mean() if "location_danger_score" in early_shots else 0,
            "shooting_pct": early_shots["is_goal"].mean(),
        }

        recent_stats = {
            "avg_distance": recent_shots["shot_distance"].mean(),
            "avg_quality": (
                recent_shots["location_danger_score"].mean() if "location_danger_score" in recent_shots else 0
            ),
            "shooting_pct": recent_shots["is_goal"].mean(),
        }

        print(f"Early Season: {early_stats['avg_distance']:.1f}ft, {early_stats['shooting_pct']:.1%}")
        print(f"Recent Games: {recent_stats['avg_distance']:.1f}ft, {recent_stats['shooting_pct']:.1%}")

        improvement = {
            "distance_change": recent_stats["avg_distance"] - early_stats["avg_distance"],
            "quality_change": recent_stats["avg_quality"] - early_stats["avg_quality"],
            "shooting_pct_change": recent_stats["shooting_pct"] - early_stats["shooting_pct"],
            "improving": recent_stats["avg_quality"] > early_stats["avg_quality"],
        }

        if improvement["improving"]:
            print("✓ Shot selection is IMPROVING")
        else:
            print("⚠ Shot selection needs work")

        return improvement

    def generate_personal_recommendations(
        self, player_shots: pd.DataFrame, tendencies: Dict, situations: List[Dict]
    ) -> Dict:
        """Generate personalized recommendations"""

        print("\nPERSONALIZED RECOMMENDATIONS:")
        print("=" * 60)

        recommendations = []

        # 1. Zone-specific advice
        for zone_stat in tendencies["zone_stats"]:
            if zone_stat["miss_rate"] > 0.3 and zone_stat["zone"] in ["Point", "Deep"]:
                recommendations.append(
                    f"ACCURACY: Work on hitting the net from {zone_stat['zone']} "
                    f"(currently missing {zone_stat['miss_rate']:.0%})"
                )

        # 2. Situation-specific advice
        trailing_stats = next((s for s in situations if s["situation"] == "Trailing"), None)
        if trailing_stats and trailing_stats.get("forced_shots"):
            recommendations.append("PATIENCE: When trailing, work puck closer instead of forcing long shots")

        # 3. Shot type optimization
        if len(tendencies["shot_distribution"]) > 1:
            shot_success = {}
            for shot_type in tendencies["shot_distribution"]:
                type_shots = player_shots[player_shots["shot_type"] == shot_type]
                if len(type_shots) > 10:
                    shot_success[shot_type] = type_shots["is_goal"].mean()

            if shot_success:
                best_shot = max(shot_success, key=lambda x: shot_success[x])
                if best_shot != tendencies["primary_shot_type"]:
                    recommendations.append(
                        f"SHOT TYPE: Your {best_shot} is more effective "
                        f"({shot_success[best_shot]:.1%}) than your go-to {tendencies['primary_shot_type']}"
                    )

        # 4. High-value situations
        rush_shots = player_shots[player_shots["is_rush"]] if "is_rush" in player_shots.columns else pd.DataFrame()
        if len(rush_shots) < 5:
            recommendations.append("OPPORTUNITY: Look to shoot more on rush chances (high-value situations)")

        # 5. Net-front presence
        close_shots = player_shots[player_shots["shot_distance"] < 15]
        if len(close_shots) / len(player_shots) < 0.2:
            recommendations.append(
                "POSITIONING: Get to the net more - only {:.0%} of your shots are from prime scoring area".format(
                    len(close_shots) / len(player_shots)
                )
            )

        for i, rec in enumerate(recommendations[:5], 1):  # Top 5 recommendations
            print(f"{i}. {rec}")

        return {"recommendations": recommendations}

    def create_player_heatmap(self, player_id: int, player_name: str = ""):
        """Create visual heatmap of player's shooting patterns"""

        if self.shots_df is None:
            print("Data not loaded")
            return

        player_shots = self.shots_df[self.shots_df["shooter_id"] == player_id]

        if len(player_shots) < 20:
            print("Not enough shots for heatmap")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Shot locations
        goals = player_shots[player_shots["is_goal"]]
        misses = player_shots[~player_shots["is_goal"]]

        ax1.scatter(misses["x_coord"], misses["y_coord"], alpha=0.5, s=30, c="blue", label="Saved/Missed")
        ax1.scatter(goals["x_coord"], goals["y_coord"], alpha=0.8, s=100, c="red", marker="*", label="Goals")
        ax1.set_xlim(-100, 100)
        ax1.set_ylim(-50, 50)
        ax1.set_title(f'{player_name or f"Player {player_id}"} - Shot Locations')
        ax1.legend()

        # Success rate by zone
        zones = ["Slot\n<15ft", "Mid-range\n15-30ft", "Point\n30-45ft", "Deep\n45ft+"]
        zone_success = []
        zone_volume = []

        for zone, (min_dist, max_dist) in zip(zones, [(0, 15), (15, 30), (30, 45), (45, 100)]):
            zone_shots = player_shots[
                (player_shots["shot_distance"] >= min_dist) & (player_shots["shot_distance"] < max_dist)
            ]
            if len(zone_shots) > 0:
                zone_success.append(zone_shots["is_goal"].mean() * 100)
                zone_volume.append(len(zone_shots))
            else:
                zone_success.append(0)
                zone_volume.append(0)

        x = np.arange(len(zones))
        width = 0.35

        ax2.bar(x - width / 2, zone_success, width, label="Shooting %", color="green", alpha=0.7)
        ax2.bar(x + width / 2, zone_volume, width, label="Shot Volume", color="blue", alpha=0.7)
        ax2.set_xlabel("Zone")
        ax2.set_ylabel("Percentage / Count")
        ax2.set_title("Performance by Zone")
        ax2.set_xticks(x)
        ax2.set_xticklabels(zones)
        ax2.legend()

        plt.tight_layout()
        plt.savefig(f"models/player_{player_id}_analysis.png", dpi=300)
        print(f"\nHeatmap saved to models/player_{player_id}_analysis.png")


def analyze_team_individuals(team_name: str = "PIT"):
    """Analyze all players on a team"""

    analyzer = PlayerShotAnalyzer()
    analyzer.load_data()

    # Get team players
    if analyzer.shots_df is None:
        print("Failed to load data")
        return

    team_shots = analyzer.shots_df[analyzer.shots_df["shooting_team"] == team_name]

    # Top 10 shooters by volume
    top_shooters = team_shots["shooter_id"].value_counts().head(10)

    print(f"\n{team_name} INDIVIDUAL PLAYER ANALYSIS")
    print("=" * 60)

    team_insights = []

    # Convert to list for easier handling
    player_list = [(pid, count) for pid, count in top_shooters.items()]

    for player_id, shot_count in player_list:
        if shot_count > 30:  # Minimum shots for analysis
            print(f"\n\nAnalyzing Player {player_id} ({shot_count} shots)...")

            # Ensure player_id is int
            try:
                pid = int(str(player_id))
            except (ValueError, TypeError):
                continue

            analysis = analyzer.analyze_player(pid)

            # Create heatmap for top 3 shooters
            if len(team_insights) < 3:
                analyzer.create_player_heatmap(pid)

            team_insights.append(
                {
                    "player_id": player_id,
                    "shots": shot_count,
                    "recommendations": analysis.get("recommendations", {}).get("recommendations", [])[
                        :2
                    ],  # Top 2 per player
                }
            )

    # Team-wide patterns
    print("\n\nTEAM-WIDE PATTERNS:")
    print("=" * 60)

    all_recs = []
    for player in team_insights:
        all_recs.extend(player["recommendations"])

    # Find common issues
    common_issues = {}
    for rec in all_recs:
        key = rec.split(":")[0]
        common_issues[key] = common_issues.get(key, 0) + 1

    print("Most common areas for improvement:")
    for issue, count in sorted(common_issues.items(), key=lambda x: x[1], reverse=True):
        print(f"- {issue}: {count} players")


if __name__ == "__main__":
    # Example: Analyze Sidney Crosby
    analyzer = PlayerShotAnalyzer()
    analyzer.load_data()

    # Crosby's player ID (example - would need real ID)
    crosby_id = 8471675
    analysis = analyzer.analyze_player(crosby_id, "Sidney Crosby")
    analyzer.create_player_heatmap(crosby_id, "Sidney Crosby")

    # Analyze whole team
    analyze_team_individuals("PIT")
