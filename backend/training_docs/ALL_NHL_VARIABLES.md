ALL VARIABLES IN NHL DATA DIRECTORY

The strength states need to be decoded:

1551 = 5v5 (5 skaters + goalie = 6 on each side)
1451 = 5v4 (powerplay)
1541 = 4v5 (penalty kill)
1661 = 6v5 (empty net)

=== ENHANCED SHOT DATA ===
data/nhl/enhanced/nhl_shots_20242025_20250528.csv (32 columns):
game_id, season, game_date, game_type, period, period_type, time_in_period, time_remaining, home_team, away_team, shooting_team, shooter_id, goalie_id, shot_type, x_coord, y_coord, event_idx, is_goal, situation, empty_net, home_score, away_score, score_diff, home_skaters, away_skaters, shot_distance, shot_angle, prev_event_type, time_since_prev_event, is_power_play, is_rebound, zone_time

data/nhl/enhanced/nhl_shots_with_names_20242025_20250528_021154.csv (42 columns):
game_id, season, game_date, game_type, period, period_type, time_in_period, time_remaining, home_team, away_team, shooting_team, shooter_id, shooter_name, shooter_position, shooter_team, goalie_id, goalie_name, goalie_team, shot_type, x_coord, y_coord, event_idx, event_type, is_goal, is_shot_on_goal, situation, empty_net, home_score, away_score, score_diff, home_skaters, away_skaters, shot_distance, shot_angle, prev_event_type, time_since_prev_event, is_power_play, is_rebound, zone_time, is_home_team, venue, zone

=== RAW SHOT DATA ===
data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv (74 columns):
game_id, game_date, period, period_type, time_in_period, time_remaining, situationCode, homeTeamDefendingSide, typeCode, typeDescKey, sortOrder, player1_id, player1_name, player1_teamAbbrev, player1_position, player1_type, player2_id, player2_name, player2_teamAbbrev, player2_position, player2_type, player3_id, player3_name, player3_teamAbbrev, player3_position, player3_type, xCoord, yCoord, zoneCode, shotType, event_type, shooting_team, shooter_id, shooter_name, goalie_id, goalie_name, is_goal, home_team, away_team, home_score, away_score, score_diff, home_skaters, away_skaters, away_goalie_pulled, home_goalie_pulled, strength_state, shot_distance, shot_angle, is_home_shooter, time_since_last_event, last_event_type, last_event_team, is_rebound, rush_shot, zone_time_start, zone_time_end, is_penalty_shot, following_event_type, following_event_time, resulted_in_icing, faceoff_win_team, prior_zone_time, cumulative_home_shots, cumulative_away_shots, period_seconds_elapsed, game_seconds_elapsed, shots_in_last_2_min, goals_in_last_5_min, is_power_play, is_short_handed, empty_net, shooter_position, goalie_team

=== PROCESSED TRAINING DATA ===
data/nhl/processed/training_data_enhanced.csv (134 columns):
[Contains all base shot data plus:]
offensive_zone_time, time_since_zone_entry, speed_from_prev, prev_event_x, prev_event_y, shots_in_sequence, time_since_last_shot, prev_shot_saved, prev_shot_missed, prev_shot_blocked, is_one_timer, is_tip_in, is_wraparound, is_deflection, is_backhand, from_behind_net, cross_slot_pass, down_low_pass, point_shot, high_slot, low_slot, right_circle, left_circle, right_point, left_point, below_goal_line, one_timer_setup, quick_release, off_the_rush, cycle_play, second_chance, broken_play, screened_shot, royal_road_pass, east_west_pass, pass_distance, pass_angle, passes_in_sequence, puck_recovery, forecheck_turnover, odd_man_rush, outnumbered_rush, controlled_entry, dump_and_chase, carry_in_entry, passing_play_entry, neutral_zone_turnover, shot_from_slot, shot_distance_from_net, shooting_angle_adjusted, danger_zone_shot, high_danger_shot, medium_danger_shot, low_danger_shot, expected_goal_value, shot_quality_index, pre_shot_movement, lateral_movement, vertical_movement, total_movement, movement_speed, goalie_angle, goalie_distance, shooter_handedness, goalie_handedness, same_handedness, shot_velocity_estimate, release_time, deception_factor, shooting_space, defender_distance, shooting_lane_open, traffic_in_front, net_front_presence, goalie_screened, shooter_speed, angle_change_rate, momentum_shift, puck_possession_time, offensive_pressure, defensive_breakdown, transition_play, sustained_attack, power_play_setup, penalty_kill_clear, four_on_four, three_on_three, overtime_play, pulled_goalie_situation, delayed_penalty, extra_attacker, two_man_advantage, five_on_three, major_penalty, home_crowd_factor, momentum_factor, clutch_situation, must_score_situation, game_situation_critical, elimination_game, playoff_intensity, rivalry_game, divisional_matchup, measuring_stick_game, statement_game, revenge_game, season_series, head_to_head_history, venue_advantage, altitude_factor, travel_fatigue, back_to_back, three_in_four, schedule_difficulty, injury_impact, lineup_changes, coaching_matchup, special_teams_matchup, style_matchup, pace_of_play, physicality_index, skill_differential, experience_differential, motivation_index, desperation_level, confidence_level, team_chemistry, player_hot_streak, goalie_hot_streak, team_momentum

data/nhl/processed/training_data_model_ready.csv (37 columns):
game_id, season, game_date, game_type, period, period_type, time_in_period, time_remaining, home_team, away_team, shooting_team, shooter_id, goalie_id, shot_type, x_coord, y_coord, event_idx, is_goal, situation, empty_net, home_score, away_score, score_diff, home_skaters, away_skaters, shot_distance, shot_angle, prev_event_type, time_since_prev_event, is_power_play, is_rebound, zone_time, shooter_name, goalie_name, is_home_team, venue, zone

=== SHIFT-BASED DATA ===
data/nhl/shifts/goals_with_on_ice_fixed.csv (5 columns):
game_id, event_idx, home_on_ice, away_on_ice, goal_scorer_id

data/nhl/shifts/shots_with_on_ice.csv (6 columns):
game_id, event_idx, shooting_team, home_on_ice, away_on_ice, shooter_id

=== SPECIALIZED PROCESSED DATA ===
data/nhl/processed/player_shot_patterns.csv (23 columns):
shooter_id, shooter_name, total_shots, total_goals, shooting_pct, avg_shot_distance, avg_shot_angle, preferred_shot_type, high_danger_shots, medium_danger_shots, low_danger_shots, high_danger_goals, medium_danger_goals, low_danger_goals, high_danger_sh_pct, pp_shots, pp_goals, pp_shooting_pct, even_strength_shots, even_strength_goals, even_strength_sh_pct, shots_per_game, goals_per_game

data/nhl/processed/goalie_workload.csv (23 columns):
game_id, game_date, period, time_in_period, goalie_id, goalie_name, shot_number, cumulative_shots, shots_last_1min, shots_last_5min, shots_last_10min, high_danger_last_5min, time_since_last_shot, avg_shot_distance_last_5, avg_shot_angle_last_5, lateral_movement_last_5, save_pct_last_10_shots, goals_against_last_10min, fatigue_score, workload_intensity, rapid_shot_sequence, sustained_pressure, period_workload, game_workload

data/nhl/processed/goalie_workload_all_shots.csv (27 columns):
[Same as above plus:] is_goal, shot_type, shot_distance, shot_angle

data/nhl/processed/offensive_zone_times.csv (12 columns):
game_id, team, period, start_time, end_time, duration, shots_during, goals_during, zone_exit_type, next_entry_time, sustained_pressure, pressure_score

data/nhl/processed/goal_sequences_fixed.csv (20 columns):
game_id, goal_event_idx, scoring_team, goal_scorer_id, goal_scorer_name, assist1_id, assist1_name, assist2_id, assist2_name, time_to_goal, sequence_length, sequence_events, shots_in_sequence, passes_in_sequence, hits_in_sequence, zone_time_before_goal, last_faceoff_team, last_faceoff_zone, rush_goal, sustained_pressure_goal

data/nhl/processed/rebound_patterns.csv (17 columns):
game_id, initial_shot_idx, rebound_shot_idx, initial_shooter_id, rebound_shooter_id, time_between_shots, initial_shot_saved, rebound_is_goal, same_shooter, initial_shot_type, rebound_shot_type, initial_distance, rebound_distance, initial_angle, rebound_angle, angle_change, location_change

data/nhl/processed/passing_sequences.csv (14 columns):
game_id, sequence_id, sequence_start, sequence_end, duration, team, num_passes, num_players, ended_in_shot, ended_in_goal, zone_changes, royal_road_passes, high_danger_passes, sequence_danger_score

data/nhl/processed/player_shift_patterns.csv (24 columns):
game_id, player_id, player_name, team, shift_number, period, shift_start, shift_end, shift_length, position, shots_for, shots_against, goals_for, goals_against, hits, blocked_shots, giveaways, takeaways, faceoffs_won, faceoffs_lost, zone_starts_o, zone_starts_d, zone_starts_n, ice_quality

data/nhl/processed/player_tiers.csv (20 columns):
player_id, player_name, position, tier, games_played, toi_per_game, points_per_60, shots_per_60, goals_per_60, assists_per_60, primary_assists_per_60, xGF_per_60, xGA_per_60, CF_per_60, CA_per_60, relative_CF_pct, zone_start_pct, PDO, offensive_impact, defensive_impact

data/nhl/processed/fast_break_patterns.csv (17 columns):
game_id, event_idx, team, zone_entry_time, first_shot_time, time_to_shot, rush_type, num_attackers, num_defenders, odd_man_rush, shot_type, shot_location, is_goal, passes_on_rush, speed_score, control_score, danger_score

data/nhl/processed/training_assists_simplified.csv (15 columns):
game_id, goal_idx, period, time_in_period, scoring_team, goal_scorer_id, assist1_id, assist2_id, shot_type, shot_distance, shot_angle, score_state, strength_state, is_empty_net, sequence_pattern

data/nhl/processed/training_data_with_assists.csv (52 columns):
[Base shot data plus:] assist1_id, assist1_name, assist2_id, assist2_name, goals_last_1min, shots_last_1min, goals_last_5min, shots_last_5min, goals_last_10min, shots_last_10min, shot_momentum_ratio, is_rush, offensive_zone_time, sustained_pressure, low_pressure_shot, high_pressure_shot, location_danger_score, in_slot, in_crease, from_point

=== AGGREGATED MONEYPUCK DATA ===
data/nhl/aggregated_data_moneypuck/teams.csv (102 columns):
[Team-level metrics for different game situations including:]
GP, TOI, GF, GA, SF, SA, FF, FA, CF, CA, xGF, xGA, SCF, SCA, HDCF, HDCA, HDGF, HDGA, MDCF, MDCA, MDGF, MDGA, LDCF, LDCA, LDGF, LDGA, SH%, SV%, PDO, [repeated for all situations, 5on5, 5on4, 4on5, other, all]

data/nhl/aggregated_data_moneypuck/skaters.csv (145 columns):
[Individual player metrics including:]
playerId, name, position, team, GP, TOI, G, A1, A2, Points, IPP, SOG, iSF, iFF, iCF, ixG, SH%, OnIce_GF, OnIce_GA, OnIce_SF, OnIce_SA, OnIce_xGF, OnIce_xGA, Off_F_goals, Off_A_goals, penalties, minor, major, misconduct, penaltiesDrawn, penaltyShots, [plus zone starts, quality metrics, etc.]

data/nhl/aggregated_data_moneypuck/goalies.csv (32 columns):
playerId, name, team, GP, TOI, SA, GA, SV%, xGA, GSAx, HDSA, HDGA, HDSV%, HDGSAx, MDSA, MDGA, MDSV%, MDGSAx, LDSA, LDGA, LDSV%, LDGSAx, SoTA, RBS, RBSaves, RBSV%, RBGA, Breakaways, BreakawayShots, BreakawayGoals, BreakawayxG, CrapshotShots, CrapshotGoals, CrapshotxG

data/nhl/aggregated_data_moneypuck/lines.csv (102 columns):
[Line combination metrics, similar structure to teams.csv but for specific forward line combinations]

=== UPDATED PROCESSED DATA VARIABLES ===

data/nhl/processed/fast_break_patterns.csv (ADDITIONAL):
miss_player, miss_distance, goal_scorer, time_to_goal, miss_x, miss_y, miss_danger_level, miss_zone, rush_distance

data/nhl/processed/goal_sequences_fixed.csv (COMPLETE):
game_id, goal_time, shooter_id, assist1_id, assist2_id, shots_before_goal, hits_before_goal, giveaways_before_goal, takeaways_before_goal, sequence_duration, events_per_second, quick_strike, off_faceoff, offensive_zone_events, neutral_zone_events, is_rebound, sustained_pressure

data/nhl/processed/goalie_workload_all_shots.csv (COMPLETE 88 columns):
game_id, season, game_type, game_date, venue, period, period_type, time_in_period, time_remaining, game_seconds, event_type, x_coord, y_coord, zone_code, shot_type, is_goal, reason, shot_distance, shot_angle, shooter_id, shooter_name, goalie_id, goalie_name, assist1_id, assist1_name, assist2_id, assist2_name, blocker_id, shooting_team_id, shooting_team, home_team_id, home_team, away_team_id, away_team, is_home_team, home_score, away_score, score_differential, is_tied, is_leading, home_skaters, away_skaters, strength_state, is_powerplay, is_shorthanded, empty_net, is_penalty_shot, prev_event_type, prev_event_x, prev_event_y, prev_event_team, time_since_prev_event, distance_from_prev_event, time_since_prev_shot, prev_shot_result, shots_in_sequence, time_since_faceoff, faceoff_win, faceoff_zone, is_off_zone_faceoff, is_rebound, is_rush, is_one_timer, speed_from_prev, time_since_zone_entry, offensive_zone_time, is_backhand, is_deflection, is_wraparound, playoff_game, saves_last_10s, saves_last_30s, saves_last_60s, shots_faced_period, shots_faced_game, shot_rate_2min, time_since_last_shot, consecutive_saves, save_pct_last_10, danger_zone, high_danger_save_pct, goalie_cold_start, fatigue_score, high_intensity_saves, rest_period, sustained_pressure, goalie_quality_rating

data/nhl/processed/goalie_workload.csv (ADDITIONAL):
saves_last_10s, saves_last_30s, saves_last_60s, shots_faced_period, shots_faced_game, shot_rate_2min, time_since_last_shot, consecutive_saves, save_pct_last_10, danger_zone, high_danger_save_pct, goalie_cold_start, fatigue_score, high_intensity_saves, rest_period, sustained_pressure

data/nhl/processed/offensive_zone_times.csv (SIMPLIFIED):
game_id, shooter_id, offensive_zone_time

data/nhl/processed/passing_sequences.csv (UPDATED):
game_id, goal_time, shooter_id, total_passes, sequence_duration, avg_pass_distance, total_pass_distance, cross_ice_passes, forward_passes, passes_per_second, quick_strike, sustained_pressure

data/nhl/processed/player_shift_patterns.csv (ADDITIONAL):
player_id, goals_for_on_ice, goals_against_on_ice, avg_shift_length_scoring, avg_shift_length_scored_on, avg_time_into_shift_scoring, avg_time_into_shift_scored_on, goal_differential_on_ice, shift_length_differential, fatigue_factor_scoring, fatigue_factor_scored_on

data/nhl/processed/player_shot_patterns.csv (ADDITIONAL):
player_name, fast_breaks_caused, fast_breaks_immediate, rebounds_created, avg_rebound_time

data/nhl/processed/player_tiers.csv (UPDATED):
player_id, position, position_group, height, weight, height_tier, shoots, games_played, goals, assists, points, points_per_game, plus_minus, plus_minus_tier, shooting_pct, save_pct, elite_scorer, elite_goalie, size_advantage

data/nhl/processed/rebound_patterns.csv (ADDITIONAL):
creator, scorer, time_to_rebound, original_distance, rebound_distance, same_shooter, original_goalie, rebound_goalie, goalie_changed

data/nhl/processed/training_data_with_assists.csv (COMPLETE 98 columns):
[All base columns plus:] shooter_name_verified, shooter_position, shooter_shoots, shooter_height, shooter_weight, assist1_name_verified, assist1_position, assist1_shoots, assist2_name_verified, assist2_position, assist2_shoots, goalie_name_verified, goalie_catches, goalie_height, goalie_weight, passing_combo, shot_handedness_match, shooter_height_advantage

data/nhl/processed/training_assists_simplified.csv (31 columns):
game_id, shooter_id, shooter_name_verified, shooter_position, assist1_id, assist1_name_verified, assist1_position, assist2_id, assist2_name_verified, assist2_position, goalie_id, goalie_name_verified, shot_distance, shot_angle, shot_type, passing_combo, shot_handedness_match, shooter_height_advantage, quick_strike, is_rebound, sustained_pressure, off_faceoff, shots_before_goal, sequence_duration, offensive_zone_time, is_powerplay, is_shorthanded, empty_net, home_score, away_score, period, time_in_period

data/nhl/processed/training_data_enhanced.csv (ADDITIONAL KEY FEATURES):
royal_road_pass, pass_angle_change, goals_last_1min, goals_last_5min, shots_last_5min, shot_momentum_ratio, rush_quality_score, quick_zone_to_shot, in_slot, in_crease, from_point, location_danger_score, low_pressure_shot, high_pressure_shot

=== PLAYER DATA (JSON) ===
data/nhl/players/*.json (e.g., 8471675.json for Sidney Crosby):
playerId, firstName, lastName, heightInInches, weightInPounds, position, shootsCatches, birthDate, birthCity, birthCountry, currentTeamId, draftYear, draftRound, draftOverall, careerTotals.regularSeason.gamesPlayed, careerTotals.regularSeason.goals, careerTotals.regularSeason.assists, careerTotals.regularSeason.points, careerTotals.regularSeason.plusMinus, careerTotals.regularSeason.shootingPctg

=== SEASON STATS ===
data/nhl/season_stats/all_players_202425.json:
Complete player roster with current season stats

data/nhl/season_stats/goalies_202425.json:
Goalie-specific stats for current season

data/nhl/season_stats/skaters_202425.json:
Skater-specific stats for current season

data/nhl/season_stats/goalie_lookup.json:
Goalie ID to name mapping

data/nhl/season_stats/skater_lookup.json:
Skater ID to name mapping

=== ON-ICE QUALITY METRICS ===
From shifts/goals_with_on_ice_fixed.csv:
- offensive_quality_sum: Sum of +/- of offensive players on ice
- defensive_quality_sum: Sum of +/- of defensive players on ice
- elite_shooters_on_ice: Count of elite offensive players
- weak_defenders_on_ice: Count of poor +/- defenders
- avg_defender_height: Average height of defenders on ice
- fresh_players: Count of players <20s into shift
- quality_differential: (offensive_quality - defensive_quality)
- mismatch_indicators: Elite shooters vs weak defenders
- fatigue_factors: How long each player has been on ice

=== FATIGUE-RELATED VARIABLES ===
From goalie_workload files:
- shots_faced_last_1min, shots_faced_last_5min, shots_faced_last_10min
- cumulative_shots_faced, high_danger_shots_last_5min
- save_percentage_last_10min, rebounds_allowed_last_5min
- lateral_movement_last_5min, rest_time_between_shots
- consecutive_shots_faced, workload_score, fatigue_indicator
- saves_last_10s, saves_last_30s, saves_last_60s
- shot_rate_2min, consecutive_saves, save_pct_last_10
- goalie_cold_start, high_intensity_saves, rest_period

From player_shift_patterns:
- shift_duration, time_since_last_shift, shifts_last_10min
- shifts_this_period, total_ice_time, ice_time_last_10min
- back_to_back_shifts, consecutive_d_zone_starts
- high_intensity_shifts, avg_shift_length_last_5
- avg_shift_length_scoring, avg_shift_length_scored_on
- avg_time_into_shift_scoring, fatigue_factor_scoring

From training data:
- offensive_zone_time, zone_time_before_shot
- defensive_zone_time_last_5min, total_ice_time_at_shot
- period_minutes_elapsed, back_to_back_games
- games_in_last_7_days, travel_miles_last_3_days

=== ADVANCED SEQUENCE METRICS ===
Time windows for faceoff analysis:
- 0-3 seconds: Direct play off draw
- 3-6 seconds: Quick strike play
- 6-10 seconds: Set play development
- 10+ seconds: Not faceoff-related

Fast break categories:
- Immediate (< 10s): True rush chances
- Quick (10-20s): Fast transitions
- Extended (20-30s): Sustained pressure breaks

Shot sequence patterns:
- Sustained pressure (3+ shots before goal)
- Quick strike (no prior shots)
- Scrambles (multiple shots in 10s)
- Second chances (after blocked/missed)

=== MONEYPUCK AGGREGATED FEATURES ===
Available for merging via player/team IDs:
- I_F_rebounds: Individual rebounds created
- I_F_giveaways: Individual giveaways
- faceoffsWon/Lost: Faceoff performance
- xGoals vs goals: Performance vs expectation
- OnIce metrics: Team performance when player on ice
- Zone start percentages
- Score/venue adjusted metrics
- Danger zone breakdowns (low/medium/high)