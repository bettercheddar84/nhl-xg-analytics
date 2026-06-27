import json
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, Any, List
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_season_stats(filepath: Path) -> Dict[str, Any]:
    """Load season statistics from JSON file."""
    try:
        with open(filepath) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Season stats file not found: {filepath}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing season stats JSON: {e}")
        return {}


def determine_height_tier(height: int, position_group: str) -> str:
    """Determine height tier based on position and height in inches."""
    if position_group == "F":
        if height < 71:  # <5'11"
            return "Small"
        elif height <= 73:  # 5'11"-6'1"
            return "Medium"
        else:
            return "Large"
    elif position_group == "D":
        if height < 72:  # <6'0"
            return "Small"
        elif height <= 74:  # 6'0"-6'2"
            return "Medium"
        else:
            return "Large"
    else:  # Goalies
        if height < 74:  # <6'2"
            return "Small"
        elif height <= 76:  # 6'2"-6'4"
            return "Medium"
        else:
            return "Large"


def determine_plus_minus_tier(plus_minus: int) -> str:
    """Categorize plus/minus into performance tiers."""
    if plus_minus >= 15:
        return "Elite"
    elif plus_minus >= 5:
        return "Good"
    elif plus_minus >= -5:
        return "Average"
    elif plus_minus >= -15:
        return "Below Average"
    else:
        return "Poor"


def process_player_files(player_files: List[Path], season_stats: Dict[str, Any]) -> pd.DataFrame:
    """Process all player files and extract tier information."""
    player_data = []
    total_files = len(player_files)

    for i, player_file in enumerate(player_files):
        if i % 100 == 0:
            logger.info(f"Processing players: {i}/{total_files} ({i / total_files * 100:.1f}%)")

        try:
            with open(player_file, encoding="utf-8") as f:
                player = json.load(f)
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                with open(player_file, encoding="latin-1") as f:
                    player = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Error reading {player_file}: {e}")
                continue
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Error reading {player_file}: {e}")
            continue

        player_id = player.get("playerId")
        if not player_id:
            logger.warning(f"No playerId found in {player_file}")
            continue

        # Get physical attributes with defaults
        height = player.get("heightInInches", 72)  # Default 6'0"
        weight = player.get("weightInPounds", 190)
        position = player.get("position", "F")
        shoots = player.get("shootsCatches", "R")

        # Get season stats
        stats = season_stats.get(str(player_id), {})

        # Determine position group
        if position == "G":
            position_group = "G"
        elif position in ["D"]:
            position_group = "D"
        else:  # C, L, R, F
            position_group = "F"

        # Get height tier
        height_tier = determine_height_tier(height, position_group)

        # Performance metrics with defaults
        games_played = stats.get("gamesPlayed", 0)
        goals = stats.get("goals", 0)
        assists = stats.get("assists", 0)
        points = goals + assists
        plus_minus = stats.get("plusMinus", 0)
        shooting_pct = stats.get("shootingPct", 0)
        save_pct = stats.get("savePct", 0)

        # Points per game
        ppg = round(points / games_played, 3) if games_played > 0 else 0

        # Plus/minus tier
        pm_tier = determine_plus_minus_tier(plus_minus)

        player_data.append(
            {
                "player_id": player_id,
                "position": position,
                "position_group": position_group,
                "height": height,
                "weight": weight,
                "height_tier": height_tier,
                "shoots": shoots,
                "games_played": games_played,
                "goals": goals,
                "assists": assists,
                "points": points,
                "points_per_game": ppg,
                "plus_minus": plus_minus,
                "plus_minus_tier": pm_tier,
                "shooting_pct": shooting_pct,
                "save_pct": save_pct,
            }
        )

    return pd.DataFrame(player_data)


def mark_elite_players(df: pd.DataFrame) -> pd.DataFrame:
    """Mark elite players based on performance metrics."""
    # Initialize elite columns
    df["elite_scorer"] = False
    df["elite_goalie"] = False

    # Elite forwards and defense (top performers by points)
    forwards_df = df[df["position_group"] == "F"].sort_values("points", ascending=False)
    defense_df = df[df["position_group"] == "D"].sort_values("points", ascending=False)

    # Mark top 20 forwards and top 5 defensemen as elite scorers
    if len(forwards_df) > 0:
        df.loc[forwards_df.head(20).index, "elite_scorer"] = True
    if len(defense_df) > 0:
        df.loc[defense_df.head(5).index, "elite_scorer"] = True

    # Elite goalies (top 5 by save % with minimum games)
    goalies_df = df[(df["position_group"] == "G") & (df["games_played"] >= 10)]
    if len(goalies_df) > 0:
        goalies_df = goalies_df.sort_values("save_pct", ascending=False)
        df.loc[goalies_df.head(5).index, "elite_goalie"] = True

    return df


def main():
    """Main execution function."""
    try:
        # Paths
        season_stats_file = Path("data/nhl/season_stats/all_players_202425.json")
        players_dir = Path("data/nhl/players")
        output_dir = Path("data/nhl/processed")
        output_file = output_dir / "player_tiers.csv"

        # Check if required files exist
        if not season_stats_file.exists():
            logger.error(f"Season stats file not found: {season_stats_file}")
            sys.exit(1)

        if not players_dir.exists():
            logger.error(f"Players directory not found: {players_dir}")
            sys.exit(1)

        logger.info("Loading season statistics...")
        season_stats = load_season_stats(season_stats_file)

        # Get all player files
        player_files = list(players_dir.glob("*.json"))
        logger.info(f"Found {len(player_files)} player files to process")

        if not player_files:
            logger.error("No player files found!")
            sys.exit(1)

        # Process all players
        logger.info("Building player tier classifications...")
        df = process_player_files(player_files, season_stats)

        if len(df) == 0:
            logger.error("No valid player data extracted!")
            sys.exit(1)

        # Mark elite players
        logger.info("Identifying elite players...")
        df = mark_elite_players(df)

        # Add additional computed features
        df["size_advantage"] = df.apply(
            lambda x: 1 if x["height_tier"] == "Large" else (0 if x["height_tier"] == "Medium" else -1), axis=1
        )

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save results
        df.to_csv(output_file, index=False)
        logger.info(f"Saved player tiers to {output_file}")

        # Print summary statistics
        logger.info("\n=== Player Tier Summary ===")
        logger.info(f"Total players processed: {len(df)}")
        logger.info(f"Elite scorers: {df['elite_scorer'].sum()}")
        logger.info(f"Elite goalies: {df['elite_goalie'].sum()}")

        logger.info("\nPosition distribution:")
        logger.info(df["position_group"].value_counts().to_string())

        logger.info("\nHeight distribution by position:")
        height_dist = df.groupby(["position_group", "height_tier"]).size()
        logger.info(height_dist.to_string())

        logger.info("\nPlus/minus distribution:")
        pm_dist = df["plus_minus_tier"].value_counts()
        logger.info(pm_dist.to_string())

        # Data quality checks
        missing_height = len(df[df["height"] == 72])  # Default value
        if missing_height > 100:
            logger.warning(f"Large number of players ({missing_height}) with default height")

        return df

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    main()
