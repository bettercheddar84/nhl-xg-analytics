import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def load_player_roster(roster_path=None):
    """Load player roster with ID to name mapping."""
    # Try multiple possible paths
    possible_paths = [
        roster_path,
        "data/nhl/player_id-first_last_name.csv",  # Your actual file
        "data/nhl/players_roster.csv",
        "data/nhl/raw/players_roster.csv",
        "data/players_roster.csv",
        "players_roster.csv",
        "../data/nhl/players_roster.csv",
    ]

    roster_df = None
    used_path = None

    for path in possible_paths:
        if path and Path(path).exists():
            try:
                roster_df = pd.read_csv(path)
                used_path = path
                break
            except Exception as e:
                logger.warning(f"Failed to read {path}: {e}")

    if roster_df is None:
        logger.error("Could not find player roster CSV in any of the expected locations:")
        for path in [p for p in possible_paths if p]:
            logger.error(f"  - {path}")
        logger.info("\nYou can:")
        logger.info("1. Place the file in one of the locations above")
        logger.info("2. Pass the path as an argument: load_player_roster('your/path/to/roster.csv')")
        logger.info("3. Use the script without player names (comment out the roster loading)")
        raise FileNotFoundError("Player roster CSV not found")

    logger.info(f"Loaded player roster from: {used_path}")

    # Create mapping dictionary
    player_map = {}
    for _, row in roster_df.iterrows():
        player_id = str(row["player_id"])
        full_name = f"{row['first_name']} {row['last_name']}"
        player_map[player_id] = full_name

    logger.info(f"Loaded {len(player_map)} players from roster")
    return player_map


def calculate_miss_danger(shot):
    """Calculate how dangerous a missed shot is based on location."""
    distance = shot.get("shot_distance", 0)
    angle = abs(shot.get("shot_angle", 0))

    if distance < 25 and angle < 30:
        return "high_danger_miss"
    elif angle > 45 or distance > 60:
        return "bad_angle_miss"
    else:
        return "medium_danger_miss"


def determine_zone(x_coord, y_coord):
    """Determine which zone the shot was taken from."""
    if pd.isna(x_coord) or pd.isna(y_coord):
        return "unknown"

    x = abs(x_coord)

    if x >= 64:
        if abs(y_coord) <= 15:
            return "slot"
        else:
            return "goal_line"
    elif x >= 25:
        if abs(y_coord) <= 20:
            return "high_slot"
        else:
            return "perimeter"
    else:
        return "point"


def calculate_distance(x1, y1, x2, y2):
    """Calculate distance between two points on the ice."""
    if any(pd.isna(v) for v in [x1, y1, x2, y2]):
        return 0
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def identify_rush_events(df, miss_event, time_window=60):
    """
    Identify all pressure sequences following a missed shot.
    Captures immediate rushes AND sustained pressure over 60 seconds.
    """
    game_id = miss_event["game_id"]
    miss_time = miss_event["game_seconds"]
    miss_team = miss_event["shooting_team"]

    # Get opponent team
    opp_team = miss_event["home_team"] if miss_team == miss_event["away_team"] else miss_event["away_team"]

    # Find all opponent events in the time window
    pressure_events = df[
        (df["game_id"] == game_id)
        & (df["shooting_team"] == opp_team)
        & (df["game_seconds"] > miss_time)
        & (df["game_seconds"] <= miss_time + time_window)
        & (df["event_type"].isin(["shot-on-goal", "missed-shot", "blocked-shot", "goal"]))
    ].copy()

    # Calculate pressure sequences
    pressure_sequences = []

    if len(pressure_events) > 0:
        # Group shots into pressure sequences (gaps > 15 seconds = new sequence)
        pressure_events["time_diff"] = pressure_events["game_seconds"].diff()
        pressure_events["new_sequence"] = (pressure_events["time_diff"] > 15) | (pressure_events["time_diff"].isna())
        pressure_events["sequence_id"] = pressure_events["new_sequence"].cumsum()

        for seq_id in pressure_events["sequence_id"].unique():
            sequence_shots = pressure_events[pressure_events["sequence_id"] == seq_id]

            # Classify pressure type
            sequence_start = sequence_shots.iloc[0]["game_seconds"] - miss_time
            if sequence_start <= 10:
                pressure_type = "immediate_rush"
            elif sequence_start <= 20:
                pressure_type = "quick_transition"
            elif sequence_start <= 35:
                pressure_type = "delayed_pressure"
            else:
                pressure_type = "sustained_pressure"

            # Get sequence outcome
            goals = sequence_shots[sequence_shots["event_type"] == "goal"]
            sequence_successful = len(goals) > 0

            # Calculate shot frequency (shots per 10 seconds)
            sequence_duration = sequence_shots.iloc[-1]["game_seconds"] - sequence_shots.iloc[0]["game_seconds"]
            shot_frequency = len(sequence_shots) / max(sequence_duration / 10, 1)

            # Get goal scorer ID if successful
            goal_scorer_id = None
            if sequence_successful and pd.notna(goals.iloc[0]["shooter_id"]):
                goal_scorer_id = str(int(goals.iloc[0]["shooter_id"]))

            pressure_sequence = {
                "sequence_start_time": sequence_shots.iloc[0]["game_seconds"],
                "sequence_end_time": sequence_shots.iloc[-1]["game_seconds"],
                "time_from_miss": sequence_start,
                "sequence_duration": sequence_duration,
                "pressure_type": pressure_type,
                "shots_in_sequence": len(sequence_shots),
                "shot_frequency": round(shot_frequency, 2),
                "sequence_successful": sequence_successful,
                "goal_time": goals.iloc[0]["game_seconds"] if sequence_successful else None,
                "goal_scorer_id": goal_scorer_id,
                "blocked_shots": len(sequence_shots[sequence_shots["event_type"] == "blocked-shot"]),
                "shots_on_goal": len(sequence_shots[sequence_shots["event_type"] == "shot-on-goal"]),
                "missed_shots": len(sequence_shots[sequence_shots["event_type"] == "missed-shot"]),
                "sequence_shots": sequence_shots[
                    ["shooter_id", "event_type", "shot_distance", "x_coord", "y_coord", "game_seconds"]
                ].to_dict("records"),
            }

            pressure_sequences.append(pressure_sequence)

    return pressure_sequences


def analyze_all_fast_breaks(df, player_map):
    """
    Analyze ALL pressure sequences following turnovers - immediate rushes and sustained pressure.
    """
    logger.info("\n=== Comprehensive Turnover Pressure Analysis (60 second window) ===")

    # Get all missed shots
    missed_shots = df[df["event_type"] == "missed-shot"].copy()
    logger.info(f"Analyzing {len(missed_shots):,} missed shots")

    all_pressure_sequences = []
    pressure_summary = {
        "total_misses": 0,
        "led_to_pressure": 0,
        "immediate_rush_goals": 0,
        "quick_transition_goals": 0,
        "delayed_pressure_goals": 0,
        "sustained_pressure_goals": 0,
        "total_goals": 0,
        "no_pressure": 0,
        "multi_sequence_pressure": 0,
    }

    # Process each missed shot
    for i, (idx, miss) in enumerate(missed_shots.iterrows()):
        if i % 5000 == 0:
            logger.info(f"Processing miss {i}/{len(missed_shots)}")

        # Skip if missing required data
        if pd.isna(miss["shooter_id"]) or pd.isna(miss["game_id"]):
            continue

        pressure_summary["total_misses"] += 1

        # Identify pressure sequences following this miss
        pressure_sequences = identify_rush_events(df, miss, time_window=60)

        if len(pressure_sequences) == 0:
            pressure_summary["no_pressure"] += 1
            # Still record the miss with no pressure
            miss_player_id = str(int(miss["shooter_id"]))
            miss_player_name = player_map.get(miss_player_id, f"Unknown_{miss_player_id}")

            pressure_record = {
                # Miss details
                "miss_player_id": miss_player_id,
                "miss_player_name": miss_player_name,
                "miss_team": miss["shooting_team"],
                "miss_distance": miss["shot_distance"],
                "miss_x": miss["x_coord"],
                "miss_y": miss["y_coord"],
                "miss_danger_level": calculate_miss_danger(miss),
                "miss_zone": determine_zone(miss["x_coord"], miss["y_coord"]),
                "miss_game_seconds": miss["game_seconds"],
                # Pressure details
                "led_to_pressure": False,
                "pressure_type": "none",
                "sequence_successful": False,
                "total_sequences": 0,
                "total_shots_against": 0,
                "time_to_first_shot": None,
                "goal_scorer_id": None,
                "goal_scorer_name": None,
                "time_to_goal": None,
                # Game context
                "game_id": miss["game_id"],
                "period": miss.get("period"),
                "home_team": miss["home_team"],
                "away_team": miss["away_team"],
            }
            all_pressure_sequences.append(pressure_record)
        else:
            pressure_summary["led_to_pressure"] += 1
            if len(pressure_sequences) > 1:
                pressure_summary["multi_sequence_pressure"] += 1

            # Aggregate all sequences for this miss
            total_shots = sum(seq["shots_in_sequence"] for seq in pressure_sequences)
            successful_sequences = [seq for seq in pressure_sequences if seq["sequence_successful"]]

            # Track goals by pressure type
            for seq in successful_sequences:
                pressure_summary["total_goals"] += 1
                pressure_summary[f"{seq['pressure_type']}_goals"] += 1

            # Get the most impactful sequence (goal or most shots)
            if successful_sequences:
                main_sequence = successful_sequences[0]  # First goal
            else:
                main_sequence = max(pressure_sequences, key=lambda x: x["shots_in_sequence"])

            miss_player_id = str(int(miss["shooter_id"]))
            miss_player_name = player_map.get(miss_player_id, f"Unknown_{miss_player_id}")

            # Get goal scorer info if successful
            goal_scorer_name = None
            if main_sequence["goal_scorer_id"]:
                goal_scorer_name = player_map.get(
                    main_sequence["goal_scorer_id"], f"Unknown_{main_sequence['goal_scorer_id']}"
                )

            # Calculate distances
            first_shot = main_sequence["sequence_shots"][0] if main_sequence["sequence_shots"] else {}
            rush_distance = calculate_distance(
                miss["x_coord"],
                miss["y_coord"],
                first_shot.get("x_coord", miss["x_coord"]),
                first_shot.get("y_coord", miss["y_coord"]),
            )

            pressure_record = {
                # Miss details
                "miss_player_id": miss_player_id,
                "miss_player_name": miss_player_name,
                "miss_team": miss["shooting_team"],
                "miss_distance": miss["shot_distance"],
                "miss_x": miss["x_coord"],
                "miss_y": miss["y_coord"],
                "miss_danger_level": calculate_miss_danger(miss),
                "miss_zone": determine_zone(miss["x_coord"], miss["y_coord"]),
                "miss_game_seconds": miss["game_seconds"],
                # Pressure details
                "led_to_pressure": True,
                "pressure_type": main_sequence["pressure_type"],
                "sequence_successful": main_sequence["sequence_successful"],
                "total_sequences": len(pressure_sequences),
                "total_shots_against": total_shots,
                "time_to_first_shot": pressure_sequences[0]["time_from_miss"],
                "goal_scorer_id": main_sequence["goal_scorer_id"],
                "goal_scorer_name": goal_scorer_name,
                "time_to_goal": (
                    main_sequence["goal_time"] - miss["game_seconds"] if main_sequence["goal_time"] else None
                ),
                # Additional metrics
                "rush_distance": rush_distance,
                "shot_frequency": main_sequence["shot_frequency"],
                "blocked_shots": main_sequence["blocked_shots"],
                "shots_on_goal": main_sequence["shots_on_goal"],
                "sequence_duration": main_sequence["sequence_duration"],
                # Game context
                "game_id": miss["game_id"],
                "period": miss.get("period"),
                "home_team": miss["home_team"],
                "away_team": miss["away_team"],
            }
            all_pressure_sequences.append(pressure_record)

    return all_pressure_sequences, pressure_summary


def analyze_player_patterns(pressure_df):
    """Analyze patterns by player with advanced statistics."""
    logger.info("\n=== Player Pattern Analysis ===")

    # Group by miss player
    player_stats = (
        pressure_df.groupby("miss_player_id")
        .agg(
            {
                "led_to_pressure": ["count", "sum"],
                "sequence_successful": "sum",
                "time_to_first_shot": ["mean", "std"],
                "rush_distance": ["mean", "std"],
                "total_shots_against": ["mean", "max"],
            }
        )
        .round(2)
    )

    player_stats.columns = [
        "total_misses",
        "led_to_pressure",
        "led_to_goal",
        "avg_time_to_first_shot",
        "std_time_to_first_shot",
        "avg_rush_distance",
        "std_rush_distance",
        "avg_shots_against",
        "max_shots_against",
    ]

    # Calculate percentile rankings using numpy
    player_stats["pressure_rate"] = (player_stats["led_to_pressure"] / player_stats["total_misses"] * 100).round(1)
    player_stats["goal_rate"] = (player_stats["led_to_goal"] / player_stats["total_misses"] * 100).round(1)

    # Add percentile rankings for risk assessment
    player_stats["pressure_rate_percentile"] = (player_stats["pressure_rate"].rank(pct=True) * 100).round(1)
    player_stats["goal_rate_percentile"] = (player_stats["goal_rate"].rank(pct=True) * 100).round(1)

    # Calculate risk score using numpy weighted average
    weights = np.array([0.3, 0.5, 0.2])  # Weights for pressure rate, goal rate, avg shots
    risk_components = np.column_stack(
        [
            player_stats["pressure_rate_percentile"],
            player_stats["goal_rate_percentile"],
            player_stats["avg_shots_against"].fillna(0).rank(pct=True) * 100,
        ]
    )
    player_stats["risk_score"] = np.average(risk_components, axis=1, weights=weights).round(1)

    # Add player names
    player_map = pressure_df.set_index("miss_player_id")["miss_player_name"].to_dict()
    player_stats["player_name"] = player_stats.index.map(player_map)

    return player_stats


def main(shots_path=None, roster_path=None, output_dir=None):
    """
    Run comprehensive fast break analysis.

    Args:
        shots_path: Path to shots CSV file
        roster_path: Path to player roster CSV file
        output_dir: Directory for output files
    """
    start_time = datetime.now()

    # Set default paths
    if shots_path is None:
        shots_path = "data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv"
    if output_dir is None:
        output_dir = Path("data/nhl/processed")

    # Check if shots file exists
    if not Path(shots_path).exists():
        logger.error(f"Shots file not found: {shots_path}")
        logger.info("Please provide the correct path to your shots CSV file")
        return

    # Load data
    logger.info(f"Loading shot data from: {shots_path}")
    df = pd.read_csv(shots_path)
    df["game_seconds"] = pd.to_numeric(df["game_seconds"])

    # Try to load player roster, but continue without it if not found
    try:
        player_map = load_player_roster(roster_path)
    except FileNotFoundError:
        logger.warning("Continuing without player names - using player IDs only")
        # Create a simple ID-to-ID mapping
        unique_ids = pd.concat([df["shooter_id"].dropna(), df.get("goal_scorer_id", pd.Series()).dropna()]).unique()
        player_map = {str(int(id)): f"Player_{int(id)}" for id in unique_ids if pd.notna(id)}

    # Analyze all fast breaks
    all_pressure_sequences, summary = analyze_all_fast_breaks(df, player_map)

    # Convert to DataFrame
    pressure_df = pd.DataFrame(all_pressure_sequences)

    # Print summary statistics
    print("\n" + "=" * 70)
    print("TURNOVER PRESSURE ANALYSIS SUMMARY (60 Second Window)")
    print("=" * 70)
    print(f"Total missed shots analyzed: {summary['total_misses']:,}")
    print(
        f"Led to pressure sequences: {summary['led_to_pressure']:,} "
        f"({summary['led_to_pressure'] / summary['total_misses'] * 100:.1f}%)"
    )
    print(
        f"No pressure generated: {summary['no_pressure']:,} "
        f"({summary['no_pressure'] / summary['total_misses'] * 100:.1f}%)"
    )
    print(f"Multi-sequence pressure: {summary['multi_sequence_pressure']:,}")

    print("\n" + "-" * 50)
    print("GOALS BY PRESSURE TYPE:")
    print("-" * 50)
    print(f"Immediate rush goals (<10s): {summary['immediate_rush_goals']:,}")
    print(f"Quick transition goals (10-20s): {summary['quick_transition_goals']:,}")
    print(f"Delayed pressure goals (20-35s): {summary['delayed_pressure_goals']:,}")
    print(f"Sustained pressure goals (35-60s): {summary['sustained_pressure_goals']:,}")
    print(f"TOTAL GOALS FROM TURNOVERS: {summary['total_goals']:,}")

    if summary["total_misses"] > 0:
        print(f"\nGoal conversion rate: {summary['total_goals'] / summary['total_misses'] * 100:.2f}%")

    # Analyze player patterns
    player_stats = analyze_player_patterns(pressure_df)

    # Show worst offenders with risk scores
    print("\n" + "=" * 70)
    print("TOP 20 TURNOVER PRESSURE RISK PLAYERS")
    print("=" * 70)
    worst_players = player_stats.nlargest(20, "risk_score")[
        ["player_name", "total_misses", "led_to_pressure", "led_to_goal", "pressure_rate", "goal_rate", "risk_score"]
    ]
    print(worst_players.to_string())

    # Show risk distribution
    print("\n" + "-" * 50)
    print("RISK SCORE DISTRIBUTION:")
    print("-" * 50)
    risk_bins = [0, 25, 50, 75, 90, 100]
    risk_labels = ["Low Risk", "Below Average", "Average", "High Risk", "Critical Risk"]
    player_stats["risk_category"] = pd.cut(
        player_stats["risk_score"], bins=risk_bins, labels=risk_labels, include_lowest=True
    )
    risk_dist = player_stats["risk_category"].value_counts().sort_index()
    for category, count in risk_dist.items():
        print(f"{category}: {count} players")

    # Additional numpy-based analytics
    print("\n" + "-" * 50)
    print("PRESSURE SEQUENCE STATISTICS:")
    print("-" * 50)

    # Calculate correlation between miss location and goal probability
    miss_distances = pressure_df["miss_distance"].to_numpy()
    goal_outcomes = pressure_df["sequence_successful"].astype(int).to_numpy()

    # Remove NaN values for correlation
    valid_mask = ~np.isnan(miss_distances)
    if np.sum(valid_mask) > 0:
        correlation = np.corrcoef(miss_distances[valid_mask], goal_outcomes[valid_mask])[0, 1]
        print(f"Correlation (miss distance vs goal): {correlation:.3f}")

    # Calculate pressure type effectiveness
    pressure_types = ["immediate_rush", "quick_transition", "delayed_pressure", "sustained_pressure"]
    for ptype in pressure_types:
        type_mask = pressure_df["pressure_type"] == ptype
        if type_mask.sum() > 0:
            success_rate = pressure_df.loc[type_mask, "sequence_successful"].mean() * 100
            avg_shots = pressure_df.loc[type_mask, "total_shots_against"].mean()
            print(f"{ptype}: {success_rate:.1f}% success rate, {avg_shots:.1f} avg shots")

    # Save detailed data
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save all pressure data
    output_file = output_dir / "turnover_pressure_analysis_60s.csv"
    pressure_df.to_csv(output_file, index=False)
    logger.info(f"Saved {len(pressure_df):,} pressure sequence records to: {output_file}")

    # Save player summary
    player_file = output_dir / "player_turnover_risk.csv"
    player_stats.to_csv(player_file)
    logger.info(f"Saved stats for {len(player_stats)} players to: {player_file}")

    # Sample output for verification
    print("\n" + "=" * 60)
    print("SAMPLE PRESSURE SEQUENCES")
    print("=" * 60)

    # Show some successful pressure sequences
    successful = pressure_df[pressure_df["sequence_successful"]].head(5)
    for idx, row in successful.iterrows():
        print("\nSuccessful Pressure Sequence:")
        print(f"  Miss by: {row['miss_player_name']} ({row['miss_team']})")
        print(f"  Goal by: {row['goal_scorer_name']} (ID: {row['goal_scorer_id']})")
        print(f"  Pressure type: {row['pressure_type']}")
        print(f"  Time to goal: {row['time_to_goal']:.1f}s")
        print(f"  Total shots in sequence: {row['total_shots_against']}")

    # Show some failed pressure sequences
    print("\nFailed Pressure Sequences:")
    failed = pressure_df[pressure_df["led_to_pressure"] & ~pressure_df["sequence_successful"]].head(5)
    for idx, row in failed.iterrows():
        print(f"\n  Miss by: {row['miss_player_name']} ({row['miss_team']})")
        print(f"  Pressure type: {row['pressure_type']}")
        print(f"  Time to first shot: {row['time_to_first_shot']:.1f}s")
        print(f"  Total shots generated: {row['total_shots_against']}")

    # Execution time
    end_time = datetime.now()
    logger.info(f"\nTotal execution time: {end_time - start_time}")


if __name__ == "__main__":
    import sys

    # Allow command line arguments
    shots_path = sys.argv[1] if len(sys.argv) > 1 else None
    roster_path = sys.argv[2] if len(sys.argv) > 2 else None
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None

    main(shots_path, roster_path, output_dir)
