#!/usr/bin/env python3
"""
Simple CSV audit without pandas dependency
"""

import csv
import os
from pathlib import Path
from collections import defaultdict

def audit_csv_file(filepath):
    """Audit a single CSV file"""
    result = {
        'file': str(filepath),
        'exists': os.path.exists(filepath),
        'size_mb': 0,
        'rows': 0,
        'columns': [],
        'errors': []
    }
    
    if not result['exists']:
        result['errors'].append('File does not exist')
        return result
    
    try:
        # Get file size
        result['size_mb'] = os.path.getsize(filepath) / (1024 * 1024)
        
        # Read CSV
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            
            # Get headers
            try:
                headers = next(reader)
                result['columns'] = headers
            except StopIteration:
                result['errors'].append('Empty file')
                return result
            
            # Count rows
            row_count = 0
            for row in reader:
                row_count += 1
                if row_count >= 100000:  # Stop counting after 100k for performance
                    result['rows'] = f"{row_count}+"
                    break
            else:
                result['rows'] = row_count
                
    except Exception as e:
        result['errors'].append(f"Error reading file: {str(e)}")
    
    return result

def main():
    # Find all CSV files
    base_path = Path('/mnt/c/Users/Robert Wolfe/Desktop/renewed-solutions/penguins_ai/data/nhl')
    csv_files = list(base_path.rglob('*.csv'))
    
    print(f"Found {len(csv_files)} CSV files to audit\n")
    
    # Group files by directory
    files_by_dir = defaultdict(list)
    for csv_file in csv_files:
        dir_name = csv_file.parent.name
        files_by_dir[dir_name].append(csv_file)
    
    # Audit each file
    for dir_name, files in sorted(files_by_dir.items()):
        print(f"\n{'='*80}")
        print(f"Directory: {dir_name}")
        print(f"{'='*80}")
        
        for csv_file in sorted(files):
            audit = audit_csv_file(csv_file)
            
            print(f"\n{csv_file.name}:")
            print(f"  Size: {audit['size_mb']:.2f} MB")
            print(f"  Rows: {audit['rows']}")
            print(f"  Columns: {len(audit['columns'])}")
            
            if audit['errors']:
                print(f"  ERRORS: {audit['errors']}")
            
            # Show column names
            if audit['columns']:
                print(f"  Columns:")
                # Group columns by 5 for readability
                for i in range(0, len(audit['columns']), 5):
                    cols = audit['columns'][i:i+5]
                    print(f"    {', '.join(cols)}")
    
    # Check for common column patterns
    print(f"\n{'='*80}")
    print("COMMON COLUMN ANALYSIS")
    print(f"{'='*80}")
    
    # Analyze shot-related files
    shot_files = [f for f in csv_files if 'shot' in f.name.lower()]
    if shot_files:
        print("\nShot-related files:")
        shot_columns = {}
        for f in shot_files:
            audit = audit_csv_file(f)
            if audit['columns']:
                shot_columns[f.name] = set(audit['columns'])
        
        # Find common columns
        if shot_columns:
            common = set.intersection(*shot_columns.values())
            print(f"  Common columns ({len(common)}): {sorted(common)[:10]}...")
            
            # Find unique columns per file
            for fname, cols in shot_columns.items():
                unique = cols - common
                if unique:
                    print(f"  {fname} unique columns: {sorted(unique)[:5]}...")
    
    # Analyze training files
    training_files = [f for f in csv_files if 'training' in f.name.lower()]
    if training_files:
        print("\nTraining-related files:")
        training_columns = {}
        for f in training_files:
            audit = audit_csv_file(f)
            if audit['columns']:
                training_columns[f.name] = set(audit['columns'])
        
        # Find common columns
        if training_columns:
            common = set.intersection(*training_columns.values())
            print(f"  Common columns ({len(common)}): {sorted(common)[:10]}...")
            
            # Find unique columns per file
            for fname, cols in training_columns.items():
                unique = cols - common
                if unique:
                    print(f"  {fname} unique columns: {sorted(unique)[:5]}...")

if __name__ == '__main__':
    main()