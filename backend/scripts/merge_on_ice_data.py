#!/usr/bin/env python3
"""
Merge on-ice player data with training shots data
This adds offensive_on_ice and defensive_on_ice columns to all shots
"""

import pandas as pd
import ast
import numpy as np

def main():
    """Merge on-ice player data with shots"""
    
    print("Merging on-ice player data with shots...")
    
    # Load training data
    shots_df = pd.read_csv("data/nhl/processed/training_data_enhanced.csv", low_memory=False)
    print(f"Loaded {len(shots_df)} shots")
    
    # Load on-ice data
    on_ice_df = pd.read_csv("data/nhl/shifts/shots_with_on_ice.csv")
    print(f"Loaded {len(on_ice_df)} shots with on-ice data")
    
    # The on_ice data should have the same order as shots if generated correctly
    # Let's verify by checking a few matches
    print("\nVerifying data alignment...")
    
    # Check if the dataframes have the same length
    if len(shots_df) == len(on_ice_df) - 1:  # -1 for header
        print(f"Data lengths match! Can merge by index.")
        
        # Simply add the columns directly
        shots_df['offensive_on_ice'] = on_ice_df['offensive_on_ice'].values
        shots_df['defensive_on_ice'] = on_ice_df['defensive_on_ice'].values
        merged_df = shots_df
    else:
        print(f"Length mismatch - shots: {len(shots_df)}, on_ice: {len(on_ice_df)}")
        print("Falling back to key-based merge...")
        
        # Create merge key
        shots_df['merge_key'] = (
            shots_df['game_id'].astype(str) + '_' + 
            shots_df['shooter_id'].astype(str) + '_' + 
            shots_df['game_seconds'].astype(str)
        )
        
        on_ice_df['merge_key'] = (
            on_ice_df['game_id'].astype(str) + '_' + 
            on_ice_df['shooter_id'].astype(str) + '_' + 
            on_ice_df['shot_time'].astype(str)
        )
    
        # Merge
        print("\nMerging data...")
        merged_df = shots_df.merge(
            on_ice_df[['merge_key', 'offensive_on_ice', 'defensive_on_ice']], 
            on='merge_key', 
            how='left'
        )
        
        # Drop the merge key
        merged_df = merged_df.drop('merge_key', axis=1)
    
    # Check merge success
    has_on_ice = merged_df['offensive_on_ice'].notna().sum()
    print(f"\nMerge results:")
    print(f"- Shots with on-ice data: {has_on_ice:,} ({has_on_ice/len(merged_df)*100:.1f}%)")
    print(f"- Shots without on-ice data: {len(merged_df) - has_on_ice:,}")
    
    # Show sample
    print("\nSample merged data:")
    sample = merged_df[merged_df['offensive_on_ice'].notna()].head(3)
    for idx, row in sample.iterrows():
        print(f"\nShot {idx}:")
        print(f"  Shooter: {row['shooter_id']}")
        print(f"  Offensive on ice: {row['offensive_on_ice']}")
        print(f"  Defensive on ice: {row['defensive_on_ice']}")
    
    # For shots without on-ice data, fill with empty lists
    merged_df['offensive_on_ice'] = merged_df['offensive_on_ice'].fillna('[]')
    merged_df['defensive_on_ice'] = merged_df['defensive_on_ice'].fillna('[]')
    
    # Save updated data
    output_path = "data/nhl/processed/training_data_with_on_ice.csv"
    merged_df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")
    
    # Also update the main file
    merged_df.to_csv("data/nhl/processed/training_data_enhanced.csv", index=False)
    print("Updated training_data_enhanced.csv with on-ice columns")
    
    # Validate by checking column presence
    print("\nValidation - checking new columns:")
    test_df = pd.read_csv("data/nhl/processed/training_data_enhanced.csv", nrows=1)
    if 'offensive_on_ice' in test_df.columns and 'defensive_on_ice' in test_df.columns:
        print("[OK] On-ice columns successfully added!")
    else:
        print("[ERROR] On-ice columns not found in saved file")

if __name__ == "__main__":
    main()