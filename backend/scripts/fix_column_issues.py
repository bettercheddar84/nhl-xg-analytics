#!/usr/bin/env python3
"""
Fix column issues in processed data files:
1. Add 'tier' column to player_tiers.csv based on performance metrics
2. Add 'shots_faced_game' alias for 'total_shots_faced_game' in goalie_workload.csv
3. Calculate actual zone_time values for training_data_enhanced.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_player_tiers(file_path):
    """Add overall 'tier' column based on player performance metrics"""
    logger.info("Fixing player_tiers.csv...")
    
    df = pd.read_csv(file_path)
    
    # Calculate overall tier based on position and performance
    def calculate_tier(row):
        if row['position_group'] == 'G':
            # Goalie tier based on save percentage
            if pd.isna(row['save_pct']):
                return 'Unknown'
            elif row['save_pct'] >= 0.920:
                return 'Elite'
            elif row['save_pct'] >= 0.910:
                return 'Top'
            elif row['save_pct'] >= 0.900:
                return 'Average'
            else:
                return 'Below Average'
        else:
            # Skater tier based on points per game
            if row['points_per_game'] >= 1.0:
                return 'Elite'
            elif row['points_per_game'] >= 0.7:
                return 'Top'
            elif row['points_per_game'] >= 0.5:
                return 'Average'
            elif row['points_per_game'] >= 0.3:
                return 'Below Average'
            else:
                return 'Replacement'
    
    df['tier'] = df.apply(calculate_tier, axis=1)
    
    # Save updated file
    df.to_csv(file_path, index=False)
    logger.info(f"Added 'tier' column with distribution: {df['tier'].value_counts().to_dict()}")


def fix_goalie_workload(file_path):
    """Add 'shots_faced_game' as alias for 'total_shots_faced_game'"""
    logger.info("Fixing goalie_workload.csv...")
    
    df = pd.read_csv(file_path)
    
    # Create alias column
    df['shots_faced_game'] = df['total_shots_faced_game']
    
    # Save updated file
    df.to_csv(file_path, index=False)
    logger.info("Added 'shots_faced_game' column as alias for 'total_shots_faced_game'")


def fix_zone_time(file_path):
    """Calculate actual zone time values from offensive_zone_time"""
    logger.info("Fixing training_data_enhanced.csv zone_time...")
    
    # Read file in chunks due to size
    chunk_size = 100000
    chunks = []
    
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        # Calculate zone_time based on offensive_zone_time and game context
        # If offensive_zone_time exists and is not null, use it
        if 'offensive_zone_time' in chunk.columns:
            chunk['zone_time'] = chunk['offensive_zone_time'].fillna(0)
        else:
            # Otherwise calculate based on time since zone entry
            if 'time_since_zone_entry' in chunk.columns:
                chunk['zone_time'] = chunk['time_since_zone_entry'].fillna(0)
            else:
                # Default to 0 if no zone time data available
                chunk['zone_time'] = 0
        
        # Convert to float to ensure numeric type
        chunk['zone_time'] = pd.to_numeric(chunk['zone_time'], errors='coerce').fillna(0)
        
        chunks.append(chunk)
    
    # Combine all chunks
    df = pd.concat(chunks, ignore_index=True)
    
    # Save updated file
    df.to_csv(file_path, index=False)
    
    logger.info(f"Fixed zone_time column. Non-zero values: {(df['zone_time'] > 0).sum()}")
    logger.info(f"Zone time stats: mean={df['zone_time'].mean():.2f}, max={df['zone_time'].max():.2f}")


def main():
    """Fix all column issues"""
    base_dir = Path("data/nhl/processed")
    
    # Fix player tiers
    player_tiers_file = base_dir / "player_tiers.csv"
    if player_tiers_file.exists():
        fix_player_tiers(player_tiers_file)
    else:
        logger.warning(f"File not found: {player_tiers_file}")
    
    # Fix goalie workload
    goalie_workload_file = base_dir / "goalie_workload.csv"
    if goalie_workload_file.exists():
        fix_goalie_workload(goalie_workload_file)
    else:
        logger.warning(f"File not found: {goalie_workload_file}")
    
    # Fix training data zone time
    training_data_file = base_dir / "training_data_enhanced.csv"
    if training_data_file.exists():
        fix_zone_time(training_data_file)
    else:
        logger.warning(f"File not found: {training_data_file}")
    
    logger.info("All column fixes completed!")


if __name__ == "__main__":
    main()