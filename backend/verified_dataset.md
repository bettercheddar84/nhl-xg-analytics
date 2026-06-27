# NHL AI Training Dataset

Input Layer Design:
- Core features: 30-35 dimensions
- Player embeddings: 64 dimensions per player
- Goalie embeddings: 32 dimensions
- Total input: ~150-200 features after encoding

1. Quantitative Analysis: Full neural network for accurate xG predictions
  2. Natural Language Understanding: Can process and explain hockey concepts
  3. Interactive Q&A: Ask questions and get explanations
  4. Interpretable: Explains WHY each prediction was made
  5. Hockey-Smart: Understands context like "rush chances" and "power plays"

  This model can:
  - Calculate xG values (quantitative)
  - Explain its predictions in plain English
  - Answer questions about specific shots
  - Provide statistical insights
  - Compare similar historical shots

calculate_royal_road_pass(df):
    """
    Detect cross-slot passes (royal road passes).
    These are passes that cross from one side of the ice to the other
    through the slot area, creating high-danger scoring chances.
    """

Pass crossed center ice (prev_event_x and x_coord have opposite signs)
Pass went through slot area (prev_event_y within 20 feet of center)

NHL SHOT DATA FEATURE DOCUMENTATION
==================================================

Key Features Added:
- shot_zone: Where shot was actually taken (offensive/neutral/defensive)
- play_type_zone: Original zone_code - type of play (O/N/D)
- royal_road_pass: Cross-slot pass in offensive zone
- is_transition_play: Rush from defensive/neutral zone
- is_sustained_pressure: Long offensive zone possession
- is_broken_play: Offensive play but defensive shot
- is_quick_strike: Quick offensive zone shot
- danger_level: high/medium/low based on location
- Various zone flags: in_slot, in_high_slot, behind_net, from_point

1551 = 5v5 (5 skaters + goalie = 6 on each side)
1451 = 5v4 (powerplay)
1541 = 4v5 (penalty kill)
1661 = 6v5 (empty net)

# NHL rink coordinates:
# x-axis: -100 (your goal) to +100 (opponent's goal)
# Blue lines are at approximately -25 and +25

# So zones should be:
# x < -25: Defensive zone ('D')
# -25 <= x <= 25: Neutral zone ('N')  
# x > 25: Offensive zone ('O')

If a shot goes directly to the goalie → no assist
If a shot is deflected by any player (including defensive team) → last offensive player to touch gets assist
If goalie saves but gives up rebound that scores → original shooter gets assist

## data\nhl\player_id-first_last_name.csv

please use this file for 

{
  "manifest": {
    "file_info": {
      "filename": "player_id-first_last_name.csv",
      "path": "data/nhl/player_id-first_last_name.csv",
      "format": "CSV",
      "encoding": "UTF-8",
      "delimiter": ",",
      "has_header": true,
      "created_date": "2024-12-19",
      "last_updated": "2024-12-19",
      "update_frequency": "As needed - when new players enter NHL"
    },
    
    "data_source": {
      "primary_source": "NHL API",
      "api_endpoints": [
        "https://api-web.nhle.com/v1/player/{player_id}/landing",
        "https://api.nhle.com/stats/rest/en/skater"
      ],
      "extraction_method": "API calls with player IDs",
      "extraction_date": "2024-12-19",
      "season_coverage": "2024-2025 NHL season active players"
    },
    
    "schema": {
      "columns": [
        {
          "name": "player_id",
          "type": "string",
          "format": "numeric_string",
          "description": "Unique NHL player identifier",
          "nullable": false,
          "unique": true,
          "example": "8475311",
          "length": 7,
          "pattern": "^8[0-9]{6}$"
        },
        {
          "name": "first_name",
          "type": "string",
          "description": "Player's first name in English",
          "nullable": false,
          "unique": false,
          "example": "Connor",
          "special_values": ["Unknown", "Not Found", "Error"],
          "notes": "May include special characters (é, ö, etc.) and apostrophes"
        },
        {
          "name": "last_name",
          "type": "string",
          "description": "Player's last name in English",
          "nullable": false,
          "unique": false,
          "example": "McDavid",
          "special_values": ["Unknown", "Not Found", "Error"],
          "notes": "May include special characters, hyphens, apostrophes, and spaces"
        }
      ]
    },
    
    "data_statistics": {
      "total_records": 1016,
      "unique_players": 1016,
      "goalies_included": false,
      "data_quality": {
        "complete_records": "~95%",
        "missing_names": "~5%",
        "duplicate_ids": 0
      }
    },
    
    "usage": {
      "purpose": "Map NHL player IDs to human-readable names for Pittsburgh Penguins AI Analytics Platform",
      "applications": [
        "Neural network feature engineering",
        "Player identification in shot data",
        "UI display of player names",
        "Data joining operations"
      ],
      "related_files": [
        "goalie_ids.txt",
        "shots_data_2024-25.csv"
      ]
    },
    
    "processing_notes": {
      "cleaning_applied": [
        "Extracted English names from multi-language dictionaries",
        "Preserved special characters in names",
        "Standardized format to CSV"
      ],
      "known_issues": [
        "Some players may have 'Not Found' or 'Unknown' values",
        "Special characters may require UTF-8 encoding for proper display",
        "Names are as provided by NHL API - may differ from common usage"
      ],
      "validation_rules": [
        "All player_ids must be 7 digits starting with 8",
        "No null values allowed in any column",
        "Each player_id must be unique"
      ]
    },
    
    "maintenance": {
      "update_process": "Run player name fetching script when new players added",
      "validation_script": "validate_player_names.py",
      "backup_policy": "Keep previous versions when updating",
      "contact": "Pittsburgh Penguins AI Analytics Team"
    }
  }
}

# **Data Folder penguins_ai/nhl**

## 1. **Money Puck Data** (`data\nhl\aggregated_data_moneypuck`)

- Use to compare to our model dataset as an aggregate

data\aggregated_data_moneypuck\aggregate-data.md
data\aggregated_data_moneypuck\goalies.csv
data\aggregated_data_moneypuck\lines.csv
data\aggregated_data_moneypuck\skaters.csv
data\aggregated_data_moneypuck\teams.csv

## 2. **NHL Historical Data** (`data\nhl\nhl_data`)

- NHL Historical data to use to weigh on the model 

(../renewedAnalytics-for-NHL/data/nhl_data/club-stats.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/draft_rankings.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/game_boxscore.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/game_landing.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/game_playbyplay.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/gamecenter_boxscore.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/gamecenter_landing.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/gamecenter_play-by-play.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/gamecenter_right-rail.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/player_game-log.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/player_gamelog.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/player_landing.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/roster_current.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/schedule_calendar.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/score_date.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/score_now.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/scoreboard.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/standings_season.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/standings.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/team_prospects.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/team_roster.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/team_schedule.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/team_stats.json) 
(../renewedAnalytics-for-NHL/data/nhl_data/wsc_game-story.json)

## . **Players Data-Egde** (`data\nhl\players_edge`)

Dataset Overview
- **Total Players**: 913
- **Total Columns**: 42
- **Date Range**: 2025-06-01T00:31:08.915553 to 2025-06-01T01:09:12.154260

1. Player Information (12 columns)
- player_id: Unique player identifier
- timestamp: Data collection timestamp  
- first_name, last_name: Player name
- position: C, LW, RW, D
- team: Team abbreviation
- jersey_number: Player number
- shoots: L/R shooting hand
- games_played: Games in current season
- goals, assists, points: Scoring statistics

2. Skating Metrics (12 columns)
- skating_top_speed_mph: Maximum skating speed achieved
- skating_[18-20/20-22/22plus]_mph_bursts: Count of high-speed bursts
- Each metric includes: value, league_avg, percentile

3. Shot Metrics (24 columns)
- shot_top_speed_mph: Maximum shot velocity
- shot_average_speed_mph: Average shot velocity
- shot_[70-80/80-90/90-100/100plus]_mph_shots: Shot counts by speed range
- Each metric includes: value, league_avg, percentile



## . **Player NHL History Data Career in hockey** (`data\nhl\players`)

This directory contains 
Directory: data/nhl/players
Total files: 1016
JSON files: 1016

NHL Player Data Structure Overview

This JSON file is a comprehensive player profile containing:
1. Core Player Attributes

Basic Info: Name, ID, position (L=Left Wing), jersey #72, team (San Jose Sharks)
Physical Stats: Height (71 inches), weight (181 lbs), shoots left-handed
Career Info: Drafted 2021 (1st round, 7th overall), birthdate (Oct 12, 2002)

2. Performance Statistics

Current Season (2024-25): 77 games, 17 goals, 41 assists, 58 points
Career Totals: 174 NHL games, 35 goals, 75 assists, 110 points
Advanced Metrics: Shooting percentage (11.26%), plus/minus (-7), power play points (16)

3. Game-by-Game Data

Last 5 Games: Detailed stats for each recent game including:

Time on ice (TOI)
Shots, goals, assists
Plus/minus rating
Penalty minutes

4. Career History

Full Season History: From youth leagues (U13) through NHL
Different Leagues: SHL (Swedish Hockey League), AHL, NHL
Development Path: Shows progression through Djurgårdens IF system

5. Additional Context

Team Roster: Current San Jose Sharks teammates
Awards: E.J. McGuire Award of Excellence (2020-21)
URLs: Headshot, hero image, team logo links

Value for LLM Training
This structured data is perfect for training LLMs to:

Understand hockey statistics and their relationships
Generate player summaries and scouting reports
Track player development patterns
Analyze performance trends
Compare players across different metrics

The data shows Eklund as a young, developing player (22 years old) who's establishing himself as a playmaker (more assists than goals) in the NHL after coming through the Swedish development system.

## . **Goalies Data-Edge**  (`data\nhl\goalie_data`)

data\goalie_data\dataset_summary.json
data\goalie_data\goalies_llm_descriptions.txt
data\goalie_data\goalies_llm_features.csv
data\goalie_data\goalies_llm_features.json

NHL Goalie Data Files Overview
1. dataset_summary.json
Purpose: High-level statistics about the entire goalie dataset
Contents:

Total number of goalies processed
Count of goalies with complete vs partial data
Performance distribution (elite, above average, average, below average)
Average statistics across all goalies
Data quality metrics

Use for LLM: Provides context about the dataset's composition and quality. Useful for understanding biases, data completeness, and overall distribution of goalie performance levels.
2. goalies_llm_descriptions.txt
Purpose: Natural language descriptions of each goalie for text-based training
Format: Human-readable text profiles
Example content:
Goalie Profile: Connor Hellebuyck (WPG)
Games Played: 63, Record: 47-12-3
Save Percentage: 0.925, GAA: 2.00
Performance Tier: Elite
High Danger Save %: 84.5% (Percentile: 94)
Workload: High (31.2 shots/game)
Role: Starter
Use for LLM: Perfect for fine-tuning language models to understand and generate hockey analytics text. Each profile provides structured information in natural language format.
3. goalies_llm_features.csv
Purpose: Tabular data with all numeric features for each goalie
Columns include:

Basic stats: goalie_id, full_name, team, games_played, wins, losses, save_pct, gaa
Advanced metrics: high_danger_save_pct, mid_range_save_pct, percentile rankings
Calculated features: shots_per_game, elite_save_ability, consistency_score
Binary indicators: is_starter, is_elite, performance tier one-hot encoding
Data quality flags: has_advanced_stats, data_completeness

Use for LLM: Structured data for training models on statistical relationships, performance prediction, and pattern recognition.
4. goalies_llm_features.json
Purpose: Same data as CSV but in JSON format for flexible processing
Structure: Array of goalie objects with nested feature dictionaries
Advantages:

Preserves data types better than CSV
Easier to parse programmatically
Supports nested structures if needed

## . **Shifts Around Goals Scored** (`data\nhl\shifts`)

Integration Guidelines

Data Pipeline:

Parse shift events into time-ordered sequences
Identify goal events and extract surrounding context
Calculate derived features (fatigue, line chemistry, etc.)
Format for neural network input


Feature Importance:

High: Current shift duration, player combinations, special teams
Medium: Recent shift history, rest time between shifts
Low: Color hex values, event descriptions


Model Architecture Considerations:

Use LSTM/GRU for sequential shift patterns
Attention mechanism for player interactions
Embeddings for player/team identities
Time-aware features for period/game state


Validation Strategy:

Hold out recent games for testing
Cross-validate across different team matchups
Ensure model generalizes beyond memorizing player names


File: shift_event_manifest.json
json{
  "data_description": {
    "name": "NHL Shift and Goal Event Data",
    "version": "1.0",
    "season": "2024-25",
    "total_shots": 312000,
    "purpose": "Neural network training for xG prediction based on shift patterns and goal events"
  },
  
  "event_types": {
    "517": {
      "code": 517,
      "name": "shift",
      "description": "Regular player shift on ice"
    },
    "505": {
      "code": 505,
      "name": "goal",
      "description": "Goal scored event",
      "detail_codes": {
        "802": "Power Play Goal (PPG)",
        "803": "Even Strength Goal (EVG)",
        "806": "Empty Net Goal (EN)"
      }
    }
  },
  
  "temporal_structure": {
    "periods": {
      "1": "First Period",
      "2": "Second Period",
      "3": "Third Period",
      "4": "Overtime",
      "5": "Shootout"
    },
    "time_format": "MM:SS",
    "duration_format": "MM:SS",
    "game_length": "60:00 (regulation)"
  },
  
  "player_attributes": {
    "playerId": "Unique identifier for player",
    "firstName": "Player's first name",
    "lastName": "Player's last name",
    "position": "Player position (extracted from other data)",
    "handedness": "L/R shooting hand (from roster data)"
  },
  
  "team_attributes": {
    "teamId": "Unique team identifier",
    "teamAbbrev": "3-letter team abbreviation",
    "teamName": "Full team name",
    "hexValue": "Team primary color"
  },
  
  "shift_attributes": {
    "shiftNumber": "Sequential shift number for player in game",
    "startTime": "When player entered ice",
    "endTime": "When player left ice",
    "duration": "Time on ice for shift"
  },
  
  "goal_context_window": {
    "description": "For each goal, capture events in surrounding time window",
    "pre_goal_window": "120 seconds before goal",
    "post_goal_window": "10 seconds after goal",
    "included_events": [
      "All player shifts active during window",
      "Line combinations on ice",
      "Special teams status (PP/PK/ES)",
      "Goalie presence (for EN goals)"
    ]
  },
  
  "feature_engineering_hints": {
    "shift_patterns": {
      "shift_length": "Duration can indicate player fatigue",
      "shift_overlap": "Players on ice together",
      "line_stability": "How long current line combination has been together",
      "rest_time": "Time between shifts for each player"
    },
    
    "goal_indicators": {
      "scorer_shift_time": "How long scorer has been on ice",
      "assist_patterns": "Players involved in assist",
      "defensive_matchup": "Opposing players on ice",
      "special_teams": "Derived from player counts"
    },
    
    "temporal_features": {
      "period_time": "Time elapsed in current period",
      "game_time": "Total time elapsed in game",
      "period_number": "Which period (affects strategy)",
      "time_remaining": "Urgency factor"
    }
  },
  
  "data_quality_notes": {
    "missing_data": {
      "goalie_shifts": "Goalies show continuous shifts per period",
      "bench_time": "Time between shifts not explicitly tracked",
      "position_data": "Must be joined from roster data"
    },
    
    "assumptions": {
      "shift_accuracy": "Start/end times accurate to second",
      "player_identification": "playerId is consistent across seasons",
      "event_ordering": "eventNumber provides chronological order"
    }
  },
  
  "llm_instructions": {
    "pattern_recognition": [
      "Identify pre-goal shift patterns that correlate with scoring",
      "Detect fatigue indicators from shift duration and frequency",
      "Recognize special teams situations from player counts",
      "Track line chemistry from repeated shift combinations"
    ],
    
    "feature_extraction": [
      "Calculate cumulative ice time for each player",
      "Identify fresh legs vs tired players",
      "Detect momentum shifts from rapid player changes",
      "Track zone time from shift patterns"
    ],
    
    "model_inputs": [
      "Current players on ice (both teams)",
      "Time on ice for each player in current shift",
      "Recent shift history (last 3 shifts per player)",
      "Special teams status",
      "Score differential",
      "Period and time remaining"
    ]
  }
}

## . **312k shots on net** (`data\nhl\raw\nhl_shots_2024-10-01_to_2025-04-15.csv`)

Model Architecture Recommendations
Based on this data structure, consider:

Input Layer: ~25-30 features after encoding
Hidden Layers:

Dense layers with batch normalization
Dropout for regularization
Consider separate pathways for spatial vs temporal features

Output: Single sigmoid activation for goal probability
Loss Function: Binary cross-entropy with class weights (due to ~10% positive rate)
Metrics: AUC-ROC, Brier score, log loss

{
  "data_description": {
    "name": "NHL Shot Data for xG Model",
    "version": "1.0",
    "season": "2024-25",
    "total_records": "312,000 shots",
    "purpose": "Neural network training for Expected Goals (xG) prediction",
    "granularity": "Individual shot attempts with contextual features"
  },

  "core_identifiers": {
    "game_id": {
      "type": "integer",
      "description": "Unique game identifier",
      "format": "YYYYGGGGGG where YYYY=season start year, GGGGGG=game number"
    },
    "season": {
      "type": "integer", 
      "description": "Season identifier",
      "format": "YYYYYYYY (start year + end year)"
    },
    "game_type": {
      "type": "integer",
      "description": "Game type code",
      "values": {
        "1": "Preseason",
        "2": "Regular Season",
        "3": "Playoffs",
        "4": "All-Star"
      }
    }
  },

  "temporal_features": {
    "game_date": {
      "type": "date",
      "format": "YYYY-MM-DD",
      "description": "Date of the game"
    },
    "period": {
      "type": "integer",
      "description": "Game period",
      "values": {
        "1": "1st Period",
        "2": "2nd Period", 
        "3": "3rd Period",
        "4": "Overtime",
        "5": "Shootout"
      }
    },
    "period_type": {
      "type": "string",
      "description": "Type of period",
      "values": ["REG", "OT", "SO"]
    },
    "time_in_period": {
      "type": "integer",
      "description": "Seconds elapsed in current period"
    },
    "time_remaining": {
      "type": "string",
      "format": "MM:SS",
      "description": "Time remaining in period"
    },
    "game_seconds": {
      "type": "integer",
      "description": "Total seconds elapsed in game"
    }
  },

  "shot_features": {
    "event_type": {
      "type": "string",
      "description": "Type of shot event",
      "values": [
        "shot-on-goal",
        "missed-shot",
        "blocked-shot",
        "goal"
      ]
    },
    "shot_type": {
      "type": "string",
      "description": "Type of shot taken",
      "values": [
        "wrist",
        "snap", 
        "slap",
        "tip-in",
        "deflection",
        "backhand",
        "wraparound"
      ]
    },
    "is_goal": {
      "type": "binary",
      "description": "Whether the shot resulted in a goal",
      "values": [0, 1]
    },
    "reason": {
      "type": "string",
      "description": "Reason for missed shot",
      "values": ["wide-left", "wide-right", "high", "short", "blocked", "saved"]
    }
  },

  "spatial_features": {
    "x_coord": {
      "type": "float",
      "description": "X-coordinate on ice (feet from center ice)",
      "range": [-100, 100],
      "note": "Negative = defensive zone, Positive = offensive zone"
    },
    "y_coord": {
      "type": "float",
      "description": "Y-coordinate on ice (feet from center line)",
      "range": [-42.5, 42.5],
      "note": "Negative = left side, Positive = right side"
    },
    "zone_code": {
      "type": "string",
      "description": "Zone where shot occurred",
      "values": {
        "O": "Offensive zone",
        "N": "Neutral zone",
        "D": "Defensive zone"
      }
    },
    "shot_distance": {
      "type": "float",
      "description": "Distance from net (feet)",
      "calculation": "sqrt((89-abs(x))^2 + y^2)"
    },
    "shot_angle": {
      "type": "float",
      "description": "Angle from net (degrees)",
      "range": [0, 180],
      "note": "0° = directly in front, 180° = behind goal line"
    }
  },

  "player_identifiers": {
    "shooter_id": {
      "type": "integer",
      "description": "Unique identifier for shooting player"
    },
    "shooter_name": {
      "type": "string",
      "description": "Name of shooting player"
    },
    "goalie_id": {
      "type": "float",
      "description": "Unique identifier for goalie (null if empty net)"
    },
    "goalie_name": {
      "type": "string",
      "description": "Name of goalie"
    },
    "assist1_id": {
      "type": "float",
      "description": "Primary assist player ID (goals only)"
    },
    "assist1_name": {
      "type": "string",
      "description": "Primary assist player name"
    },
    "assist2_id": {
      "type": "float",
      "description": "Secondary assist player ID (goals only)"
    },
    "assist2_name": {
      "type": "string",
      "description": "Secondary assist player name"
    },
    "blocker_id": {
      "type": "float",
      "description": "Player who blocked shot (blocked shots only)"
    }
  },

  "team_identifiers": {
    "shooting_team_id": {
      "type": "integer",
      "description": "ID of team taking shot"
    },
    "shooting_team": {
      "type": "string",
      "description": "Abbreviation of shooting team"
    },
    "home_team_id": {
      "type": "integer",
      "description": "Home team ID"
    },
    "home_team": {
      "type": "string",
      "description": "Home team abbreviation"
    },
    "away_team_id": {
      "type": "integer",
      "description": "Away team ID"
    },
    "away_team": {
      "type": "string",
      "description": "Away team abbreviation"
    },
    "is_home_team": {
      "type": "binary",
      "description": "Whether shooting team is home team",
      "values": [0, 1]
    }
  },

  "game_state_features": {
    "home_score": {
      "type": "integer",
      "description": "Home team score at time of shot"
    },
    "away_score": {
      "type": "integer",
      "description": "Away team score at time of shot"
    },
    "score_differential": {
      "type": "integer",
      "description": "Score difference from shooting team perspective",
      "calculation": "shooting_team_score - opposing_team_score"
    },
    "is_tied": {
      "type": "binary",
      "description": "Whether game is tied"
    },
    "is_leading": {
      "type": "binary",
      "description": "Whether shooting team is leading"
    }
  },

  "strength_state_features": {
    "home_skaters": {
      "type": "integer",
      "description": "Number of home team skaters on ice",
      "range": [3, 6]
    },
    "away_skaters": {
      "type": "integer",
      "description": "Number of away team skaters on ice",
      "range": [3, 6]
    },
    "strength_state": {
      "type": "integer",
      "description": "Encoded strength state",
      "encoding": "1000*home_skaters + 100*away_skaters + 10*home_goalie + away_goalie"
    },
    "is_powerplay": {
      "type": "binary",
      "description": "Whether shooting team has man advantage"
    },
    "is_shorthanded": {
      "type": "binary",
      "description": "Whether shooting team is shorthanded"
    },
    "empty_net": {
      "type": "binary",
      "description": "Whether opposing net is empty"
    },
    "is_penalty_shot": {
      "type": "binary",
      "description": "Whether shot is a penalty shot"
    }
  },

  "shot_sequence_features": {
    "prev_event_type": {
      "type": "string",
      "description": "Type of previous event",
      "values": ["shot", "hit", "giveaway", "takeaway", "faceoff", etc.]
    },
    "prev_event_x": {
      "type": "float",
      "description": "X-coordinate of previous event"
    },
    "prev_event_y": {
      "type": "float",
      "description": "Y-coordinate of previous event"
    },
    "prev_event_team": {
      "type": "float",
      "description": "Team ID of previous event"
    },
    "time_since_prev_event": {
      "type": "integer",
      "description": "Seconds since previous event"
    },
    "distance_from_prev_event": {
      "type": "float",
      "description": "Distance from previous event location (feet)"
    },
    "speed_from_prev": {
      "type": "float",
      "description": "Speed of puck movement (feet/second)",
      "calculation": "distance_from_prev_event / time_since_prev_event"
    }
  },

  "shot_history_features": {
    "time_since_prev_shot": {
      "type": "integer",
      "description": "Seconds since last shot attempt"
    },
    "prev_shot_result": {
      "type": "string",
      "description": "Result of previous shot",
      "values": ["goal", "shot-on-goal", "missed-shot", "blocked-shot"]
    },
    "shots_in_sequence": {
      "type": "integer",
      "description": "Number of consecutive shots by same team"
    }
  },

  "faceoff_features": {
    "time_since_faceoff": {
      "type": "integer",
      "description": "Seconds since last faceoff"
    },
    "faceoff_win": {
      "type": "binary",
      "description": "Whether shooting team won last faceoff"
    },
    "faceoff_zone": {
      "type": "string",
      "description": "Zone of last faceoff",
      "values": ["O", "N", "D"]
    },
    "is_off_zone_faceoff": {
      "type": "binary",
      "description": "Whether shot came from offensive zone faceoff"
    }
  },

  "shot_quality_features": {
    "is_rebound": {
      "type": "binary",
      "description": "Whether shot is a rebound opportunity"
    },
    "is_rush": {
      "type": "binary",
      "description": "Whether shot came off a rush"
    },
    "is_one_timer": {
      "type": "binary",
      "description": "Whether shot was a one-timer"
    },
    "is_backhand": {
      "type": "binary",
      "description": "Whether shot was backhand"
    },
    "is_deflection": {
      "type": "binary",
      "description": "Whether shot was deflected"
    },
    "is_wraparound": {
      "type": "binary",
      "description": "Whether shot was wraparound attempt"
    }
  },

  "zone_time_features": {
    "time_since_zone_entry": {
      "type": "float",
      "description": "Seconds since puck entered offensive zone"
    },
    "offensive_zone_time": {
      "type": "integer",
      "description": "Total seconds in offensive zone during possession"
    }
  },

  "target_variable": {
    "is_goal": {
      "type": "binary",
      "description": "Primary target for xG model",
      "values": [0, 1],
      "class_balance": "Approximately 8-10% positive class"
    }
  },

  "feature_engineering_recommendations": {
    "high_importance": [
      "shot_distance",
      "shot_angle",
      "shot_type",
      "is_rebound",
      "is_rush",
      "empty_net",
      "prev_event_type"
    ],
    "medium_importance": [
      "score_differential",
      "is_powerplay",
      "time_since_prev_shot",
      "offensive_zone_time",
      "is_one_timer"
    ],
    "interaction_features": [
      "distance_x_angle",
      "rush_x_distance",
      "rebound_x_time_since_shot",
      "powerplay_x_shot_type"
    ]
  },

  "data_quality_notes": {
    "missing_values": {
      "goalie_id": "NULL when empty net or penalty shot",
      "assist_ids": "NULL for non-goals",
      "blocker_id": "NULL for non-blocked shots",
      "prev_event_coords": "May be NULL for first event"
    },
    "validation_checks": [
      "shot_distance should match calculated distance from coordinates",
      "strength_state encoding should match skater counts",
      "is_goal should be 1 only for event_type='goal'"
    ]
  }
}

## . **Processed Data Examples** (`data\nhl\processed`)

data/nhl/processed/data_manifest.json 
data/nhl/processed/fast_break_patterns.csv 
data/nhl/processed/feature_documentation.txt 
data/nhl/processed/goal_sequences_fixed.csv 
data/nhl/processed/goalie_shift_patterns.csv 
data/nhl/processed/goalie_workload_all_shots.csv 
data/nhl/processed/goalie_workload.csv 
data/nhl/processed/offensive_zone_times.csv 
data/nhl/processed/pass_type_summary.csv 
data/nhl/processed/passing_sequences.csv 
data/nhl/processed/player_shift_patterns.csv 
data/nhl/processed/player_shot_patterns.csv 
data/nhl/processed/player_tiers.csv 
data/nhl/processed/player_turnover_risk.csv 
data/nhl/processed/rebound_patterns.csv 
data/nhl/processed/shots_enhanced_all_passes.csv 
data/nhl/processed/skater_shift_patterns.csv 
data/nhl/processed/training_assists_simplified.csv 
data/nhl/processed/training_data_enhanced.csv 
data/nhl/processed/training_data_model_ready.csv 
data/nhl/processed/training_data_with_assists.csv 
data/nhl/processed/training_data_with_danger.csv 
data/nhl/processed/training_data_with_on_ice.csv 
data/nhl/processed/turnover_pressure_analysis_60s.csv

## . **24-25 season stats** (`data\nhl\season_stats`)

(data/nhl/season_stats/all_players_202425.json) 
(data/nhl/season_stats/goalie_lookup.json) 
(data/nhl/season_stats/goalies_202425.json) 
(data/nhl/season_stats/skater_lookup.json) 
(data/nhl/season_stats/skaters_202425.json)

## 4. **NHL Play by Play** (`data\nhl\play_by_play`)

NHL 2024-25 Season Data Manifest

- Dataset Overview
- **Total Games**: 1,312 games
- **Season**: 2024-2025
- **Game Type**: Regular Season (gameType: 2)
- **Coverage**: All 32 NHL teams × 82 games each
- **Data Format**: JSON files per game
- **File Pattern**: `game_20240200XX.json` through `game_20240213XX.json`

- File Structure
data/
├── play_by_play/
│   ├── game_2024020001.json  # Season opener
│   ├── game_2024020002.json
│   ├── game_2024020003.json  # SEA vs STL (sample 1)
│   ├── game_2024020026.json  # TOR vs PIT (sample 2)
│   └── ... (1,312 total files)

- Game ID Format
- **Pattern**: `YYYYTTNNNN`
  - `YYYY`: Season year (2024)
  - `TT`: Game type (02 = Regular season)
  - `NNNN`: Sequential game number (0001-1312)

- Expected Data Volume
| Metric | Count | Notes |
|--------|-------|-------|
| Total Games | 1,312 | Each game appears once |
| Total Team-Games | 2,624 | 32 teams × 82 games |
| Shot Events (505,506,507,508) | ~315,000 | ~240 per game |
| Total Events (all types) | ~2.5M | ~1,900 per game |
| Unique Players | ~800 | Roster players |
| Unique Goalies | ~80 | Starting + backup |

- Teams Included (32)
- **Atlantic**: BOS, BUF, DET, FLA, MTL, OTT, TBL, TOR
- **Metropolitan**: CAR, CBJ, NJD, NYI, NYR, PHI, PIT, WSH  
- **Central**: ARI, CHI, COL, DAL, MIN, NSH, STL, WPG
- **Pacific**: ANA, CGY, EDM, LAK, SJS, SEA, VAN, VGK

- Data Completeness Checklist
- [ ] All 1,312 game files present
- [ ] Each team appears in exactly 82 games
- [ ] No duplicate gameIds
- [ ] All files parse as valid JSON
- [ ] Date range: October 2024 - April 2025

- Key Fields for xG Model
```json
{
  "plays": [
    {
      "typeCode": 505-508,  // Shot-related events
      "details": {
        "xCoord": -100 to 100,
        "yCoord": -42 to 42,
        "shotType": "wrist|slap|snap|tip-in|backhand|deflected|wrap-around",
        "shootingPlayerId": 8XXXXXX,
        "goalieInNetId": 8XXXXXX
      }
    }
  ]
}
Processing Priority

Core Events: 505 (goals), 506 (shots), 507 (missed), 508 (blocked)
Context Events: 502 (faceoffs), 509 (penalties) for situation
Sequence Events: Recent 5-10 events before each shot

This manifest gives you a clear overview of your complete dataset structure and what to expect when processing all games







data/nhl/processed/data_manifest.json 
data/nhl/processed/fast_break_patterns.csv 
data/nhl/processed/feature_documentation.txt 
data/nhl/processed/goal_sequences_fixed.csv 
data/nhl/processed/goalie_shift_patterns.csv 
data/nhl/processed/goalie_workload.csv 
data/nhl/processed/NHL_AI_TRAINING_FINAL.csv 
data/nhl/processed/offensive_zone_times.csv 
data/nhl/processed/pass_type_summary.csv 
data/nhl/processed/passing_sequences.csv 
data/nhl/processed/player_shift_patterns.csv 
data/nhl/processed/player_shot_patterns.csv 
data/nhl/processed/player_tiers.csv 
data/nhl/processed/player_turnover_risk.csv 
data/nhl/processed/rebound_patterns.csv 
data/nhl/processed/skater_shift_patterns.csv 
data/nhl/processed/turnover_pressure_analysis_60s.csv