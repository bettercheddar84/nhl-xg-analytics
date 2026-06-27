"""
Calculate missing statistics and cross-sport analytics features
These are stats you have the data for but haven't calculated yet
"""

import pandas as pd
import numpy as np
import networkx as nx
from typing import Dict, Union


class AdvancedStatsCalculator:
    """Calculate missing advanced statistics from existing data"""

    def __init__(self):
        self.shots_df: Union[pd.DataFrame, None] = None
        self.shifts_df: Union[pd.DataFrame, None] = None
        self.players_df: Union[pd.DataFrame, None] = None

    def calculate_player_gravity(self, player_id: int) -> float:
        """
        NBA-style gravity score - how much defensive attention does player draw?
        High gravity players create space for teammates
        """

        if self.shots_df is None:
            return 0

        # When player is on ice
        mask = self.shots_df["offensive_on_ice"].notna()
        on_ice_shots = self.shots_df[mask & self.shots_df["offensive_on_ice"].str.contains(str(player_id), na=False)]

        # Shots by teammates when player on ice
        teammate_shots = on_ice_shots[on_ice_shots["shooter_id"] != player_id]

        if len(teammate_shots) == 0:
            return 0

        # Quality of teammate shots (higher = player draws defenders)
        teammate_shot_quality = teammate_shots["shot_distance"].mean()
        teammate_xg = teammate_shots["location_danger_score"].mean()

        # Assist to shot ratio (high = creates for others)
        player_assists = on_ice_shots[
            (on_ice_shots["assist1_id"] == player_id) | (on_ice_shots["assist2_id"] == player_id)
        ].shape[0]

        player_shots = on_ice_shots[on_ice_shots["shooter_id"] == player_id].shape[0]

        assist_ratio = player_assists / (player_shots + 1)  # Avoid division by zero

        # Gravity score combines space creation and playmaking
        gravity_score = (
            (30 - teammate_shot_quality) / 30 * 0.4  # Closer shots = more gravity
            + teammate_xg * 0.4  # Higher danger = more gravity
            + min(assist_ratio, 2) / 2 * 0.2  # Playmaking tendency
        )

        return gravity_score

    def calculate_true_shooting_percentage(self, player_id: int) -> Dict[str, float]:
        """
        Basketball-style true shooting % - adjusts for shot quality
        """
        if self.shots_df is None:
            return {"true_shooting_pct": 0, "regular_shooting_pct": 0, "shot_selection_quality": 0}

        player_shots = self.shots_df[self.shots_df["shooter_id"] == player_id]

        if len(player_shots) == 0:
            return {"true_shooting_pct": 0, "regular_shooting_pct": 0, "shot_selection_quality": 0}

        goals = player_shots["is_goal"].sum()
        regular_shooting_pct = player_shots["is_goal"].mean()

        # Sum of xG represents "expected makes"
        expected_goals = player_shots["location_danger_score"].sum()

        # True shooting = actual goals / expected goals
        true_shooting_pct = goals / (expected_goals + 1)

        # Shot selection quality
        avg_shot_quality = player_shots["location_danger_score"].mean()

        return {
            "true_shooting_pct": true_shooting_pct,
            "regular_shooting_pct": regular_shooting_pct,
            "shot_selection_quality": avg_shot_quality,
            "shot_selection_rating": true_shooting_pct / (regular_shooting_pct + 0.001),
        }

    def calculate_usage_rate(self, player_id: int) -> float:
        """
        NBA-style usage rate - what % of team's offense runs through player?
        """
        if self.shots_df is None:
            return 0

        # When player is on ice
        mask = self.shots_df["offensive_on_ice"].notna()
        on_ice_events = self.shots_df[mask & self.shots_df["offensive_on_ice"].str.contains(str(player_id), na=False)]

        if len(on_ice_events) == 0:
            return 0

        # Player's direct involvement (shots + primary assists)
        player_usage_events = on_ice_events[
            (on_ice_events["shooter_id"] == player_id) | (on_ice_events["assist1_id"] == player_id)
        ].shape[0]

        total_team_events = len(on_ice_events)

        usage_rate = player_usage_events / total_team_events

        return usage_rate

    def calculate_clutch_rating(self, player_id: int) -> Dict[str, float]:
        """
        Performance in high-leverage situations
        """
        if self.shots_df is None:
            return {"clutch_rating": 1.0, "clutch_shooting": 0, "regular_shooting": 0}

        # Define clutch situations
        clutch_shots = self.shots_df[
            (self.shots_df["shooter_id"] == player_id)
            & (self.shots_df["time_remaining"] < 300)  # Last 5 minutes
            & (abs(self.shots_df["score_differential"]) <= 1)  # Close game
            & (self.shots_df["period"] >= 3)  # 3rd period or OT
        ]

        regular_shots = self.shots_df[
            (self.shots_df["shooter_id"] == player_id) & ~self.shots_df.index.isin(clutch_shots.index)
        ]

        if len(clutch_shots) < 5:  # Need minimum sample
            return {"clutch_rating": 1.0, "clutch_shooting": 0, "regular_shooting": 0}

        clutch_shooting = clutch_shots["is_goal"].mean()
        regular_shooting = regular_shots["is_goal"].mean() if len(regular_shots) > 0 else 0

        # Expected performance in clutch
        clutch_xg = clutch_shots["location_danger_score"].mean()

        # Clutch rating: actual vs expected in big moments
        clutch_rating = clutch_shooting / (clutch_xg + 0.001)

        return {
            "clutch_rating": clutch_rating,
            "clutch_shooting": clutch_shooting,
            "regular_shooting": regular_shooting,
            "clutch_lift": clutch_shooting - regular_shooting,
            "clutch_shots": len(clutch_shots),
        }

    def calculate_shooting_babip(self, player_id: int) -> float:
        """
        Baseball-style BABIP - shooting % on shots that hit the net
        Like "batting average on balls in play"
        """
        if self.shots_df is None:
            return 0

        player_shots = self.shots_df[self.shots_df["shooter_id"] == player_id]

        # Shots that weren't blocked or missed
        shots_on_net = player_shots[~player_shots["event_type"].isin(["missed-shot", "blocked-shot"])]

        if len(shots_on_net) == 0:
            return 0

        # Goals per shot on net (excludes misses/blocks)
        babip = shots_on_net["is_goal"].mean()

        # League average is ~0.09 for all shots, but ~0.30 for shots on net
        return babip

    def calculate_win_probability_added(self, shot: pd.Series) -> float:
        """
        MLB/NFL-style WPA - how much did this shot change win probability?
        """

        def win_probability(score_diff: int, time_remaining: int, is_pp: bool = False) -> float:
            """Simple win probability model"""
            # Ensure we're working with integers
            score_diff = int(score_diff)
            time_remaining = int(time_remaining)

            # Base win probability from score differential
            base_wp = 1 / (1 + np.exp(-0.5 * score_diff))

            # Time adjustment (less time = more certain)
            time_factor = 1 - (time_remaining / 3600)  # 60 minutes
            wp = base_wp * (1 + time_factor) / 2

            # Power play adjustment
            if is_pp and score_diff >= 0:
                wp += 0.05
            elif is_pp and score_diff < 0:
                wp += 0.10

            return np.clip(wp, 0.01, 0.99)

        # Helper to ensure non-None integer
        def get_int(series: pd.Series, key: str, default: int) -> int:
            val = series.get(key, default)
            return default if val is None else int(val)

        # Pre-shot win probability - use helper to ensure non-None
        score_diff = get_int(shot, "score_differential", 0)
        time_remaining = get_int(shot, "time_remaining", 1800)
        is_pp = bool(shot.get("is_powerplay", False) or False)

        pre_wp = win_probability(int(score_diff), int(time_remaining), is_pp)  # type: ignore

        # Post-shot win probability
        if shot.get("is_goal", False):
            post_wp = win_probability(score_diff + 1, time_remaining, False)
        else:
            # Even missed shots have small impact
            post_wp = pre_wp * 0.99  # Slight decrease from missed opportunity

        return post_wp - pre_wp

    def calculate_defensive_rating_forwards(self, player_id: int) -> Dict[str, float]:
        """
        NBA-style defensive rating for forwards
        """
        if self.shots_df is None:
            return {"defensive_rating": 100, "xga_per_60": 0}

        # Shots against when player on ice
        mask = self.shots_df["defensive_on_ice"].notna()
        defensive_events = self.shots_df[
            mask & self.shots_df["defensive_on_ice"].str.contains(str(player_id), na=False)
        ]

        if len(defensive_events) == 0:
            return {"defensive_rating": 100, "xga_per_60": 0}

        # Expected goals against per 60
        xga = defensive_events["location_danger_score"].sum()

        # Get ice time (would need to calculate from shifts)
        # For now, estimate from number of events
        estimated_minutes = len(defensive_events) / 20  # Rough estimate

        xga_per_60 = (xga / estimated_minutes) * 60 if estimated_minutes > 0 else 0

        # Defensive rating (lower is better, 100 is average)
        league_avg_xga_per_60 = 2.5  # Example
        defensive_rating = (xga_per_60 / league_avg_xga_per_60) * 100

        # Takeaways and blocked shots boost rating
        # Would need to identify these from play-by-play

        return {"defensive_rating": defensive_rating, "xga_per_60": xga_per_60, "shots_against": len(defensive_events)}

    def calculate_chaos_factor(self, game_id: str, period: int = None) -> float:
        """
        Measure of game/period chaos - broken structure leads to different xG
        """
        if self.shots_df is None:
            return 0

        if period:
            game_events = self.shots_df[(self.shots_df["game_id"] == game_id) & (self.shots_df["period"] == period)]
        else:
            game_events = self.shots_df[self.shots_df["game_id"] == game_id]

        if len(game_events) < 2:
            return 0

        # Events per minute
        time_span = game_events["game_seconds"].max() - game_events["game_seconds"].min()
        events_per_minute = len(game_events) / (time_span / 60) if time_span > 0 else 0

        # Average distance between consecutive events
        event_distances = []
        for i in range(1, len(game_events)):
            if pd.notna(game_events.iloc[i]["x_coord"]) and pd.notna(game_events.iloc[i - 1]["x_coord"]):
                dist = np.sqrt(
                    (game_events.iloc[i]["x_coord"] - game_events.iloc[i - 1]["x_coord"]) ** 2
                    + (game_events.iloc[i]["y_coord"] - game_events.iloc[i - 1]["y_coord"]) ** 2
                )
                event_distances.append(dist)

        avg_distance = np.mean(event_distances) if event_distances else 0

        # Possession changes (team switches)
        possession_changes = 0
        for i in range(1, len(game_events)):
            if game_events.iloc[i]["shooting_team"] != game_events.iloc[i - 1]["shooting_team"]:
                possession_changes += 1

        changes_per_minute = possession_changes / (time_span / 60) if time_span > 0 else 0

        # Chaos score combines all factors
        chaos_factor = (
            events_per_minute / 3 * 0.3  # Normalized by typical rate
            + avg_distance / 50 * 0.3  # Normalized by rink size
            + changes_per_minute / 2 * 0.4  # Normalized by typical rate
        )

        return float(chaos_factor)

    def calculate_momentum_score(self, team: str, game_id: str, current_time: int) -> float:
        """
        Comprehensive momentum calculation beyond just recent goals
        """
        if self.shots_df is None:
            return 0.5

        recent_window = 300  # 5 minutes

        recent_events = self.shots_df[
            (self.shots_df["game_id"] == game_id)
            & (self.shots_df["game_seconds"] >= current_time - recent_window)
            & (self.shots_df["game_seconds"] < current_time)
        ]

        if len(recent_events) == 0:
            return 0.5  # Neutral momentum

        team_events = recent_events[recent_events["shooting_team"] == team]
        opponent_events = recent_events[recent_events["shooting_team"] != team]

        # Components of momentum
        components = {
            "goals": team_events["is_goal"].sum() - opponent_events["is_goal"].sum(),
            "shots": len(team_events) - len(opponent_events),
            "shot_quality": (team_events["location_danger_score"].mean() if len(team_events) > 0 else 0)
            - (opponent_events["location_danger_score"].mean() if len(opponent_events) > 0 else 0),
            "zone_time": (
                team_events["offensive_zone_time"].mean()
                if len(team_events) > 0 and "offensive_zone_time" in team_events.columns
                else 0
            ),
        }

        # Weight components
        momentum_score = (
            np.tanh(components["goals"] * 0.5) * 0.4  # Goals most important, tanh to cap effect
            + np.tanh(components["shots"] / 10) * 0.2  # Shot volume
            + components["shot_quality"] * 0.2  # Shot quality
            + min(components["zone_time"] / 30, 1) * 0.2  # Sustained pressure
        )

        # Convert to 0-1 scale
        return (momentum_score + 1) / 2

    def calculate_passing_network_centrality(self, team: str, game_id: str) -> Dict[int, float]:
        """
        Network analysis of passing patterns - who are the key playmakers?
        """
        if self.shots_df is None:
            return {}

        game_events = self.shots_df[(self.shots_df["game_id"] == game_id) & (self.shots_df["shooting_team"] == team)]

        # Build passing network
        G = nx.DiGraph()

        for _, event in game_events.iterrows():
            if pd.notna(event.get("assist1_id")):
                # Add edge from assist1 to shooter
                G.add_edge(event["assist1_id"], event["shooter_id"], weight=1)

                if pd.notna(event.get("assist2_id")):
                    # Add edge from assist2 to assist1
                    G.add_edge(event["assist2_id"], event["assist1_id"], weight=1)

        if len(G.nodes()) == 0:
            return {}

        # Calculate centrality metrics
        centrality = nx.betweenness_centrality(G)

        # Normalize to 0-1 scale
        max_centrality = max(centrality.values()) if centrality else 1
        normalized_centrality = {player: score / max_centrality for player, score in centrality.items()}

        return normalized_centrality

    def calculate_expected_assists(self, player_id: int) -> Dict[str, float]:
        """
        xA - Expected assists based on quality of chances created
        """
        if self.shots_df is None:
            return {"expected_assists": 0, "actual_assists": 0, "assist_quality": 0}

        # Find all shots where player had primary assist
        assisted_shots = self.shots_df[self.shots_df["assist1_id"] == player_id]

        if len(assisted_shots) == 0:
            return {"expected_assists": 0, "actual_assists": 0, "assist_quality": 0}

        # Sum of xG from shots they set up
        expected_assists = assisted_shots["location_danger_score"].sum()
        actual_assists = assisted_shots["is_goal"].sum()

        # Quality of chances created
        avg_chance_quality = assisted_shots["location_danger_score"].mean()

        return {
            "expected_assists": expected_assists,
            "actual_assists": actual_assists,
            "assist_luck": actual_assists - expected_assists,
            "assist_quality": avg_chance_quality,
            "assists_above_expected": actual_assists / (expected_assists + 0.001),
        }

    def calculate_shot_approach_patterns(self, player_id: int) -> Dict[str, Union[float, str]]:
        """
        How player approaches shooting positions (like route running in NFL)
        """
        if self.shots_df is None:
            return {}

        player_shots = self.shots_df[self.shots_df["shooter_id"] == player_id]

        if len(player_shots) == 0:
            return {}

        patterns = {
            "straight_line": 0,  # Direct approach (rush)
            "curl_and_drag": 0,  # Around defense
            "give_and_go": 0,  # Pass and relocate
            "off_the_cycle": 0,  # From below goal line
            "point_blast": 0,  # From blue line
        }

        for _, shot in player_shots.iterrows():
            # Classify based on shot characteristics
            if shot.get("is_rush", False):
                patterns["straight_line"] += 1
            elif shot.get("prev_event_type") == "Pass" and shot.get("time_since_prev_event", float("inf")) < 2:
                patterns["give_and_go"] += 1
            elif shot.get("shot_distance", 0) > 50:
                patterns["point_blast"] += 1
            elif abs(shot.get("y_coord", 0)) > 30:
                patterns["off_the_cycle"] += 1
            else:
                patterns["curl_and_drag"] += 1

        # Normalize to percentages
        total_shots = sum(patterns.values())
        pattern_percentages: Dict[str, Union[float, str]] = {
            pattern: count / total_shots for pattern, count in patterns.items()
        }

        # Find signature move
        if patterns:
            signature_pattern = max(patterns, key=lambda k: patterns[k])
            pattern_percentages["signature_move"] = signature_pattern
            pattern_percentages["signature_frequency"] = float(patterns[signature_pattern] / total_shots)
        else:
            pattern_percentages["signature_move"] = "unknown"
            pattern_percentages["signature_frequency"] = 0.0

        return pattern_percentages


def main():
    """Calculate missing stats for all players"""

    calculator = AdvancedStatsCalculator()

    # Load data
    print("Loading data...")
    calculator.shots_df = pd.read_csv("data/nhl/processed/training_data_enhanced.csv")

    # Get unique players
    all_players = (
        pd.concat(
            [calculator.shots_df["shooter_id"], calculator.shots_df["assist1_id"], calculator.shots_df["assist2_id"]]
        )
        .dropna()
        .unique()
    )

    print("Calculating advanced stats for {} players...".format(len(all_players)))

    # Calculate all advanced stats
    results = []

    for player_id in all_players[:100]:  # Start with first 100 players
        player_stats = {
            "player_id": player_id,
            "gravity_score": calculator.calculate_player_gravity(player_id),
            "usage_rate": calculator.calculate_usage_rate(player_id),
            "shooting_babip": calculator.calculate_shooting_babip(player_id),
        }

        # Add true shooting stats
        true_shooting = calculator.calculate_true_shooting_percentage(player_id)
        player_stats.update(true_shooting)

        # Add clutch stats
        clutch = calculator.calculate_clutch_rating(player_id)
        player_stats.update(clutch)

        # Add expected assists
        xa = calculator.calculate_expected_assists(player_id)
        player_stats.update(xa)

        results.append(player_stats)

    # Save results
    advanced_stats_df = pd.DataFrame(results)
    advanced_stats_df.to_csv("data/nhl/processed/advanced_player_stats.csv", index=False)

    print("\nTop 10 players by gravity score:")
    print(advanced_stats_df.nlargest(10, "gravity_score")[["player_id", "gravity_score", "usage_rate"]])

    print("\nMost clutch players:")
    clutch_players = advanced_stats_df[advanced_stats_df["clutch_shots"] >= 10]
    print(clutch_players.nlargest(10, "clutch_rating")[["player_id", "clutch_rating", "clutch_lift"]])

    print("\nBest playmakers (xA):")
    playmakers = advanced_stats_df[advanced_stats_df["expected_assists"] > 0]
    print(
        playmakers.nlargest(10, "expected_assists")[["player_id", "expected_assists", "actual_assists", "assist_luck"]]
    )


if __name__ == "__main__":
    main()
