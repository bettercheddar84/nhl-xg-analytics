#!/usr/bin/env python3
"""
Comprehensive audit of NHL CSV files to identify data inconsistencies
"""

import pandas as pd
import os
from pathlib import Path
import json
from datetime import datetime

def audit_csv_file(filepath):
    """Audit a single CSV file"""
    result = {
        'file': str(filepath),
        'exists': os.path.exists(filepath),
        'size_mb': 0,
        'rows': 0,
        'columns': [],
        'dtypes': {},
        'null_counts': {},
        'sample_values': {},
        'errors': []
    }
    
    if not result['exists']:
        result['errors'].append('File does not exist')
        return result
    
    try:
        # Get file size
        result['size_mb'] = os.path.getsize(filepath) / (1024 * 1024)
        
        # Read CSV with low_memory=False to infer types better
        df = pd.read_csv(filepath, low_memory=False, nrows=5)  # First read just headers
        result['columns'] = list(df.columns)
        
        # Now read full file
        df = pd.read_csv(filepath, low_memory=False)
        result['rows'] = len(df)
        
        # Get data types
        result['dtypes'] = {col: str(dtype) for col, dtype in df.dtypes.items()}
        
        # Get null counts
        result['null_counts'] = df.isnull().sum().to_dict()
        
        # Get sample values (first 3 non-null values)
        for col in df.columns:
            non_null = df[col].dropna()
            if len(non_null) > 0:
                result['sample_values'][col] = non_null.head(3).tolist()
            else:
                result['sample_values'][col] = []
                
    except Exception as e:
        result['errors'].append(f"Error reading file: {str(e)}")
    
    return result

def find_column_inconsistencies(audits):
    """Find inconsistencies between related files"""
    inconsistencies = []
    
    # Group files by category
    categories = {
        'shots': ['nhl_shots', 'shots_with'],
        'training': ['training_data'],
        'player': ['player_tiers', 'player_shot', 'player_shift'],
        'goalie': ['goalie_workload', 'goalie_shift'],
        'processed': ['_patterns', 'sequences', 'zone_times']
    }
    
    for category, patterns in categories.items():
        category_files = []
        for audit in audits:
            filename = os.path.basename(audit['file'])
            if any(pattern in filename for pattern in patterns):
                category_files.append(audit)
        
        if len(category_files) > 1:
            # Check for column mismatches
            all_columns = {}
            for file_audit in category_files:
                filename = os.path.basename(file_audit['file'])
                all_columns[filename] = set(file_audit['columns'])
            
            # Find common columns
            if all_columns:
                common_cols = set.intersection(*all_columns.values())
                for filename, cols in all_columns.items():
                    unique_cols = cols - common_cols
                    if unique_cols:
                        inconsistencies.append({
                            'category': category,
                            'file': filename,
                            'unique_columns': list(unique_cols),
                            'missing_from_others': True
                        })
    
    return inconsistencies

def check_expected_columns(audits):
    """Check if files have expected columns based on their names"""
    expected = {
        'shots': ['game_id', 'x', 'y', 'player_id', 'shot_type', 'period'],
        'training': ['game_id', 'shot_distance', 'shot_angle', 'is_goal'],
        'player': ['player_id', 'player_name'],
        'goalie': ['goalie_id', 'goalie_name'],
        'shifts': ['shift_start', 'shift_end', 'player_id']
    }
    
    missing = []
    for audit in audits:
        filename = os.path.basename(audit['file'])
        file_cols = set(audit['columns'])
        
        for category, expected_cols in expected.items():
            if category in filename.lower():
                missing_cols = set(expected_cols) - file_cols
                if missing_cols:
                    # Check for similar column names (case variations, underscores vs camelCase)
                    likely_matches = {}
                    for missing_col in missing_cols:
                        for actual_col in file_cols:
                            if (missing_col.lower() in actual_col.lower() or 
                                actual_col.lower() in missing_col.lower()):
                                likely_matches[missing_col] = actual_col
                    
                    missing.append({
                        'file': filename,
                        'category': category,
                        'missing_columns': list(missing_cols),
                        'likely_matches': likely_matches,
                        'actual_columns': list(file_cols)[:10]  # First 10 for reference
                    })
    
    return missing

def main():
    # Find all CSV files
    csv_files = []
    base_path = Path('/mnt/c/Users/Robert Wolfe/Desktop/renewed-solutions/penguins_ai/data/nhl')
    
    for csv_file in base_path.rglob('*.csv'):
        csv_files.append(csv_file)
    
    print(f"Found {len(csv_files)} CSV files to audit\n")
    
    # Audit each file
    audits = []
    for csv_file in sorted(csv_files):
        print(f"Auditing: {csv_file.name}")
        audit = audit_csv_file(csv_file)
        audits.append(audit)
    
    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_files': len(audits),
            'total_size_mb': sum(a['size_mb'] for a in audits),
            'total_rows': sum(a['rows'] for a in audits),
            'files_with_errors': sum(1 for a in audits if a['errors'])
        },
        'files': audits,
        'inconsistencies': find_column_inconsistencies(audits),
        'missing_expected': check_expected_columns(audits)
    }
    
    # Save detailed report
    with open('/mnt/c/Users/Robert Wolfe/Desktop/renewed-solutions/penguins_ai/data/nhl/audit_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "="*80)
    print("AUDIT SUMMARY")
    print("="*80)
    print(f"Total CSV files: {report['summary']['total_files']}")
    print(f"Total size: {report['summary']['total_size_mb']:.2f} MB")
    print(f"Total rows: {report['summary']['total_rows']:,}")
    print(f"Files with errors: {report['summary']['files_with_errors']}")
    
    print("\n" + "-"*80)
    print("FILE DETAILS")
    print("-"*80)
    for audit in audits:
        filename = os.path.basename(audit['file'])
        print(f"\n{filename}:")
        print(f"  Rows: {audit['rows']:,}")
        print(f"  Columns: {len(audit['columns'])}")
        print(f"  Size: {audit['size_mb']:.2f} MB")
        if audit['errors']:
            print(f"  ERRORS: {audit['errors']}")
        
        # Show first 5 columns
        if audit['columns']:
            print(f"  First 5 columns: {audit['columns'][:5]}")
    
    print("\n" + "-"*80)
    print("COLUMN INCONSISTENCIES")
    print("-"*80)
    if report['inconsistencies']:
        for inc in report['inconsistencies']:
            print(f"\n{inc['file']} ({inc['category']} category):")
            print(f"  Unique columns: {inc['unique_columns']}")
    else:
        print("No major inconsistencies found between related files")
    
    print("\n" + "-"*80)
    print("MISSING EXPECTED COLUMNS")
    print("-"*80)
    if report['missing_expected']:
        for miss in report['missing_expected']:
            print(f"\n{miss['file']} ({miss['category']} category):")
            print(f"  Missing: {miss['missing_columns']}")
            if miss['likely_matches']:
                print(f"  Likely matches: {miss['likely_matches']}")
            print(f"  Actual columns (first 10): {miss['actual_columns']}")
    else:
        print("All files have their expected columns")
    
    print("\n" + "="*80)
    print(f"Full report saved to: data/nhl/audit_report.json")

if __name__ == '__main__':
    main()