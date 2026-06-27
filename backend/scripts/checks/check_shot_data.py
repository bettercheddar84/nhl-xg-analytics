import pandas as pd

# Load shot data
df = pd.read_csv("data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv")

print("=== DATA STRUCTURE ===")
print(f"Total rows: {len(df):,}")
print(f"\nColumns: {list(df.columns)}")

print("\n=== MISSING DATA ===")
print(f"Missing shooter_id: {df['shooter_id'].isna().sum():,}")
print(f"Missing shooter_name: {df['shooter_name'].isna().sum():,}")
print(f"Missing goalie_id: {df['goalie_id'].isna().sum():,}")

print("\n=== SAMPLE ROWS WITH MISSING DATA ===")
missing_shooter = df[df["shooter_id"].isna()].head(3)
if len(missing_shooter) > 0:
    print("\nRows with missing shooter_id:")
    print(missing_shooter[["game_id", "event_type", "shooter_id", "shooter_name", "goalie_id"]])

print("\n=== EVENT TYPE BREAKDOWN ===")
print(df["event_type"].value_counts())

print("\n=== SAMPLE GOOD DATA ===")
good_data = df[df["shooter_id"].notna() & df["is_goal"] == 1].head(5)
print("\nSample goals with valid shooter IDs:")
for idx, row in good_data.iterrows():
    print(f"  Shooter: {row['shooter_name']} (ID: {row['shooter_id']})")

print("\n=== UNIQUE PLAYERS ===")
valid_shooters = df[df["shooter_id"].notna()]
print(f"Unique shooters with valid IDs: {valid_shooters['shooter_id'].nunique()}")
print(f"Unique shooter names: {valid_shooters['shooter_name'].nunique()}")
