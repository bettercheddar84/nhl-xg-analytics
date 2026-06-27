import json
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_age(birth_date_str, reference_date="2024-10-01"):
    if not birth_date_str:
        return None
    birth = datetime.strptime(birth_date_str, "%Y-%m-%d")
    ref = datetime.strptime(reference_date, "%Y-%m-%d")
    return (ref - birth).days / 365.25


def determine_height_tier(height, position_group):
    if position_group == "F":
        if height < 71:
            return "Small"
        elif height <= 73:
            return "Medium"
        else:
            return "Large"
    elif position_group == "D":
        if height < 72:
            return "Small"
        elif height <= 74:
            return "Medium"
        else:
            return "Large"
    else:  # Goalies
        if height < 74:
            return "Small"
        elif height <= 76:
            return "Medium"
        else:
            return "Large"


def determine_plus_minus_tier(plus_minus):
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


def process_player_files(player_files, season_stats):
    player_data = []

    for i, player_file in enumerate(player_files):
        if i % 100 == 0:
            logger.info(f"Processing players: {i}/{len(player_files)}")

        with open(player_file) as f:
            player = json.load(f)

        player_id = player.get("playerId")

        # Physical attributes
        height = player.get("heightInInches", 72)
        weight = player.get("weightInPounds", 190)
        position = player.get("position", "F")
        shoots = player.get("shootsCatches", "R")

        # Add new features
        age = calculate_age(player.get("birthDate"))
        draft_round = player.get("draftRound", 99)

        # Career stats
        career = player.get("careerTotals", {}).get("regularSeason", {})
        career_games = career.get("gamesPlayed", 0)
        career_goals = career.get("goals", 0)
        career_shooting_pct = career.get("shootingPctg", 0)

        # Determine position group
        position_group = "G" if position == "G" else ("D" if position == "D" else "F")

        # Get height tier
        height_tier = determine_height_tier(height, position_group)

        # Season stats
        stats = season_stats.get(str(player_id), {})
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
                # New features
                "age": age,
                "draft_round": draft_round,
                "is_first_round": int(draft_round == 1),
                "career_games": career_games,
                "career_goals": career_goals,
                "career_shooting_pct": career_shooting_pct,
                "is_veteran": int(career_games >= 300),
                "is_rookie": int(career_games < 50),
                "birth_country": player.get("birthCountry", "CAN"),
                "team_id": player.get("currentTeamId"),
            }
        )

    return pd.DataFrame(player_data)


def mark_elite_players(df):
    df["elite_scorer"] = False
    df["elite_goalie"] = False

    forwards_df = df[df["position_group"] == "F"].sort_values("points", ascending=False)
    defense_df = df[df["position_group"] == "D"].sort_values("points", ascending=False)

    if len(forwards_df) > 0:
        df.loc[forwards_df.head(20).index, "elite_scorer"] = True
    if len(defense_df) > 0:
        df.loc[defense_df.head(5).index, "elite_scorer"] = True

    goalies_df = df[(df["position_group"] == "G") & (df["games_played"] >= 10)]
    if len(goalies_df) > 0:
        goalies_df = goalies_df.sort_values("save_pct", ascending=False)
        df.loc[goalies_df.head(5).index, "elite_goalie"] = True

    return df


def main():
    season_stats_file = Path("data/nhl/season_stats/all_players_202425.json")
    players_dir = Path("data/nhl/players")
    output_file = Path("data/nhl/processed/player_tiers_enhanced.csv")

    logger.info("Loading season statistics...")
    with open(season_stats_file) as f:
        season_stats = json.load(f)

    player_files = list(players_dir.glob("*.json"))
    logger.info(f"Found {len(player_files)} player files")

    df = process_player_files(player_files, season_stats)
    df = mark_elite_players(df)

    df["size_advantage"] = df["height_tier"].map({"Large": 1, "Medium": 0, "Small": -1})

    df.to_csv(output_file, index=False)
    logger.info(f"Saved enhanced player tiers to {output_file}")
    logger.info(f"Total players: {len(df)}")
    logger.info("New features added: age, draft info, career stats, team_id")


if __name__ == "__main__":
    main()
