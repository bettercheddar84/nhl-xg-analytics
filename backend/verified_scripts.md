# Data Scripts

Error Handling: Check all columns exist before running the script
    Print error and stop script if no match
Always write script to print 25 records for testing before running a full live script

NEEDS:
Shooter position - Still not in your data!
On-ice players - Only have for ~4K shots, need for all 312K
Player quality metrics - Need to merge MoneyPuck data

## 1.  (scripts/add_advanced_features.py)  

Script Purpose
Enhances shot data with advanced contextual features for xG modeling by calculating momentum, location danger, and pre-shot sequence characteristics.
Input Files
1. data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv
Required columns:

game_id (int): Unique game identifier
shooter_id (int): Player ID who took shot
game_seconds (int): Seconds elapsed in game
is_goal (int): Binary goal indicator (0/1)
prev_event_x (float): X coordinate of previous event
prev_event_y (float): Y coordinate of previous event
x_coord (float): X coordinate of shot
y_coord (float): Y coordinate of shot
shot_angle (float): Angle to net in degrees
time_since_prev_event (float): Seconds since last event
prev_event_type (str): Type of previous event
is_rush (int): Rush indicator (0/1)
speed_from_prev (float): Speed from previous event
time_since_zone_entry (float): Seconds since zone entry
is_powerplay (int): Power play indicator (0/1)
is_shorthanded (int): Short handed indicator (0/1)
empty_net (int): Empty net indicator (0/1)

2. data/nhl/processed/goal_sequences_fixed.csv
Required columns:

game_id (int): Game identifier
shooter_id (int): Goal scorer ID
goal_time (int): Time of goal in game seconds
assist1_id (float): First assist player ID (nullable)
assist2_id (float): Second assist player ID (nullable)
shots_before_goal (int): Shots in sequence before goal
hits_before_goal (int): Hits before goal
sequence_duration (float): Duration of offensive sequence
quick_strike (int): Quick goal indicator (0/1)
off_faceoff (int): Goal off faceoff (0/1)
offensive_zone_events (int): Events in offensive zone
is_rebound (int): Rebound goal (0/1)
sustained_pressure (int): Sustained pressure indicator (0/1)

Calculated Features (New Columns)
Royal Road Features

royal_road_pass (int): Cross-slot pass indicator (0/1)
pass_angle_change (float): Pass angle change in degrees (0-180)

Momentum Features

goals_last_1min (float): Goals in last 60 seconds
goals_last_5min (float): Goals in last 300 seconds
goals_last_10min (float): Goals in last 600 seconds
shots_last_1min (float): Shots in last 60 seconds
shots_last_5min (float): Shots in last 300 seconds
shots_last_10min (float): Shots in last 600 seconds
shot_momentum_ratio (float): Ratio of recent shots

Rush Quality

rush_quality_score (float): Speed-weighted rush quality (0-1)
quick_zone_to_shot (int): Quick shot after zone entry (0/1)

Location Danger

in_slot (int): Shot from slot area (0/1)
in_crease (int): Shot from crease area (0/1)
from_point (int): Shot from point (0/1)
location_danger_score (float): Combined location danger (0-1)

Pressure Indicators
low_pressure_shot (int): Low defensive pressure (0/1)
high_pressure_shot (int): High defensive pressure (0/1)

Situation
situation (str): Game situation ["ES", "PP", "SH", "EN"]

Output Files
1. data/nhl/processed/training_data_enhanced.csv

All original columns from shots data
All merged columns from goal sequences (only populated for goals)
All calculated features listed above
Shape: Same number of rows as input (312k), ~95 columns

2. data/nhl/processed/training_data_model_ready.csv

Essential features only (subset of ~45 columns)
Missing columns (not in source data):

shooter_position
assist1_position
assist2_position
passing_combo
shooter_height_advantage

Key Issues

Merge Logic Problem: Tries to merge goal-specific sequence data onto ALL shots
Missing Features: Lists features in "essential" that don't exist in source data
No Error Handling: Assumes all columns exist without checking
Inefficient Momentum Calculation: Uses is_goal for both count and sum in rolling windows

The script has good feature engineering ideas but flawed implementation, especially the merge logic that conflates goal-specific sequences with general shot context.


## 2. (scripts/analyze_corsi_vs_fastbreak_risk.py) 

Script Purpose
Analyzes the trade-off between shot volume (Corsi) and fast break risk to find optimal shot selection strategy.
Key Functions

extract_fast_breaks(): Identifies failed shots leading to opponent goals within 30s
calculate_shot_value_equation(): Net value = P(goal) + P(rebound) - P(fast break against)
find_optimal_corsi_strategy(): Finds danger score threshold maximizing net goals

Current Issues

Flawed fast break detection: Any opponent goal within 30s counts as "fast break" - doesn't verify causation
Missing PBP integration: Could use play-by-play to track actual possession changes
No validation: Doesn't check if is_rush flag on opponent goals correlates with findings

Do We Need It?
Yes, but modified. The concept is valuable - teams need to know when shot attempts become counterproductive. But it needs:
pythondef improve_fast_break_detection(self):
    """Use PBP data to verify fast breaks"""
    # Check for actual possession change
    # Verify rush indicators
    # Track zone progression
    # Validate time thresholds
The analysis could significantly impact strategy if the detection is accurate. Teams avoiding low-quality shots that create odd-man rushes could prevent 10-20 goals per season.

## 4. (scripts/analyze_shot_accuracy_impact.py) 



## 5. (scripts/analyze_shot_patterns.py) 
(scripts/audit_nhl_csv_files.py) 
(scripts/build_complete_dataset.py) 
(scripts/build_complete_xg_features.py) 
(scripts/build_goalie_workload.py) 
(scripts/build_on_ice_quality.py) 
(scripts/build_player_embeddings.py) 
(scripts/build_player_tiers.py) 
(scripts/build_shift_patterns.py) 
(scripts/calculate_hockey_babip.py) 
(scripts/calculate_missing_stats.py) 
(scripts/calculate_on_ice_quality.py) 
(scripts/calculate_shot_value_decay.py) 
(scripts/check_missing_players.py) 
(scripts/check_nhl_features.py) 
(scripts/create_training_assists_data.py) 
(scripts/extract_assist_patterns.py) 
(scripts/extract_season_features.py) 
(scripts/extract_shot_consequences.py) 
(scripts/extract_zone_time.py) 
(scripts/fetch_complete_shift_data.py) 
(scripts/fetch_play_by_play.py) 
(scripts/fix_column_names.py) 
(scripts/merge_on_ice_data.py) 
(scripts/merge_training_data.py) 
(scripts/player_archetype_recommendations.py) 
(scripts/player_shot_decision_analyzer.py) 
(scripts/prepare_xg_training_data.py) 
(scripts/simple_csv_audit.py)