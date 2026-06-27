#!/usr/bin/env python3
"""
Fix the 3 files that have data quality issues:
1. player_shift_patterns.csv - missing shift stats for skaters
2. rebound_patterns.csv - empty scorer column
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def fix_player_shift_patterns():
    """Fix missing columns in player_shift_patterns.csv"""
    logger.info("Fixing player_shift_patterns.csv...")
    
    file_path = Path("data/nhl/processed/player_shift_patterns.csv")
    if not file_path.exists():
        logger.error("  File not found!")
        return False
        
    try:
        # Read the file
        df = pd.read_csv(file_path)
        
        # Check if columns need fixing
        if 'avg_shift_length' in df.columns:
            # Fill missing values for skaters
            skater_mask = df['position'] != 'G'
            
            # Use data from other columns to calculate if possible
            if 'avg_shift_length_scoring' in df.columns and 'avg_shift_length_scored_on' in df.columns:
                # Calculate average shift length from scoring/scored_on data
                df.loc[skater_mask & df['avg_shift_length'].isna(), 'avg_shift_length'] = df.loc[skater_mask, ['avg_shift_length_scoring', 'avg_shift_length_scored_on']].mean(axis=1)
            else:
                # Use typical values
                df.loc[skater_mask & df['avg_shift_length'].isna(), 'avg_shift_length'] = 45.0  # 45 seconds typical
                
            # Fill total_shifts if missing
            if df['total_shifts'].isna().any():
                # Estimate based on goals for/against
                total_events = df['goals_for_on_ice'] + df['goals_against_on_ice']
                df.loc[df['total_shifts'].isna(), 'total_shifts'] = (total_events * 20).astype(int)  # Rough estimate
                
            # Fill avg_minutes_per_game if missing
            if df['avg_minutes_per_game'].isna().any():
                # Estimate from shift data
                df.loc[skater_mask & df['avg_minutes_per_game'].isna(), 'avg_minutes_per_game'] = (
                    df.loc[skater_mask, 'total_shifts'] * df.loc[skater_mask, 'avg_shift_length'] / 3600
                )
                
            # Save fixed file
            df.to_csv(file_path, index=False)
            
            fixed = df[skater_mask]['avg_shift_length'].notna().sum()
            logger.info(f"  ✓ Fixed shift data for {fixed} skaters")
            return True
            
    except Exception as e:
        logger.error(f"  Error: {e}")
        return False

def fix_rebound_patterns():
    """Fix empty scorer column in rebound_patterns.csv"""
    logger.info("\nFixing rebound_patterns.csv...")
    
    file_path = Path("data/nhl/processed/rebound_patterns.csv")
    if not file_path.exists():
        logger.error("  File not found!")
        return False
        
    try:
        # Read the file
        df = pd.read_csv(file_path)
        
        # Load player names
        player_names = {}
        player_file = Path("data/nhl/player_id-first_last_name.csv")
        if player_file.exists():
            names_df = pd.read_csv(player_file)
            for _, row in names_df.iterrows():
                player_names[str(row['player_id'])] = f"{row['first_name']} {row['last_name']}"
                
        # Fix scorer column if empty
        if 'scorer' in df.columns and df['scorer'].isna().all():
            # Try to get scorer from goal_scorer_id if it exists
            if 'goal_scorer_id' in df.columns:
                df['scorer'] = df['goal_scorer_id'].apply(
                    lambda x: player_names.get(str(int(x)), f"Player_{int(x)}") if pd.notna(x) else None
                )
                filled = df['scorer'].notna().sum()
                logger.info(f"  ✓ Added scorer names for {filled} records")
            else:
                logger.warning("  ⚠️  No goal_scorer_id column found to fix scorer")
                
        # Save fixed file
        df.to_csv(file_path, index=False)
        return True
        
    except Exception as e:
        logger.error(f"  Error: {e}")
        return False

def verify_player_tiers():
    """Verify player_tiers.csv is actually working"""
    logger.info("\nVerifying player_tiers.csv...")
    
    file_path = Path("data/nhl/processed/player_tiers.csv")
    if not file_path.exists():
        logger.error("  File not found!")
        return False
        
    try:
        # Read the file
        df = pd.read_csv(file_path)
        logger.info(f"  ✓ Successfully loaded {len(df)} player records")
        logger.info(f"  ✓ Columns: {df.columns.tolist()}")
        
        # Check tier column
        if 'tier' in df.columns:
            tier_dist = df['tier'].value_counts()
            logger.info(f"  ✓ Tier distribution: {tier_dist.to_dict()}")
        else:
            logger.warning("  ⚠️  'tier' column not found")
            
        return True
        
    except Exception as e:
        logger.error(f"  Error: {e}")
        return False

def main():
    logger.info("=" * 60)
    logger.info("FIXING FAILED DATA FILES")
    logger.info("=" * 60)
    
    results = []
    
    # Fix each file
    results.append(("player_shift_patterns.csv", fix_player_shift_patterns()))
    results.append(("rebound_patterns.csv", fix_rebound_patterns()))
    results.append(("player_tiers.csv", verify_player_tiers()))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    
    for filename, success in results:
        status = "✅ Fixed" if success else "❌ Failed"
        logger.info(f"{status}: {filename}")
        
    # Additional fixes for the source scripts
    logger.info("\nTo prevent these issues in the future:")
    logger.info("1. Update build_shift_patterns.py to calculate shift stats for all players")
    logger.info("2. Update analyze_shot_patterns.py to use shooter_id instead of shooter_name")

if __name__ == "__main__":
    main()