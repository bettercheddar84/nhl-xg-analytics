# Path: scripts/cleanup_processed_folder.py

import os
import shutil
from datetime import datetime

print("Cleaning up processed folder...\n")

# Create archive directory
archive_dir = f"data/nhl/processed/archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(archive_dir, exist_ok=True)
print(f"Created archive: {archive_dir}")

# Files to delete/archive
files_to_archive = [
    # Failed files from earlier
    "player_shift_patterns.csv",  # Failed to load
    "player_tiers.csv",  # Failed to load
    "rebound_patterns.csv",  # Failed to load
    # Old training files
    "training_data_clean_from_raw.csv",
    "training_data_final_clean.csv",
    "training_data_final_enhanced.csv",
    "training_data_final_fixed.csv",
    "training_data_final_v2.csv",
]

# Move files
moved_count = 0
for file in files_to_archive:
    source = f"data/nhl/processed/{file}"
    if os.path.exists(source):
        dest = os.path.join(archive_dir, file)
        shutil.move(source, dest)
        print(f"✓ Archived: {file}")
        moved_count += 1
    else:
        print(f"✗ Not found: {file}")

print(f"\nMoved {moved_count} files to archive")

# List remaining files
print("\n📁 REMAINING FILES IN PROCESSED:")
remaining = os.listdir("data/nhl/processed")
remaining = [f for f in remaining if f != os.path.basename(archive_dir)]
remaining.sort()

for i, file in enumerate(remaining, 1):
    size = os.path.getsize(f"data/nhl/processed/{file}") / 1024 / 1024
    print(f"{i:2d}. {file:<40} {size:>6.1f} MB")

print(f"\nTotal files: {len(remaining)}")

# Summary of key files
print("\n✅ KEY FILES:")
key_files = [
    ("NHL_AI_TRAINING_FINAL.csv", "Main training dataset"),
    ("player_turnover_risk.csv", "Player quality metrics"),
    ("skater_shift_patterns.csv", "Player fatigue patterns"),
    ("goalie_workload.csv", "Goalie fatigue data"),
]

for file, desc in key_files:
    if file in remaining:
        print(f"- {file}: {desc}")
