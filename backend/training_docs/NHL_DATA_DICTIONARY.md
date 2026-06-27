# NHL Shots Data Dictionary

## Overview
This document provides a comprehensive data dictionary for the NHL shots raw data file:
`data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv`

## Column Definitions

### Game Identifiers
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| game_id | int | Unique identifier for the game (format: YYYYGGGGGG) |
| season | int | Season identifier (e.g., 20242025 for 2024-25 season) |
| game_type | int | Game type code (2 = Regular season, 3 = Playoffs) |
| game_date | string | Date of the game (YYYY-MM-DD format) |
| venue | string | Name of the arena where game was played |

### Time Information
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| period | int | Period number (1, 2, 3, 4+ for overtime) |
| period_type | string | Type of period - **Enum values:** REG, OT, SO |
| time_in_period | int | Seconds elapsed in the current period |
| time_remaining | string | Time remaining in period (MM:SS format) |
| game_seconds | int | Total seconds elapsed in the game |

### Shot Event Details
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| event_type | string | Type of shot event - **Enum values:** shot-on-goal, missed-shot, blocked-shot, goal |
| x_coord | float | X-coordinate of shot location on ice |
| y_coord | float | Y-coordinate of shot location on ice |
| zone_code | string | Zone where shot occurred - **Enum values:** O (Offensive), D (Defensive), N (Neutral) |
| shot_type | string | Type of shot - **Enum values:** wrist, slap, snap, backhand, tip-in, deflected, wrap-around, bat, poke, between-legs, cradle |
| is_goal | boolean | Whether the shot resulted in a goal (0/1) |
| reason | string | Reason for missed shot - **Enum values:** wide-left, wide-right, high-and-wide-left, high-and-wide-right, above-crossbar, hit-crossbar, hit-left-post, hit-right-post, short, blocked, teammate-blocked, failed-bank-attempt, other-block |

### Calculated Metrics
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| shot_distance | float | Distance from goal in feet |
| shot_angle | float | Angle to goal in degrees |

### Player Information
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| shooter_id | int | Player ID of the shooter |
| shooter_name | string | Name of the shooter |
| goalie_id | float | Player ID of the goalie (NaN if empty net) |
| goalie_name | string | Name of the goalie |
| assist1_id | float | Player ID of primary assist (NaN if no assist) |
| assist1_name | string | Name of primary assist player |
| assist2_id | float | Player ID of secondary assist (NaN if no assist) |
| assist2_name | string | Name of secondary assist player |
| blocker_id | float | Player ID of shot blocker (NaN if not blocked) |

### Team Information
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| shooting_team_id | int | Team ID of shooting team |
| shooting_team | string | Three-letter code of shooting team |
| home_team_id | int | Team ID of home team |
| home_team | string | Three-letter code of home team |
| away_team_id | int | Team ID of away team |
| away_team | string | Three-letter code of away team |
| is_home_team | boolean | Whether shooting team is home team (0/1) |

### Game State
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| home_score | int | Home team score at time of shot |
| away_score | int | Away team score at time of shot |
| score_differential | int | Score difference from shooting team perspective |
| is_tied | boolean | Whether game is tied (0/1) |
| is_leading | boolean | Whether shooting team is leading (0/1) |
| home_skaters | int | Number of home team skaters on ice |
| away_skaters | int | Number of away team skaters on ice |
| strength_state | string | Game strength state code (4-digit format: home_goalie + home_skaters + away_goalie + away_skaters) |
| is_powerplay | boolean | Whether shooting team is on power play (0/1) |
| is_shorthanded | boolean | Whether shooting team is shorthanded (0/1) |
| empty_net | boolean | Whether opposing net is empty (0/1) |
| is_penalty_shot | boolean | Whether shot is a penalty shot (0/1) |

### Previous Event Context
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| prev_event_type | string | Type of previous event - **Enum values:** faceoff, hit, giveaway, takeaway, delayed-penalty, failed-shot-attempt, penalty, period-start, stoppage |
| prev_event_x | float | X-coordinate of previous event |
| prev_event_y | float | Y-coordinate of previous event |
| prev_event_team | float | Team ID of previous event |
| time_since_prev_event | int | Seconds since previous event |
| distance_from_prev_event | float | Distance from previous event location |

### Shot Sequence Information
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| time_since_prev_shot | int | Seconds since previous shot |
| prev_shot_result | string | Result of previous shot - **Enum values:** shot-on-goal, missed-shot, blocked-shot, goal |
| shots_in_sequence | int | Number of shots in current sequence |

### Faceoff Context
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| time_since_faceoff | int | Seconds since last faceoff |
| faceoff_win | boolean | Whether shooting team won the faceoff (0/1) |
| faceoff_zone | string | Zone of last faceoff - **Enum values:** O (Offensive), D (Defensive), N (Neutral) |
| is_off_zone_faceoff | boolean | Whether last faceoff was in offensive zone (0/1) |

### Advanced Features
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| is_rebound | boolean | Whether shot is a rebound (0/1) |
| is_rush | boolean | Whether shot came off a rush (0/1) |
| is_one_timer | boolean | Whether shot is a one-timer (0/1) |
| speed_from_prev | float | Speed of puck movement from previous event (feet/second) |
| time_since_zone_entry | float | Seconds since offensive zone entry |
| offensive_zone_time | int | Total seconds in offensive zone |
| is_backhand | boolean | Whether shot is backhand (0/1) |
| is_deflection | boolean | Whether shot is a deflection (0/1) |
| is_wraparound | boolean | Whether shot is a wraparound (0/1) |
| playoff_game | boolean | Whether game is a playoff game (0/1) |

## Strength State Codes

The `strength_state` column uses a 4-digit code representing the on-ice player configuration:
- Digit 1: Home team goalie (1 = goalie on ice, 0 = empty net)
- Digit 2: Home team skaters (3-6 players)
- Digit 3: Away team goalie (1 = goalie on ice, 0 = empty net)
- Digit 4: Away team skaters (3-6 players)

Common values:
- 1551: Even strength (5v5 with both goalies)
- 1451: Home team power play (5v4)
- 1541: Away team power play (4v5)
- 1441: 4v4 play
- 1331: 3v3 play (overtime)
- 0551: Home team empty net
- 1550: Away team empty net

## Data Quality Notes

1. **Missing Values**: 
   - Goalie information is NaN for empty net situations
   - Assist information is NaN when no assists on goals
   - Blocker ID is NaN for non-blocked shots
   - Shot type is empty for blocked shots (blocker perspective)

2. **Coordinate System**:
   - X-coordinates range from -100 to 100 (center ice = 0)
   - Y-coordinates range from -42.5 to 42.5 (center ice = 0)
   - Positive X is offensive zone for home team

3. **Boolean Columns**:
   - All boolean columns use 0/1 encoding
   - 0 = False, 1 = True

4. **Time Fields**:
   - All time measurements are in seconds
   - time_in_period counts up from 0
   - time_remaining counts down to 0:00

# NHL Data Dictionary - Complete Variable List

## Directory Structure
```
data/nhl/
├── aggregated_data_moneypuck/    # MoneyPuck analytics data
├── endpoint_samples/             # NHL API endpoint examples
├── enhanced/                     # Processed shot data with features
├── nhl_api_samples/             # NHL API response samples
├── play_by_play/                # Game play-by-play JSON files
├── processed/                   # Feature-engineered datasets
├── raw/                         # Raw shot data
└── shifts/                      # Player shift data
```

## CSV Files and Their Variables

### 1. aggregated_data_moneypuck/goalies.csv
**Goalie performance metrics from MoneyPuck**
- `playerId`: Unique player identifier
- `season`: Season year (e.g., 20242025)
- `name`: Goalie name
- `team`: Team abbreviation
- `position`: Position (G)
- `situation`: Game situation (all, 5v5, etc.)
- `games_played`: Number of games played
- `icetime`: Total ice time
- `xGoals`: Expected goals against
- `goals`: Actual goals against
- `unblocked_shot_attempts`: Shots faced (unblocked)
- `xRebounds`: Expected rebounds
- `rebounds`: Actual rebounds
- `xFreeze`: Expected frozen pucks
- `freeze`: Actual frozen pucks
- `xOnGoal`: Expected shots on goal
- `ongoal`: Actual shots on goal
- `xPlayStopped`: Expected play stoppages
- `playStopped`: Actual play stoppages
- `xPlayContinuedInZone`: Expected continued play in zone
- `playContinuedInZone`: Actual continued play in zone
- `xPlayContinuedOutsideZone`: Expected continued play outside zone
- `playContinuedOutsideZone`: Actual continued play outside zone
- `flurryAdjustedxGoals`: Adjusted expected goals
- `lowDangerShots`: Low danger shots faced
- `mediumDangerShots`: Medium danger shots faced
- `highDangerShots`: High danger shots faced
- `lowDangerxGoals`: Expected goals from low danger
- `mediumDangerxGoals`: Expected goals from medium danger
- `highDangerxGoals`: Expected goals from high danger
- `lowDangerGoals`: Actual goals from low danger
- `mediumDangerGoals`: Actual goals from medium danger
- `highDangerGoals`: Actual goals from high danger
- `blocked_shot_attempts`: Blocked shots
- `penalityMinutes`: Penalty minutes
- `penalties`: Number of penalties

### 2. aggregated_data_moneypuck/lines.csv
**Line combination performance metrics**
- `lineId`: Unique line identifier
- `season`, `name`, `team`, `position`, `situation`: Basic info
- `games_played`, `icetime`, `iceTimeRank`: Usage metrics
- `xGoalsPercentage`: Expected goals percentage
- `corsiPercentage`: Shot attempt percentage
- `fenwickPercentage`: Unblocked shot attempt percentage
- **For metrics**: xOnGoalFor, xGoalsFor, xReboundsFor, xFreezeFor, xPlayStoppedFor, xPlayContinuedInZoneFor, xPlayContinuedOutsideZoneFor
- **Adjusted metrics**: flurryAdjustedxGoalsFor, scoreVenueAdjustedxGoalsFor, flurryScoreVenueAdjustedxGoalsFor
- **Counting stats**: shotsOnGoalFor, missedShotsFor, blockedShotAttemptsFor, shotAttemptsFor, goalsFor, reboundsFor, reboundGoalsFor
- **Game events**: freezeFor, playStoppedFor, playContinuedInZoneFor, playContinuedOutsideZoneFor
- **Other**: savedShotsOnGoalFor, savedUnblockedShotAttemptsFor, penaltiesFor, penalityMinutesFor, faceOffsWonFor, hitsFor, takeawaysFor, giveawaysFor
- **Danger zones**: lowDangerShotsFor, mediumDangerShotsFor, highDangerShotsFor (plus xGoals and actual goals for each)
- **Score-adjusted**: scoreAdjustedShotsAttemptsFor, unblockedShotAttemptsFor, scoreAdjustedUnblockedShotAttemptsFor
- **Zone**: dZoneGiveawaysFor
- **Rebounds**: xGoalsFromxReboundsOfShotsFor, xGoalsFromActualReboundsOfShotsFor, reboundxGoalsFor
- **Shot credit**: totalShotCreditFor, scoreAdjustedTotalShotCreditFor, scoreFlurryAdjustedTotalShotCreditFor
- **Against metrics**: All above metrics repeated with "Against" suffix

### 3. aggregated_data_moneypuck/skaters.csv
**Individual skater performance metrics**
- `playerId`, `season`, `name`, `team`, `position`, `situation`: Basic info
- `games_played`, `icetime`, `shifts`: Usage
- `gameScore`: Game score metric
- `onIce_xGoalsPercentage`, `offIce_xGoalsPercentage`: On/off ice expected goals
- `onIce_corsiPercentage`, `offIce_corsiPercentage`: On/off ice Corsi
- `onIce_fenwickPercentage`, `offIce_fenwickPercentage`: On/off ice Fenwick
- `iceTimeRank`: Ice time ranking
- **Individual metrics (I_F_ prefix)**: xOnGoal, xGoals, xRebounds, xFreeze, xPlayStopped, xPlayContinuedInZone, xPlayContinuedOutsideZone
- **Adjusted individual**: flurryAdjustedxGoals, scoreVenueAdjustedxGoals, flurryScoreVenueAdjustedxGoals
- **Points**: primaryAssists, secondaryAssists, points, goals
- **Shots**: shotsOnGoal, missedShots, blockedShotAttempts, shotAttempts
- **Other individual**: rebounds, reboundGoals, freeze, playStopped, playContinuedInZone, playContinuedOutsideZone
- **Saved shots**: savedShotsOnGoal, savedUnblockedShotAttempts
- `penalties`, `I_F_penalityMinutes`: Penalty stats
- **Faceoffs/physical**: faceOffsWon, hits, takeaways, giveaways
- **Danger zones**: lowDangerShots, mediumDangerShots, highDangerShots (plus xGoals and goals)
- **Score-adjusted**: scoreAdjustedShotsAttempts, unblockedShotAttempts, scoreAdjustedUnblockedShotAttempts
- **Zone**: dZoneGiveaways
- **Rebounds**: xGoalsFromxReboundsOfShots, xGoalsFromActualReboundsOfShots, reboundxGoals
- **Earned rebounds**: xGoals_with_earned_rebounds, xGoals_with_earned_rebounds_scoreAdjusted, xGoals_with_earned_rebounds_scoreFlurryAdjusted
- **Shifts**: shifts, oZoneShiftStarts, dZoneShiftStarts, neutralZoneShiftStarts, flyShiftStarts, oZoneShiftEnds, dZoneShiftEnds, neutralZoneShiftEnds, flyShiftEnds
- **Faceoffs**: faceoffsWon, faceoffsLost
- **Time/penalties**: timeOnBench, penalityMinutes, penalityMinutesDrawn, penaltiesDrawn
- `shotsBlockedByPlayer`: Shots blocked by this player
- **On-ice metrics (OnIce_F_, OnIce_A_ prefixes)**: All team metrics while player is on ice
- **Off-ice metrics (OffIce_F_, OffIce_A_ prefixes)**: Team metrics while player is off ice
- **After shifts**: xGoalsForAfterShifts, xGoalsAgainstAfterShifts, corsiForAfterShifts, corsiAgainstAfterShifts, fenwickForAfterShifts, fenwickAgainstAfterShifts

### 4. aggregated_data_moneypuck/teams.csv
**Team-level performance metrics**
- Similar structure to lines.csv but aggregated at team level
- All the same metrics (For/Against) without individual player components

### 5. enhanced/nhl_shots_20242025_20250528.csv
**Basic enhanced shot data**
- `game_id`: Unique game identifier
- `game_date`: Date of game
- `home_team`, `away_team`: Team abbreviations
- `event_idx`: Event index in game
- `period`: Period number
- `period_type`: Type of period (REG, OT, SO)
- `time_in_period`: Time elapsed in period (MM:SS)
- `time_remaining`: Time remaining in period
- `is_goal`: Binary goal indicator
- `shooter_id`, `shooter_name`: Shooter identification
- `shot_type`: Type of shot (Wrist, Slap, etc.)
- `x_coord`, `y_coord`: Shot coordinates
- `zone`: Zone where shot taken
- `goalie_id`, `goalie_name`: Goalie identification
- `home_score`, `away_score`: Current score
- `score_diff`: Score differential
- `shooting_team`: Team taking shot
- `situation`: Game situation
- `home_skaters`, `away_skaters`: Number of skaters
- `shot_distance`: Distance from net
- `shot_angle`: Angle to net
- `is_power_play`: Power play indicator
- `prev_event_type`: Previous event type
- `time_since_prev_event`: Time since last event
- `is_rebound`: Rebound indicator
- `is_rush`: Rush shot indicator
- `zone_time`: Time spent in offensive zone
- `season`: Season identifier
- `game_type`: Game type code
- `venue`: Venue name
- `event_type`: Type of event
- `is_shot_on_goal`: Shot on goal indicator
- `shooter_position`: Shooter's position
- `shooter_team`: Shooter's team
- `goalie_team`: Goalie's team
- `is_home_team`: Home team indicator

### 7. processed/fast_break_patterns.csv
**Fast break and counter-attack patterns**
- `miss_player`: Player who missed previous shot
- `miss_distance`: Distance of missed shot
- `goal_scorer`: Player who scored on fast break
- `time_to_goal`: Time between miss and goal
- `miss_x`, `miss_y`: Coordinates of missed shot
- `miss_danger_level`: Danger level of missed shot
- `miss_zone`: Zone of missed shot
- `rush_distance`: Distance covered on rush

### 8. processed/goal_sequences_fixed.csv
**Goal sequence analysis**
- `game_id`: Game identifier
- `goal_time`: Time of goal
- `shooter_id`: Goal scorer ID
- `assist1_id`, `assist2_id`: Assist player IDs
- `shots_before_goal`: Shots in sequence before goal
- `hits_before_goal`: Hits in sequence
- `giveaways_before_goal`: Giveaways in sequence
- `takeaways_before_goal`: Takeaways in sequence
- `sequence_duration`: Total sequence time
- `events_per_second`: Event rate
- `quick_strike`: Quick strike indicator
- `off_faceoff`: Goal off faceoff
- `offensive_zone_events`: Events in offensive zone
- `neutral_zone_events`: Events in neutral zone
- `is_rebound`: Rebound goal
- `sustained_pressure`: Sustained pressure indicator

### 9. processed/goalie_workload.csv
**Goalie workload and fatigue metrics**
- `game_id`: Game identifier
- `goal_id`: Goal identifier
- `goal_time`: Time of goal
- `goalie_id`: Goalie identifier
- `saves_last_10s`: Saves in last 10 seconds
- `saves_last_30s`: Saves in last 30 seconds
- `saves_last_60s`: Saves in last 60 seconds
- `shot_rate_2min`: Shot rate over 2 minutes
- `time_since_last_shot`: Time since last shot faced
- `total_shots_faced_game`: Total shots in game
- `fatigue_score`: Calculated fatigue score
- `high_intensity_saves`: High danger saves
- `rest_period`: Rest period indicator
- `sustained_pressure`: Under sustained pressure

### 10. processed/goalie_workload_all_shots.csv
**Comprehensive shot and goalie workload data**
- All basic shot data fields plus:
- `game_seconds`: Seconds elapsed in game
- `reason`: Reason for missed shot/save
- `blocker_id`: Player who blocked shot
- `shooting_team_id`: Shooting team ID
- `home_team_id`, `away_team_id`: Team IDs
- `score_differential`: Score difference
- `is_tied`, `is_leading`: Game state indicators
- `strength_state`: Strength state (5v5, 5v4, etc.)
- `empty_net`: Empty net indicator
- `is_penalty_shot`: Penalty shot indicator
- `prev_event_x`, `prev_event_y`: Previous event location
- `prev_event_team`: Team of previous event
- `distance_from_prev_event`: Distance from previous event
- `time_since_prev_shot`: Time since last shot
- `prev_shot_result`: Result of previous shot
- `shots_in_sequence`: Number of shots in sequence
- `time_since_faceoff`: Time since last faceoff
- `faceoff_win`: Faceoff won by shooting team
- `faceoff_zone`: Zone of last faceoff
- `is_off_zone_faceoff`: Off offensive zone faceoff
- `is_one_timer`: One-timer shot
- `speed_from_prev`: Speed from previous event
- `time_since_zone_entry`: Time since zone entry
- `offensive_zone_time`: Time in offensive zone
- `is_backhand`, `is_deflection`, `is_wraparound`: Shot type indicators
- `playoff_game`: Playoff game indicator
- `shots_faced_period`, `shots_faced_game`: Shot counts
- `consecutive_saves`: Consecutive saves made
- `save_pct_last_10`: Save percentage last 10 shots
- `danger_zone`: Danger zone classification
- `high_danger_save_pct`: High danger save percentage
- `goalie_cold_start`: Cold start indicator
- `goalie_quality_rating`: Goalie quality metric

### 11. processed/offensive_zone_times.csv
**Offensive zone time by shooter**
- `game_id`: Game identifier
- `shooter_id`: Shooter identifier
- `offensive_zone_time`: Time spent in offensive zone

### 12. processed/passing_sequences.csv
**Passing play analysis**
- `game_id`: Game identifier
- `goal_time`: Time of goal
- `shooter_id`: Goal scorer
- `total_passes`: Passes in sequence
- `sequence_duration`: Duration of passing sequence
- `avg_pass_distance`: Average pass distance
- `total_pass_distance`: Total pass distance
- `cross_ice_passes`: Number of cross-ice passes
- `forward_passes`: Number of forward passes
- `passes_per_second`: Pass rate
- `quick_strike`: Quick strike indicator
- `sustained_pressure`: Sustained pressure indicator

### 13. processed/player_shift_patterns.csv
**Player shift performance patterns**
- `player_id`: Player identifier
- `goals_for_on_ice`: Goals for while on ice
- `goals_against_on_ice`: Goals against while on ice
- `avg_shift_length_scoring`: Average shift length when scoring
- `avg_shift_length_scored_on`: Average shift length when scored on
- `avg_time_into_shift_scoring`: Time into shift when scoring
- `avg_time_into_shift_scored_on`: Time into shift when scored on
- `goal_differential_on_ice`: Goal differential
- `shift_length_differential`: Shift length differential
- `fatigue_factor_scoring`: Fatigue factor when scoring
- `fatigue_factor_scored_on`: Fatigue factor when scored on

### 14. processed/player_shot_patterns.csv
**Player shooting patterns**
- `player_name`: Player name
- `fast_breaks_caused`: Fast breaks created
- `fast_breaks_immediate`: Immediate fast break goals
- `rebounds_created`: Rebounds created
- `avg_rebound_time`: Average time to rebound

### 15. processed/player_tiers.csv
**Player classification and tiers**
- `player_id`: Player identifier
- `position`: Player position
- `position_group`: Position group (F/D/G)
- `height`, `weight`: Physical attributes
- `height_tier`: Height classification
- `shoots`: Shooting hand
- `games_played`: Games played
- `goals`, `assists`, `points`: Scoring stats
- `points_per_game`: Points per game
- `plus_minus`: Plus/minus rating
- `plus_minus_tier`: Plus/minus classification
- `shooting_pct`: Shooting percentage
- `save_pct`: Save percentage (goalies)
- `elite_scorer`: Elite scorer indicator
- `elite_goalie`: Elite goalie indicator
- `size_advantage`: Size advantage indicator

### 16. processed/rebound_patterns.csv
**Rebound shot patterns**
- `creator`: Player who created rebound
- `scorer`: Player who scored on rebound
- `time_to_rebound`: Time between shots
- `original_distance`: Distance of original shot
- `rebound_distance`: Distance of rebound shot
- `same_shooter`: Same shooter indicator
- `original_goalie`: Original goalie
- `rebound_goalie`: Goalie on rebound
- `goalie_changed`: Goalie change indicator

### 17. processed/training_assists_simplified.csv
**Simplified training data with assists**
- Core shot data plus:
- `shooter_name_verified`, `shooter_position`: Verified shooter info
- `assist1_name_verified`, `assist1_position`: First assist info
- `assist2_name_verified`, `assist2_position`: Second assist info
- `goalie_name_verified`: Verified goalie name
- `passing_combo`: Passing combination type
- `shot_handedness_match`: Handedness match indicator
- `shooter_height_advantage`: Height advantage
- `quick_strike`, `is_rebound`, `sustained_pressure`: Play type indicators
- `off_faceoff`: Off faceoff indicator
- `shots_before_goal`: Shots before goal
- `sequence_duration`: Sequence duration
- `offensive_zone_time`: Time in offensive zone
- `is_powerplay`, `is_shorthanded`: Special teams
- `empty_net`: Empty net indicator

### 18. processed/training_data_enhanced.csv
**Enhanced training data with all features**
- Comprehensive dataset combining multiple sources
- All shot data fields
- All sequence data fields
- All workload fields
- `royal_road_pass`: Cross-slot pass indicator
- `pass_angle_change`: Pass angle change
- `goals_last_1min`, `shots_last_1min`: Recent activity (1 min)
- `goals_last_5min`, `shots_last_5min`: Recent activity (5 min)
- `goals_last_10min`, `shots_last_10min`: Recent activity (10 min)
- `shot_momentum_ratio`: Momentum metric
- `rush_quality_score`: Rush quality metric
- `quick_zone_to_shot`: Quick zone entry to shot
- `in_slot`, `in_crease`, `from_point`: Location indicators
- `location_danger_score`: Location danger metric
- `low_pressure_shot`, `high_pressure_shot`: Pressure indicators

### 19. processed/training_data_model_ready.csv
**Model-ready training data**
- Cleaned and feature-selected data for model training
- Key features only, optimized for xG model

### 20. processed/training_data_with_assists.csv
**Training data with assist information**
- Complete shot data with verified assist information
- Player attributes (height, weight, shoots/catches)
- `passing_combo`: Type of passing play
- `shot_handedness_match`: Shooter/goalie handedness match
- `shooter_height_advantage`: Height advantage metric

### 21. raw/nhl_shots_2024-10-01_to_2025-04-15.csv
**Raw shot data from NHL API**
- Base shot data as extracted from NHL API
- Foundation for all processed datasets

### 22. shifts/goals_with_on_ice_fixed.csv
**Goals with on-ice players**
- `game_id`: Game identifier
- `goal_time`: Time of goal
- `shooter_id`: Goal scorer
- `offensive_on_ice`: Offensive players on ice (list)
- `defensive_on_ice`: Defensive players on ice (list)

### 23. shifts/shots_with_on_ice.csv
**Shots with on-ice players**
- `game_id`: Game identifier
- `shot_time`: Time of shot
- `shooter_id`: Shooter identifier
- `is_goal`: Goal indicator
- `offensive_on_ice`: Offensive players on ice
- `defensive_on_ice`: Defensive players on ice

## JSON Files Structure

### 1. play_by_play/*.json
**Game play-by-play data**
Top-level keys:
- `id`, `season`, `gameType`, `gameDate`, `venue`, `venueLocation`
- `startTimeUTC`, `easternUTCOffset`, `venueUTCOffset`
- `tvBroadcasts`, `gameState`, `gameScheduleState`
- `periodDescriptor`, `awayTeam`, `homeTeam`
- `shootoutInUse`, `otInUse`, `clock`, `displayPeriod`
- `maxPeriods`, `gameOutcome`, `plays`, `rosterSpots`
- `regPeriods`, `summary`

Play structure:
- `eventId`, `periodDescriptor`, `timeInPeriod`, `timeRemaining`
- `situationCode`, `homeTeamDefendingSide`, `typeCode`, `typeDescKey`
- `sortOrder`, `details`

Play detail keys by type:
- **blocked-shot**: blockingPlayerId, eventOwnerTeamId, reason, shootingPlayerId, xCoord, yCoord, zoneCode
- **faceoff**: eventOwnerTeamId, losingPlayerId, winningPlayerId, xCoord, yCoord, zoneCode
- **giveaway**: eventOwnerTeamId, playerId, xCoord, yCoord, zoneCode
- **goal**: assist1PlayerId, assist2PlayerId, awayScore, homeScore, scoringPlayerId, shotType, xCoord, yCoord, zoneCode, goalieInNetId
- **hit**: eventOwnerTeamId, hitteePlayerId, hittingPlayerId, xCoord, yCoord, zoneCode
- **missed-shot**: eventOwnerTeamId, goalieInNetId, reason, shootingPlayerId, shotType, xCoord, yCoord, zoneCode
- **penalty**: committedByPlayerId, descKey, drawnByPlayerId, duration, eventOwnerTeamId, typeCode, xCoord, yCoord, zoneCode
- **shot-on-goal**: awaySOG, eventOwnerTeamId, goalieInNetId, homeSOG, shootingPlayerId, shotType, xCoord, yCoord, zoneCode
- **takeaway**: eventOwnerTeamId, playerId, xCoord, yCoord, zoneCode

### 2. shifts/*.json
**Player shift data**
Top-level keys:
- `data`: Array of shift records
- `total`: Total number of shifts

Shift record structure:
- `id`, `detailCode`, `duration`, `endTime`
- `eventDescription`, `eventDetails`, `eventNumber`
- `firstName`, `gameId`, `hexValue`, `lastName`
- `period`, `playerId`, `shiftNumber`
- `startTime`, `teamAbbrev`, `teamId`, `teamName`, `typeCode`

### 3. endpoint_samples/*.json
**NHL API endpoint response samples**

Key structures:
- **club-stats.json**: season, gameType, skaters[], goalies[]
- **gamecenter_*.json**: Full game data with plays, rosters, stats
- **player_*.json**: Player stats, game logs, career data
- **roster_current.json**: forwards[], defensemen[], goalies[]
- **score_*.json**: Game scores and schedules
- **standings.json**: Team standings with extensive metrics

### 4. nhl_api_samples/*.json
**Additional NHL API samples**
Similar structure to endpoint_samples with various API responses

## Key Relationships

1. **Player IDs** link across all datasets:
   - `playerId`, `shooter_id`, `goalie_id`, `assist1_id`, `assist2_id`

2. **Game IDs** connect events:
   - Format: YYYYTTNNNN (Year, Type, Number)

3. **Time references**:
   - `time_in_period`: "MM:SS" format
   - `game_seconds`: Total seconds elapsed
   - Various `time_since_*` fields for sequencing

4. **Location data**:
   - `x_coord`, `y_coord`: Rink coordinates
   - `zone_code`: O(ffensive), N(eutral), D(efensive)
   - `shot_distance`, `shot_angle`: Calculated from coordinates

5. **Situation codes**:
   - Format: "HHAAP" (Home skaters, Away skaters, Period)
   - Used to determine strength states

6. **Event sequencing**:
   - `event_idx`, `eventId`, `sortOrder` for ordering
   - `prev_event_*` fields for context