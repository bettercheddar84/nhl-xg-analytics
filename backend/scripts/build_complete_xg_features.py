 
    # Basic quality metrics
    off_plus_minus = off_players["plus_minus"].sum() if len(off_players) > 0 else 0
    def_plus_minus = def_players["plus_minus"].sum() if len(def_players) > 0 else 0

    # Elite player counts
    elite_shooters = len(off_players[off_players["elite_scorer"]])
    weak_defenders = len(def_players[def_players["plus_minus"] < -10])

    # Physical mismatches
    avg_off_height = (
        off_players["height"].mean() if len(off_players) > 0 and not off_players["height"].isna().all() else 72
    )
    avg_def_height = (
        def_players["height"].mean() if len(def_players) > 0 and not def_players["height"].isna().all() else 72
    )

    # Get advanced stats from MoneyPuck data
    off_xg_impact = 0
    def_xg_impact = 0

    if len(offensive_ids) > 0:
        off_stats = player_stats[player_stats["playerId"].isin(offensive_ids)]
        if len(off_stats) > 0:
            off_xg_impact = off_stats["onIce_xGoalsPercentage"].mean()

    if len(defensive_ids) > 0:
        def_stats = player_stats[player_stats["playerId"].isin(defensive_ids)]
        if len(def_stats) > 0:
            def_xg_impact = def_stats["onIce_xGoalsPercentage"].mean()

    return {
        "offensive_quality_sum": off_plus_minus,
        "defensive_quality_sum": def_plus_minus,
        "quality_differential": off_plus_minus - def_plus_minus,
        "elite_shooters_on_ice": elite_shooters,
        "weak_defenders_on_ice": weak_defenders,
        "height_advantage": avg_off_height - avg_def_height,
        "offensive_xg_impact": off_xg_impact,
        "defensive_xg_impact": def_xg_impact,
        "xg_differential": off_xg_impact - def_xg_impact,
    }


def calculate_shot_consequences(shot_df: pd.DataFrame, window_seconds: int = 10) -> pd.DataFrame:
    """Track what happens after each shot within time window"""

    consequences = []

    for idx, shot in shot_df.iterrows():
        game_shots = shot_df[shot_df["game_id"] == shot["game_id"]]

        # Find events after this shot
        future_events = game_shots[
            (game_shots["game_seconds"] > shot["game_seconds"])
            & (game_shots["game_seconds"] <= shot["game_seconds"] + window_seconds)
        ]

        # Check for fast break
        opponent_shots = future_events[future_events["shooting_team"] != shot["shooting_team"]]
        led_to_opponent_shot = len(opponent_shots) > 0
        time_to_opponent_shot = (
            opponent_shots.iloc[0]["game_seconds"] - shot["game_seconds"] if led_to_opponent_shot else None
        )

        # Check for rebound
        same_team_shots = future_events[future_events["shooting_team"] == shot["shooting_team"]]
        created_rebound = len(same_team_shots) > 0 and shot["is_goal"] == 0

        # Rim around danger (for missed shots)
        rim_danger = 0
        if shot["is_goal"] == 0 and shot["y_coord"] is not None:
            # Shots that miss wide are more dangerous
            rim_danger = abs(shot["y_coord"]) / 42.5  # Normalized by rink width

        consequences.append(
            {
                "shot_index": idx,
                "led_to_opponent_shot": led_to_opponent_shot,
                "time_to_opponent_shot": time_to_opponent_shot,
                "created_rebound_chance": created_rebound,
                "rim_around_danger": rim_danger,
                "fast_break_risk": (
                    1
                    if (led_to_opponent_shot and time_to_opponent_shot is not None and time_to_opponent_shot < 5)
                    else 0
                ),
            }
        )

    return pd.DataFrame(consequences)


def calculate_royal_road_pass(shot_df: pd.DataFrame) -> pd.Series:
    """Detect royal road passes (cross-slot passes)"""

    # Royal road = pass crossed the slot (x coordinates have opposite signs)
    # and pass went through high-danger area (y coordinates < 20)
    royal_road = (
        (shot_df["prev_event_x"] * shot_df["x_coord"] < 0)  # Opposite sides
        & (abs(shot_df["prev_event_y"]) < 20)  # Through slot
        & (abs(shot_df["y_coord"]) < 20)  # Shot from slot
        & (shot_df["prev_event_type"] == "Pass")
    )

    return royal_road.astype(int)


def calculate_screen_quality(shot_df: pd.DataFrame, player_tiers: pd.DataFrame) -> pd.DataFrame:
    """Calculate screening effectiveness"""

    screen_quality = []

    for idx, shot in shot_df.iterrows():
        if pd.notna(shot.get("blocker_id")):
            blocker = player_tiers[player_tiers["player_id"] == shot["blocker_id"]]
            if len(blocker) > 0:
                # Screen quality based on size and position
                screener_size = blocker.iloc[0]["height"] * blocker.iloc[0]["weight"]
                # Assume screener is near crease (8-15 feet from net)
                screen_distance = 10
                quality = screener_size / (screen_distance * 100)  # Normalize
            else:
                quality = 0
        else:
            quality = 0

        screen_quality.append(quality)

    return pd.DataFrame({"screen_quality": screen_quality})


def load_player_embeddings(player_ids: List[int]) -> Dict[int, np.ndarray]:
    """Load player career stats for embeddings"""

    embeddings = {}

    for player_id in player_ids:
        try:
            with open(f"data/nhl/players/{player_id}.json", "r") as f:
                player_data = json.load(f)

            # Create embedding from career stats
            stats = player_data.get("careerTotals", {}).get("regularSeason", {})

            embedding = np.array(
                [
                    stats.get("gamesPlayed", 0) / 1000,  # Normalize
                    stats.get("goals", 0) / 500,
                    stats.get("assists", 0) / 1000,
                    stats.get("points", 0) / 1500,
                    stats.get("plusMinus", 0) / 100,
                    stats.get("shootingPctg", 0),
                    player_data.get("heightInInches", 72) / 80,
                    player_data.get("weightInPounds", 200) / 250,
                ]
            )

            embeddings[player_id] = embedding

        except FileNotFoundError:
            # Default embedding for missing players
            embeddings[player_id] = np.zeros(8)

    return embeddings


def main():
    """Build complete feature set for xG model"""

    print("Loading base shot data...")
    # Load your most complete shot dataset
    shots_df = pd.read_csv("data/nhl/processed/training_data_with_assists.csv")

    print("Loading supporting data...")
    # Load additional data sources
    player_tiers = pd.read_csv("data/nhl/processed/player_tiers.csv")
    skaters = pd.read_csv("data/nhl/aggregated_data_moneypuck/skaters.csv")
    goalies = pd.read_csv("data/nhl/aggregated_data_moneypuck/goalies.csv")
    teams = pd.read_csv("data/nhl/aggregated_data_moneypuck/teams.csv")
    # lines = pd.read_csv("data/nhl/aggregated_data_moneypuck/lines.csv")  # Removed unused variable

    # Load on-ice data
    shots_on_ice = pd.read_csv("data/nhl/shifts/shots_with_on_ice.csv")

    print("Calculating shot consequences...")
    # Add shot consequence features
    consequences = calculate_shot_consequences(shots_df)
    shots_df = pd.concat([shots_df, consequences.set_index("shot_index")], axis=1)

    print("Calculating on-ice quality for all shots...")
    # Merge with on-ice data
    shots_df = shots_df.merge(
        shots_on_ice[["game_id", "shot_time", "offensive_on_ice", "defensive_on_ice"]],
        left_on=["game_id", "game_seconds"],
        right_on=["game_id", "shot_time"],
        how="left",
    )

    # Calculate on-ice quality
    quality_features = []
    for idx, shot in shots_df.iterrows():
        if pd.notna(shot.get("offensive_on_ice")):
            off_ids = extract_player_ids_from_string(shot["offensive_on_ice"])
            def_ids = extract_player_ids_from_string(shot["defensive_on_ice"])
            quality = calculate_on_ice_quality(off_ids, def_ids, player_tiers, skaters)
        else:
            quality = {
                k: 0
                for k in [
                    "offensive_quality_sum",
                    "defensive_quality_sum",
                    "quality_differential",
                    "elite_shooters_on_ice",
                    "weak_defenders_on_ice",
                    "height_advantage",
                    "offensive_xg_impact",
                    "defensive_xg_impact",
                    "xg_differential",
                ]
            }
        quality_features.append(quality)

    quality_df = pd.DataFrame(quality_features)
    shots_df = pd.concat([shots_df, quality_df], axis=1)

    print("Adding advanced features...")
    # Royal road passes
    shots_df["royal_road_pass"] = calculate_royal_road_pass(shots_df)

    # Screen quality
    screen_quality_df = calculate_screen_quality(shots_df, player_tiers)
    shots_df["screen_quality"] = screen_quality_df["screen_quality"]

    # Rush quality (not just binary)
    shots_df["rush_quality"] = shots_df["speed_from_prev"] / 30  # Normalize by max speed
    shots_df["rush_quality"] = shots_df["rush_quality"].fillna(0).clip(0, 1)

    # Pre-shot deception
    shots_df["quick_release"] = (shots_df["time_since_prev_event"] < 0.5).astype(int)

    # Expanded shot value
    shots_df["shot_value"] = (
        shots_df["is_goal"] + shots_df["created_rebound_chance"] * 0.3 - shots_df["fast_break_risk"] * 0.2
    )

    # Add player-specific features from MoneyPuck
    print("Merging player-specific metrics...")

    # Shooter metrics
    shooter_features = skaters[
        ["playerId", "I_F_shotAttempts", "I_F_goals", "I_F_rebounds", "I_F_xGoals", "I_F_highDangerShots"]
    ]
    shooter_features.columns = ["shooter_id"] + [f"shooter_{col}" for col in shooter_features.columns[1:]]
    shots_df = shots_df.merge(shooter_features, on="shooter_id", how="left")

    # Goalie metrics
    goalie_features = goalies[["playerId", "xGoals", "goals", "lowDangerSV%", "mediumDangerSV%", "highDangerSV%"]]
    goalie_features.columns = ["goalie_id"] + [f"goalie_{col}" for col in goalie_features.columns[1:]]
    shots_df = shots_df.merge(goalie_features, on="goalie_id", how="left")

    # Team context
    team_features = teams[["team", "xGoalsPercentage", "xGoalsFor", "goalsFor"]]
    team_features["team_finishing_ability"] = team_features["goalsFor"] / team_features["xGoalsFor"]
    shots_df = shots_df.merge(team_features, left_on="shooting_team", right_on="team", how="left")

    print("Creating player embeddings...")
    # Get unique player IDs
    all_player_ids = (
        pd.concat([shots_df["shooter_id"], shots_df["assist1_id"], shots_df["assist2_id"], shots_df["goalie_id"]])
        .dropna()
        .unique()
    )

    embeddings = load_player_embeddings(all_player_ids.astype(int).tolist())

    # Add embeddings as features
    for player_type in ["shooter", "assist1", "assist2", "goalie"]:
        for i in range(8):  # 8-dimensional embeddings
            shots_df[f"{player_type}_embed_{i}"] = shots_df[f"{player_type}_id"].map(
                lambda x: embeddings.get(int(x), np.zeros(8))[i] if pd.notna(x) else 0
            )

    # Create situation-specific flags for hierarchical modeling
    shots_df["situation_5v5"] = (shots_df["strength_state"] == "5v5").astype(int)
    shots_df["situation_pp"] = shots_df["is_powerplay"].astype(int)
    shots_df["situation_pk"] = shots_df["is_shorthanded"].astype(int)
    shots_df["situation_en"] = shots_df["empty_net"].astype(int)

    # Save enhanced dataset
    print(f"Saving enhanced dataset with {len(shots_df.columns)} features...")
    shots_df.to_csv("data/nhl/processed/training_data_complete_xg.csv", index=False)

    # Save feature list
    with open("data/nhl/processed/xg_features_complete.txt", "w") as f:
        for col in sorted(shots_df.columns):
            f.write(f"{col}\n")

    print(f"Complete! Created dataset with {len(shots_df)} shots and {len(shots_df.columns)} features")

    # Print feature summary
    print("\nNew features added:")
    new_features = [
        "led_to_opponent_shot",
        "time_to_opponent_shot",
        "created_rebound_chance",
        "rim_around_danger",
        "fast_break_risk",
        "offensive_quality_sum",
        "defensive_quality_sum",
        "quality_differential",
        "elite_shooters_on_ice",
        "weak_defenders_on_ice",
        "height_advantage",
        "offensive_xg_impact",
        "defensive_xg_impact",
        "xg_differential",
        "royal_road_pass",
        "screen_quality",
        "rush_quality",
        "quick_release",
        "shot_value",
        "team_finishing_ability",
    ]
    for feature in new_features:
        if feature in shots_df.columns:
            print(f"  - {feature}: {shots_df[feature].describe().to_dict()}")


if __name__ == "__main__":
    main()
