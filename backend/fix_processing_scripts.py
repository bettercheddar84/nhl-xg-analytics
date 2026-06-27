#!/usr/bin/env python3
"""
Fix known issues in data processing scripts before running them
"""

import re
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def fix_calculate_on_ice_quality():
    """Fix the offensive_rating column issue"""
    logger.info("Fixing calculate_on_ice_quality.py...")
    
    file_path = Path("scripts/calculate_on_ice_quality.py")
    content = file_path.read_text()
    
    # Replace offensive_rating with actual column that exists
    fixes = [
        # Fix line 73: offensive_rating -> offensive_impact
        ('player_tier.iloc[0]["offensive_rating"]', 
         'player_tier.iloc[0].get("offensive_impact", 0.5)'),
        
        # Fix line 88: defensive_rating -> defensive_impact  
        ('player_tier.iloc[0]["defensive_rating"]',
         'player_tier.iloc[0].get("defensive_impact", 0.5)'),
    ]
    
    for old, new in fixes:
        if old in content:
            content = content.replace(old, new)
            logger.info(f"  ✓ Fixed: {old} -> {new}")
    
    file_path.write_text(content)

def fix_calculate_shot_value_decay():
    """Fix the is_rebound column issue"""
    logger.info("\nFixing calculate_shot_value_decay.py...")
    
    file_path = Path("scripts/calculate_shot_value_decay.py")
    content = file_path.read_text()
    
    # Add is_rebound check
    if '"is_rebound"' in content and 'shots_df["is_rebound"]' not in content:
        # Add calculation before the aggregation
        insert_after = "shots_df = pd.read_csv"
        insert_lines = """
    
    # Calculate is_rebound if not present
    if 'is_rebound' not in shots_df.columns:
        shots_df['is_rebound'] = 0
        if 'time_since_prev_shot' in shots_df.columns:
            shots_df.loc[shots_df['time_since_prev_shot'] <= 3, 'is_rebound'] = 1
"""
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if insert_after in line:
                lines.insert(i + 1, insert_lines)
                break
        
        content = '\n'.join(lines)
        logger.info("  ✓ Added is_rebound calculation")
    
    file_path.write_text(content)

def fix_calculate_hockey_babip():
    """Fix the total_shots_first column issue"""
    logger.info("\nFixing calculate_hockey_babip.py...")
    
    file_path = Path("scripts/calculate_hockey_babip.py")
    content = file_path.read_text()
    
    # Fix line 207 - total_shots_first doesn't exist
    if 'comparison["total_shots_first"]' in content:
        content = content.replace(
            'comparison["total_shots_first"] >= 25',
            'comparison["total_shots"] >= 50'  # Just use total shots
        )
        logger.info("  ✓ Fixed total_shots_first reference")
    
    file_path.write_text(content)

def fix_calculate_missing_stats():
    """Fix the assist1_id column issue"""
    logger.info("\nFixing calculate_missing_stats.py...")
    
    file_path = Path("scripts/calculate_missing_stats.py")
    content = file_path.read_text()
    
    # Check if assist columns exist before using them
    if 'calculator.shots_df["assist1_id"]' in content:
        # Add check before concatenating
        old_code = '[calculator.shots_df["shooter_id"], calculator.shots_df["assist1_id"], calculator.shots_df["assist2_id"]]'
        new_code = '''[calculator.shots_df["shooter_id"]] + 
        ([calculator.shots_df["assist1_id"]] if "assist1_id" in calculator.shots_df.columns else []) +
        ([calculator.shots_df["assist2_id"]] if "assist2_id" in calculator.shots_df.columns else [])'''
        
        content = content.replace(old_code, new_code)
        logger.info("  ✓ Added assist column checks")
    
    file_path.write_text(content)

def fix_build_player_embeddings():
    """Fix the offensive_on_ice type issue"""
    logger.info("\nFixing build_player_embeddings.py...")
    
    file_path = Path("scripts/build_player_embeddings.py")
    content = file_path.read_text()
    
    # Fix the extract_player_ids_from_string function to handle different types
    old_func = '''def extract_player_ids_from_string(on_ice_str):
    """Extract player IDs from string representation of list"""
    if pd.isna(on_ice_str):
        return []
    
    player_ids = []
    # Handle string that looks like: "['Player Name (ID)', 'Player Name (ID)']"
    players = on_ice_str.strip("[]").split(",")
    for player in players:
        if "(" in player and ")" in player:'''
    
    new_func = '''def extract_player_ids_from_string(on_ice_str):
    """Extract player IDs from string representation of list"""
    if pd.isna(on_ice_str):
        return []
    
    # Handle if it's already an integer
    if isinstance(on_ice_str, (int, float)):
        return [int(on_ice_str)]
    
    # Convert to string if needed
    on_ice_str = str(on_ice_str)
    
    player_ids = []
    # Handle string that looks like: "['Player Name (ID)', 'Player Name (ID)']"
    players = on_ice_str.strip("[]").split(",")
    for player in players:
        player = str(player).strip().strip("'\"")
        if "(" in player and ")" in player:'''
    
    if old_func in content:
        content = content.replace(old_func, new_func)
        logger.info("  ✓ Fixed player ID extraction to handle multiple types")
    
    file_path.write_text(content)

def main():
    logger.info("=" * 60)
    logger.info("FIXING KNOWN ISSUES IN PROCESSING SCRIPTS")
    logger.info("=" * 60)
    
    try:
        fix_calculate_on_ice_quality()
    except Exception as e:
        logger.error(f"✗ Error fixing calculate_on_ice_quality: {e}")
    
    try:
        fix_calculate_shot_value_decay()
    except Exception as e:
        logger.error(f"✗ Error fixing calculate_shot_value_decay: {e}")
    
    try:
        fix_calculate_hockey_babip()
    except Exception as e:
        logger.error(f"✗ Error fixing calculate_hockey_babip: {e}")
    
    try:
        fix_calculate_missing_stats()
    except Exception as e:
        logger.error(f"✗ Error fixing calculate_missing_stats: {e}")
    
    try:
        fix_build_player_embeddings()
    except Exception as e:
        logger.error(f"✗ Error fixing build_player_embeddings: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("SCRIPT FIXES COMPLETE")
    logger.info("You can now run: python prepare_essential_data.py")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()