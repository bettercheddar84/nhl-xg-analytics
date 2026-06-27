import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load shots data
df = pd.read_csv("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")

# Get unique players from each role
shooters = set(df["shooter_id"].dropna().astype(int))
goalies = set(df["goalie_id"].dropna().astype(int))
assist1 = set(df["assist1_id"].dropna().astype(int))
assist2 = set(df["assist2_id"].dropna().astype(int))

# Combine all unique players
all_players = shooters.union(goalies).union(assist1).union(assist2)

# Check player files
player_dir = Path("data/nhl/players")
existing_players = {int(f.stem) for f in player_dir.glob("*.json")}

# Find missing players
missing_players = all_players - existing_players

logger.info(f"Unique shooters: {len(shooters)}")
logger.info(f"Unique goalies: {len(goalies)}")
logger.info(f"Unique assist1: {len(assist1)}")
logger.info(f"Unique assist2: {len(assist2)}")
logger.info(f"Total unique players in shots data: {len(all_players)}")
logger.info(f"Player files available: {len(existing_players)}")
logger.info(f"Missing player files: {len(missing_players)}")

# Show some missing players
if missing_players:
    logger.info("\nExample missing player IDs:")
    for pid in list(missing_players)[:10]:
        # Find what role this player had
        roles = []
        if pid in shooters:
            roles.append("shooter")
        if pid in goalies:
            roles.append("goalie")
        if pid in assist1:
            roles.append("assist1")
        if pid in assist2:
            roles.append("assist2")
        logger.info(f'  {pid}: {", ".join(roles)}')
