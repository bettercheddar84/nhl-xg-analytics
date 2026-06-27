# Documentation vs Reality Discrepancies

## Executive Summary
The documentation describes an advanced xG model with 150+ features, but the actual implementation has only 98 columns in the main training data. Many critical features mentioned in documentation are completely missing from the data.

## Critical Discrepancies

### 1. Column Count Mismatch
- **Documented**: training_data_enhanced.csv has 134 columns
- **Reality**: training_data_enhanced.csv has only 98 columns
- **Missing**: 36+ documented features don't exist

### 2. Completely Missing Feature Categories

#### Pass-Related Features (NOT IN DATA)
- royal_road_pass
- east_west_pass
- pass_distance
- pass_angle
- passes_in_sequence
- cross_slot_pass
- down_low_pass
- high_danger_passes

#### Shot Location Zones (NOT IN DATA)
- high_slot
- low_slot
- right_circle
- left_circle
- right_point
- left_point
- below_goal_line
- from_behind_net

#### Pre-Shot Movement (NOT IN DATA)
- pre_shot_movement
- lateral_movement
- vertical_movement
- total_movement
- movement_speed
- angle_change_rate

#### Defensive Pressure (NOT IN DATA)
- defender_distance
- shooting_lane_open
- traffic_in_front
- net_front_presence
- goalie_screened

#### Advanced Shot Types (NOT IN DATA)
- one_timer_setup
- quick_release
- off_the_rush
- cycle_play
- broken_play
- screened_shot

#### Game Context Features (NOT IN DATA)
- momentum_shift
- momentum_factor
- clutch_situation
- must_score_situation
- elimination_game
- playoff_intensity
- rivalry_game
- home_crowd_factor

#### Advanced Metrics (NOT IN DATA)
- expected_goal_value
- shot_quality_index
- danger_zone_shot
- deception_factor
- shooting_space
- shot_velocity_estimate

### 3. Feature Name Inconsistencies

| Documentation Says | Reality Has | Issue |
|-------------------|-------------|-------|
| offensive_rating | Not present | Scripts expect this from player_tiers.csv |
| is_rebound | Not in base data | Only in some processed files |
| assist1_id | Present in raw, missing in enhanced | Column dropped during processing |
| zone_time | Present but all zeros | Calculation never completed |

### 4. Data Processing Gaps

Scripts that exist but haven't been run on full dataset:
- calculate_on_ice_quality.py (fails due to missing offensive_rating)
- calculate_shot_value_decay.py (fails due to missing is_rebound)
- calculate_hockey_babip.py (fails due to data structure issues)
- build_player_embeddings.py (fails due to string/int type issues)

### 5. MoneyPuck vs NHL API Confusion

Some scripts expect MoneyPuck column names:
- arenaAdjustedShotDistance
- shotAngleAdjusted
- shotGeneratedRebound

But data uses NHL API names:
- shot_distance
- shot_angle
- is_rebound

## Impact on Model

The missing features severely limit the model's capability:

1. **No passing data** - Can't identify high-danger passing plays
2. **No movement data** - Can't account for pre-shot player movement
3. **No defensive pressure** - Can't adjust for shooting difficulty
4. **Limited location detail** - Only have x,y coords, not semantic zones
5. **No momentum/context** - Missing game flow features

## Recommendations

### Immediate Actions
1. Update documentation to reflect actual available features
2. Fix column name inconsistencies in processing scripts
3. Run working feature extraction scripts on full dataset

### Feature Engineering Needed
1. Calculate shot location zones from x,y coordinates
2. Derive passing metrics from play-by-play sequences
3. Calculate momentum from recent events
4. Extract defensive pressure from on-ice player positions

### Long-term Improvements
1. Implement missing feature calculations
2. Create unified data pipeline with consistent naming
3. Add data validation to ensure features exist before use
4. Version control feature sets for reproducibility

## Scripts That Need Fixing

1. **calculate_on_ice_quality.py**
   - Line 73: Expects 'offensive_rating' column that doesn't exist
   - Need to calculate ratings from raw stats instead

2. **calculate_shot_value_decay.py**
   - Line 27: Expects 'is_rebound' column
   - Need to use rebound calculation from other scripts

3. **calculate_hockey_babip.py**
   - Line 207: Expects 'total_shots_first' column
   - Data structure mismatch in split-half analysis

4. **build_player_embeddings.py**
   - Line 239: Type error with 'offensive_on_ice' (int vs string)
   - Need to handle data type conversion

5. **calculate_missing_stats.py**
   - Line 476: Expects 'assist1_id' column
   - Column exists in raw but not enhanced data

## Conclusion

The current implementation is much simpler than documented. To achieve the promised "state-of-the-art" xG model, significant feature engineering work is needed. The good news is that many of the calculation scripts exist - they just need to be fixed and run properly.