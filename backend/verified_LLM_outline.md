The model should distinguish:

Angle-Specific Scoring Patterns

Which angle ranges have highest goal probability
How angle interacts with shot type (wrist shots vs one-timers)
Handedness effects (left-handed shooter from right side)

Distance-Angle Interactions

Close-range wide angles (wraparounds, stuff attempts)
Mid-range optimal angles (one-timer spots)
Long-range straight shots (point shots through traffic)

Contextual Angle Value

Same angle has different value based on:

Pass origin (cross-ice pass makes sharp angles dangerous)
Goalie positioning (time since last event)
Shot type (deflections work better from certain angles)

Primary Input File
data/nhl/processed/training_data_enhanced.csv (or your consolidated master file)
Required Features for Angle Learning
Core Geometric Features

shot_angle (float, 0-180): Angle from net center
shot_distance (float): Distance to net in feet
x_coord (float, -100 to 100): Rink X coordinate
y_coord (float, -42.5 to 42.5): Rink Y coordinate

Shot Context Features

shot_type (string): ['wrist', 'slap', 'snap', 'tip-in', 'backhand', 'deflected', 'wrap-around']
prev_event_x (float): Previous event X coordinate
prev_event_y (float): Previous event Y coordinate
prev_event_type (string): Type of previous event
time_since_prev_event (float): Seconds elapsed

Player Features (CURRENTLY MISSING - CRITICAL)

shooter_position (string): ['C', 'LW', 'RW', 'D']
shooter_shoots (string): ['L', 'R']
goalie_catches (string): ['L', 'R']

Engineered Features to Add
python# Add these before training
df['angle_rad'] = np.radians(df['shot_angle'])
df['sin_angle'] = np.sin(df['angle_rad'])
df['cos_angle'] = np.cos(df['angle_rad'])
df['is_off_wing'] = ((df['y_coord'] > 0) & (df['shooter_shoots'] == 'L')) | 
                    ((df['y_coord'] < 0) & (df['shooter_shoots'] == 'R'))
df['pass_angle_change'] = np.abs(
    np.arctan2(df['y_coord'], df['x_coord']) - 
    np.arctan2(df['prev_event_y'], df['prev_event_x'])
) * 180 / np.pi
Sequence Features (Already in file)

royal_road_pass (int, 0/1): Cross-slot pass indicator
is_rebound (int, 0/1): Rebound opportunity
is_rush (int, 0/1): Rush chance
time_since_zone_entry (float): Seconds in zone

Target Variable

is_goal (int, 0/1): Binary target

Data Types Summary
python# Floats
numeric_features = [
    'shot_angle', 'shot_distance', 'x_coord', 'y_coord',
    'prev_event_x', 'prev_event_y', 'time_since_prev_event',
    'sin_angle', 'cos_angle', 'pass_angle_change'
]

# Categoricals (need encoding)
categorical_features = [
    'shot_type', 'prev_event_type', 'shooter_position',
    'shooter_shoots', 'goalie_catches'
]

# Binary flags
binary_features = [
    'is_goal', 'royal_road_pass', 'is_rebound', 'is_rush',
    'is_off_wing', 'is_power_play', 'is_shorthanded'
]
Critical Missing Data

Shooter position/handedness - Must extract from player files
Goalie handedness - Must extract from player files
On-ice player quality - Only have for 4K rows, need for all

Without shooter position and handedness, the model can't properly learn angle effectiveness!

## 1. data\nhl\play_by_play

def document_pbp_folder():
    """Document play-by-play JSON structure and coverage"""
    
    pbp_dir = Path("data/nhl/play_by_play")
    
    # 1. File inventory
    print(f"Total PBP files: {len(list(pbp_dir.glob('*.json')))}")
    print(f"File naming pattern: {game_id}.json")
    
    # 2. Sample structure from one file
    with open(pbp_dir / "2024020008.json") as f:
        sample = json.load(f)
    
    # Document key fields
    structure = {
        "game_metadata": ["id", "gameDate", "startTimeUTC", "venue", "gameState"],
        "teams": ["homeTeam", "awayTeam"],
        "plays": {
            "count": len(sample.get("plays", [])),
            "event_types": ["goal", "shot-on-goal", "missed-shot", "blocked-shot", 
                          "hit", "giveaway", "takeaway", "faceoff", "penalty"],
            "key_fields": ["eventId", "timeInPeriod", "typeDescKey", "details"]
        },
        "details_by_type": {
            "goal": ["scoringPlayerId", "assist1PlayerId", "xCoord", "yCoord"],
            "shot": ["shootingPlayerId", "shotType", "xCoord", "yCoord", "goalieInNetId"],
            "faceoff": ["winningPlayerId", "losingPlayerId", "zoneCode"]
        }
    }
    
    # 3. Data quality checks
    missing_games = shots_games - pbp_games  # Games in shots but not PBP
    coordinate_alignment = verify_coordinates_match()  # Compare x,y between datasets
    
    return structure

