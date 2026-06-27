# Documentation vs Reality: NHL Data Discrepancies

## Summary of Findings

After analyzing the documentation files against actual data structures, I've identified several significant discrepancies between what's documented and what actually exists in the data files.

## 1. Column Count Mismatch

### Documented vs Actual
- **ALL_NHL_VARIABLES.md** claims `training_data_enhanced.csv` has **134 columns**
- **Actual file** has only **98 columns**
- Missing: 36 columns that are documented but don't exist

### Missing Advanced Features (Documented but Not Found)
The following features are mentioned in ALL_NHL_VARIABLES.md but don't exist in the actual enhanced training data:

#### Shot Location Features (lines 39-44)
- `high_slot`, `low_slot` 
- `right_circle`, `left_circle`
- `right_point`, `left_point`
- `below_goal_line`
- `from_behind_net`
- `in_slot`, `in_crease`, `from_point` (these DO exist in some files)

#### Pass Features (lines 34-38)
- `royal_road_pass` - Critical feature mentioned in ADVANCED_XG_IMPLEMENTATION.md
- `east_west_pass`
- `pass_distance`
- `pass_angle`
- `passes_in_sequence`

#### Movement & Speed Features (lines 56-63)
- `pre_shot_movement`
- `lateral_movement`, `vertical_movement`
- `total_movement`, `movement_speed`
- `shot_velocity_estimate`
- `release_time`
- `deception_factor`

#### Defensive Features (lines 64-68)
- `shooting_space`
- `defender_distance`
- `shooting_lane_open`
- `traffic_in_front`
- `net_front_presence`

#### Advanced Metrics (lines 50-55)
- `expected_goal_value`
- `shot_quality_index`
- `danger_zone_shot`
- `high_danger_shot`, `medium_danger_shot`, `low_danger_shot`

#### Game Context Features (lines 84-134)
Many contextual features listed including:
- `momentum_shift`, `momentum_factor`
- `clutch_situation`, `must_score_situation`
- `elimination_game`, `playoff_intensity`
- `rivalry_game`, `divisional_matchup`
- `venue_advantage`, `altitude_factor`
- `travel_fatigue`, `back_to_back`
- And many more...

## 2. Data Type & Structure Issues

### Raw Data Structure (Actual: 70 columns)
The raw shots file (`nhl_shots_2024-10-01_to_2025-04-15.csv`) actually has 70 columns, matching what's documented in NHL_DATA_DICTIONARY.md. This documentation appears accurate.

### Enhanced Data Structure Issues
1. **Column 134 claim is false** - No version of training data has 134 columns
2. **Most advanced features exist only in documentation**
3. **Some features mentioned in ADVANCED_XG_IMPLEMENTATION.md haven't been implemented**

## 3. Feature Engineering Scripts

### Scripts That Exist But Haven't Been Run on Full Data
1. `add_advanced_features.py` - Contains royal_road_pass calculation but not applied to training data
2. `build_complete_xg_features.py` - Referenced in docs but doesn't create the documented features
3. Many calculation scripts exist but their outputs aren't in the training data

### Features That ARE Present
- Basic shot features (distance, angle, type)
- Game state features (score, period, strength)
- Some calculated features (is_rebound, is_rush, offensive_zone_time)
- Player attributes (height, weight, position, handedness)
- Location danger score (exists but calculation method unclear)

## 4. Documentation Inconsistencies

### ADVANCED_XG_IMPLEMENTATION.md Claims
- "150+ features" - Reality: 98 features
- "Complete Feature Engineering" - Many features not implemented
- "Player embeddings from career stats" - Not found in training data
- "Shot consequences tracking" - Partially implemented

### ALL_NHL_VARIABLES.md Issues
- Lists many calculated features that don't exist
- Column counts are wrong for multiple files
- Describes processing that hasn't been completed

## 5. Critical Missing Features for xG Model

Based on the documentation, these important features are missing:
1. **Royal road passes** - Key predictor of high-danger chances
2. **Pass metrics** - Distance, angle, type of passes leading to shots
3. **Shot location zones** - Detailed zone breakdowns (slot, circles, points)
4. **Defensive pressure** - No defender proximity or shooting lane info
5. **Advanced movement** - Pre-shot movement, lateral shifts
6. **True player embeddings** - Just basic stats, not learned representations

## 6. Recommendations

### Immediate Actions Needed
1. **Run feature engineering scripts** to create documented features
2. **Update documentation** to reflect actual data structure
3. **Implement missing critical features** (especially royal road passes)
4. **Verify all column counts and names** in documentation

### Priority Features to Add
1. Royal road pass detection
2. Detailed shot location zones
3. Pass sequence metrics
4. Defensive pressure indicators
5. Player quality differentials (partially implemented)

### Documentation Updates
1. Fix column counts in ALL_NHL_VARIABLES.md
2. Mark which features are "planned" vs "implemented"
3. Add data pipeline documentation showing which scripts create which features
4. Update ADVANCED_XG_IMPLEMENTATION.md to reflect current state

## Conclusion

There's a significant gap between the documented "advanced" xG model and what's actually implemented. The current training data has basic features but lacks many of the sophisticated metrics described in the documentation. This explains why model performance might not match expectations - many key predictive features simply don't exist in the data yet.

## Specific Feature Implementation Status

### Features Referenced in Neural Network Model but Not in Data:
The `train_neural_xg_model.py` script expects these features that don't exist in the training data:
- `royal_road_pass` - Mentioned in scripts but not in actual CSVs
- `screen_quality` - Not found in any data file
- `rush_quality` - Different from `rush_quality_score` which may exist
- `quick_release` - Not in data
- `offensive_quality_sum`, `defensive_quality_sum` - Only in goals data, not all shots
- `quality_differential` - Not in training data
- `elite_shooters_on_ice`, `weak_defenders_on_ice` - Not calculated
- `height_advantage` - Different from `shooter_height_advantage`
- `offensive_xg_impact`, `defensive_xg_impact`, `xg_differential` - Not found
- `led_to_opponent_shot`, `created_rebound_chance` - Consequence features not implemented
- `rim_around_danger`, `fast_break_risk` - Not in data

### Features Actually Being Used in Current Model:
The simpler `train_xg_shots_2024.py` uses MoneyPuck data with different feature names:
- `arenaAdjustedShotDistance` (not `shot_distance`)
- `arenaAdjustedXCordABS`, `arenaAdjustedYCordAbs` (not `x_coord`, `y_coord`)
- `shotAngleAdjusted` (not `shot_angle`)
- `timeSinceFaceoff`, `timeLeft` (different format)
- `shotRebound`, `shotRush` (not `is_rebound`, `is_rush`)

This shows a fundamental disconnect - the documentation describes features for NHL API data, but some training scripts use MoneyPuck data with completely different column names.