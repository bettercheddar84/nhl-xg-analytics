#!/usr/bin/env python3
"""
Fix column naming issues in the enhanced training data
"""

import pandas as pd
import sys
from pathlib import Path

def diagnose_columns():
    """Diagnose column naming issues"""
    
    # Load the data
    enhanced_path = "data/nhl/processed/training_data_enhanced.csv"
    raw_path = "data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv"
    
    print("=== COLUMN DIAGNOSIS ===")
    
    # Read just the headers
    enhanced_df = pd.read_csv(enhanced_path, nrows=1)
    raw_df = pd.read_csv(raw_path, nrows=1)
    
    print(f"\nEnhanced data columns: {len(enhanced_df.columns)}")
    print(f"Raw data columns: {len(raw_df.columns)}")
    
    # Find duplicate column names (with suffixes)
    enhanced_cols = list(enhanced_df.columns)
    
    # Check for suffix patterns
    suffix_cols = [col for col in enhanced_cols if col.endswith(('_x', '_y', '_from_pbp'))]
    if suffix_cols:
        print(f"\nColumns with merge suffixes: {len(suffix_cols)}")
        for col in sorted(suffix_cols):
            base_name = col.rsplit('_', 1)[0] if '_x' in col or '_y' in col else col.replace('_from_pbp', '')
            print(f"  {col} (base: {base_name})")
    
    # Check what scripts are looking for
    print("\nColumns scripts are looking for but might be missing:")
    expected_cols = [
        'offensive_rating', 'defensive_rating', 'net_rating',
        'offensive_on_ice', 'defensive_on_ice',
        'true_shooting_pct', 'scoring_efficiency',
        'assist1_id', 'assist2_id', 'is_rebound'
    ]
    
    for col in expected_cols:
        if col in enhanced_cols:
            print(f"  [OK] {col} - exists")
        else:
            # Check for suffixed versions
            suffixed = [c for c in enhanced_cols if c.startswith(col)]
            if suffixed:
                print(f"  [?] {col} - found as: {suffixed}")
            else:
                print(f"  [X] {col} - missing")
    
    return enhanced_cols, list(raw_df.columns)

def fix_columns():
    """Fix the column naming issues"""
    
    print("\n=== FIXING COLUMNS ===")
    
    # Load the data
    df = pd.read_csv("data/nhl/processed/training_data_enhanced.csv")
    
    # Handle suffixed columns from merge
    # For _x/_y suffixes, typically _x is from the left dataframe (original)
    rename_map = {}
    
    for col in df.columns:
        if col.endswith('_x'):
            base_name = col[:-2]
            # Check if there's a _y version
            if f"{base_name}_y" in df.columns:
                # Keep _x as the main column
                rename_map[col] = base_name
                print(f"Renaming {col} -> {base_name}")
        elif col.endswith('_from_pbp'):
            # This seems to be a duplicate from play-by-play data
            base_name = col.replace('_from_pbp', '')
            if base_name not in df.columns and f"{base_name}_x" not in df.columns:
                rename_map[col] = base_name
                print(f"Renaming {col} -> {base_name}")
    
    # Apply renames
    if rename_map:
        df = df.rename(columns=rename_map)
        
        # Drop _y columns if we kept _x
        drop_cols = []
        for col in df.columns:
            if col.endswith('_y'):
                base_name = col[:-2]
                if base_name in df.columns:
                    drop_cols.append(col)
                    print(f"Dropping duplicate: {col}")
        
        if drop_cols:
            df = df.drop(columns=drop_cols)
    
    # Save the fixed data
    output_path = "data/nhl/processed/training_data_fixed.csv"
    df.to_csv(output_path, index=False)
    print(f"\nFixed data saved to: {output_path}")
    print(f"Final columns: {len(df.columns)}")
    
    return df

if __name__ == "__main__":
    # First diagnose
    enhanced_cols, raw_cols = diagnose_columns()
    
    # Then fix
    df = fix_columns()
    
    # Verify fix
    print("\n=== VERIFICATION ===")
    critical_cols = ['assist1_id', 'assist2_id', 'is_rebound']
    for col in critical_cols:
        if col in df.columns:
            print(f"[OK] {col} is now available")
        else:
            print(f"[X] {col} is still missing")