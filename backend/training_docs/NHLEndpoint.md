(penguins_env) PS C:\Users\Robert Wolfe\Desktop\renewed-solutions\penguins_ai> python scripts/deep_api_diagnostic.py 
Deep analysis of NHL API play-by-play structure...

Analyzing 2024020008.json in detail...

============================================================
TOP-LEVEL API STRUCTURE
============================================================
Keys: ['id', 'season', 'gameType', 'limitedScoring', 'gameDate', 'venue', 'venueLocation', 'startTimeUTC', 'easternUTCOffset', 'venueUTCOffset', 'tvBroadcasts', 'gameState', 'gameScheduleState', 'periodDescriptor', 'awayTeam', 'homeTeam', 'shootoutInUse', 'otInUse', 'clock', 'displayPeriod', 'maxPeriods', 'gameOutcome', 'plays', 'rosterSpots', 'regPeriods', 'summary']

Array 'tvBroadcasts' has 2 items
  First item keys: ['id', 'market', 'countryCode', 'network', 'sequenceNumber']

Array 'plays' has 285 items
  First item keys: ['eventId', 'periodDescriptor', 'timeInPeriod', 'timeRemaining', 'situationCode', 'homeTeamDefendingSide', 'typeCode', 'typeDescKey', 'sortOrder']

Array 'rosterSpots' has 40 items
  First item keys: ['teamId', 'playerId', 'firstName', 'lastName', 'sweaterNumber', 'positionCode', 'headshot']


Total plays in game: 285

============================================================
ALL UNIQUE KEYS IN PLAYS
============================================================
Play-level keys: ['details', 'eventId', 'homeTeamDefendingSide', 'periodDescriptor', 'pptReplayUrl', 'situationCode', 'sortOrder', 'timeInPeriod', 'timeRemaining', 'typeCode', 'typeDescKey']

Detail-level keys: ['assist1PlayerId', 'assist1PlayerTotal', 'assist2PlayerId', 'assist2PlayerTotal', 'awaySOG', 'awayScore', 'blockingPlayerId', 'committedByPlayerId', 'descKey', 'discreteClip', 'discreteClipFr', 'drawnByPlayerId', 'duration', 'eventOwnerTeamId', 'goalieInNetId', 'highlightClip', 'highlightClipSharingUrl', 'hitteePlayerId', 'hittingPlayerId', 'homeSOG', 'homeScore', 'losingPlayerId', 'playerId', 'reason', 'scoringPlayerId', 'scoringPlayerTotal', 'secondaryReason', 'shootingPlayerId', 'shotType', 'typeCode', 'winningPlayerId', 'xCoord', 'yCoord', 'zoneCode']

Situation keys: []

============================================================
SEARCHING FOR PASS-RELATED DATA
============================================================
Found pass-related references:
  displayPeriod: displayPeriod = 1
  plays: plays = [{'eventId': 102, 'periodDescriptor': {'number': 1, 'periodType': 'REG', 'maxRegulationPeriods': 3},
  plays[1].details.losingPlayerId: losingPlayerId = 8474641
  plays[1].details.winningPlayerId: winningPlayerId = 8476392
  plays[2].details.hittingPlayerId: hittingPlayerId = 8478891
  plays[2].details.hitteePlayerId: hitteePlayerId = 8480834
  plays[3].details.hittingPlayerId: hittingPlayerId = 8475799
  plays[3].details.hitteePlayerId: hitteePlayerId = 8480834
  plays[4].details.hittingPlayerId: hittingPlayerId = 8476392
  plays[4].details.hitteePlayerId: hitteePlayerId = 8480834
  plays[5].details.hittingPlayerId: hittingPlayerId = 8478891
  plays[5].details.hitteePlayerId: hitteePlayerId = 8477406
  plays[6].details.shootingPlayerId: shootingPlayerId = 8476460
  plays[8].details.losingPlayerId: losingPlayerId = 8477934
  plays[8].details.winningPlayerId: winningPlayerId = 8476480
  rosterSpots[0].playerId: playerId = 8470621
  rosterSpots[1].playerId: playerId = 8474641
  rosterSpots[2].playerId: playerId = 8475218
  rosterSpots[3].playerId: playerId = 8475717
  rosterSpots[4].playerId: playerId = 8475784

============================================================
SAMPLE COMPLETE PLAY OBJECTS
============================================================

--- PERIOD-START EVENT (index 0) ---
{ 'eventId': 102,
  'homeTeamDefendingSide': 'left',
  'periodDescriptor': {'maxRegulationPeriods': 3, 'number': 1, 'periodType': 'REG'},
  'situationCode': '1551',
  'sortOrder': 10,
  'timeInPeriod': '00:00',
  'timeRemaining': '20:00',
  'typeCode': 520,
  'typeDescKey': 'period-start'}

--- FACEOFF EVENT (index 1) ---
{ 'details': { 'eventOwnerTeamId': 52,
               'losingPlayerId': 8474641,
               'winningPlayerId': 8476392,
               'xCoord': 0,
               'yCoord': 0,
               'zoneCode': 'N'},
  'eventId': 101,
  'homeTeamDefendingSide': 'left',
  'periodDescriptor': {'maxRegulationPeriods': 3, 'number': 1, 'periodType': 'REG'},
  'situationCode': '1551',
  'sortOrder': 11,
  'timeInPeriod': '00:00',
  'timeRemaining': '20:00',
  'typeCode': 502,
  'typeDescKey': 'faceoff'}

  *** Multiple players in this event: ['losingPlayerId', 'winningPlayerId']

--- HIT EVENT (index 2) ---
{ 'details': { 'eventOwnerTeamId': 52,
               'hitteePlayerId': 8480834,
               'hittingPlayerId': 8478891,
               'xCoord': -98,
               'yCoord': -21,
               'zoneCode': 'O'},
  'eventId': 88,
  'homeTeamDefendingSide': 'left',
  'periodDescriptor': {'maxRegulationPeriods': 3, 'number': 1, 'periodType': 'REG'},
  'situationCode': '1551',
  'sortOrder': 12,
  'timeInPeriod': '00:07',
  'timeRemaining': '19:53',
  'typeCode': 503,
  'typeDescKey': 'hit'}

  *** Multiple players in this event: ['hittingPlayerId', 'hitteePlayerId']

--- SHOT-ON-GOAL EVENT (index 6) ---
{ 'details': { 'awaySOG': 1,
               'eventOwnerTeamId': 52,
               'goalieInNetId': 8479973,
               'homeSOG': 0,
               'shootingPlayerId': 8476460,
               'shotType': 'wrist',
               'xCoord': -70,
               'yCoord': 4,
               'zoneCode': 'O'},
  'eventId': 62,
  'homeTeamDefendingSide': 'left',
  'periodDescriptor': {'maxRegulationPeriods': 3, 'number': 1, 'periodType': 'REG'},
  'situationCode': '1551',
  'sortOrder': 24,
  'timeInPeriod': '01:14',
  'timeRemaining': '18:46',
  'typeCode': 506,
  'typeDescKey': 'shot-on-goal'}

--- STOPPAGE EVENT (index 7) ---
{ 'details': {'reason': 'goalie-stopped-after-sog'},
  'eventId': 8,
  'homeTeamDefendingSide': 'left',
  'periodDescriptor': {'maxRegulationPeriods': 3, 'number': 1, 'periodType': 'REG'},
  'situationCode': '1551',
  'sortOrder': 25,
  'timeInPeriod': '01:16',
  'timeRemaining': '18:44',
  'typeCode': 516,
  'typeDescKey': 'stoppage'}

============================================================
GOAL EVENTS ANALYSIS
============================================================

--- GOAL #1 ---
{ 'details': { 'assist1PlayerId': 8475799,
               'assist1PlayerTotal': 1,
               'assist2PlayerId': 8478891,
               'assist2PlayerTotal': 1,
               'awayScore': 1,
               'discreteClip': 6363056815112,
               'discreteClipFr': 6363057193112,
               'eventOwnerTeamId': 52,
               'goalieInNetId': 8479973,
               'highlightClip': 6363056523112,
               'highlightClipSharingUrl': 'https://nhl.com/video/wpg-edm-lowry-scores-goal-against-stuart-skinner-6363056523112',        
               'homeScore': 0,
               'scoringPlayerId': 8476392,
               'scoringPlayerTotal': 1,
               'shotType': 'wrist',
               'xCoord': -90,
               'yCoord': -11,
               'zoneCode': 'O'},
  'eventId': 347,
  'homeTeamDefendingSide': 'left',
  'periodDescriptor': {'maxRegulationPeriods': 3, 'number': 1, 'periodType': 'REG'},
  'pptReplayUrl': 'https://wsr.nhle.com/sprites/20242025/2024020008/ev347.json',
  'situationCode': '1551',
  'sortOrder': 183,
  'timeInPeriod': '14:56',
  'timeRemaining': '05:04',
  'typeCode': 505,
  'typeDescKey': 'goal'}

Details keys: ['xCoord', 'yCoord', 'zoneCode', 'shotType', 'scoringPlayerId', 'scoringPlayerTotal', 'assist1PlayerId', 'assist1PlayerTotal', 'assist2PlayerId', 'assist2PlayerTotal', 'eventOwnerTeamId', 'goalieInNetId', 'awayScore', 'homeScore', 'highlightClipSharingUrl', 'highlightClip', 'discreteClip', 'discreteClipFr']
  scoringPlayerId: 8476392
  scoringPlayerTotal: 1
  assist1PlayerId: 8475799
  assist1PlayerTotal: 1
  assist2PlayerId: 8478891
  assist2PlayerTotal: 1

--- GOAL #2 ---
{ 'details': { 'assist1PlayerId': 8475799,
               'assist1PlayerTotal': 2,
               'assist2PlayerId': 8480145,
               'assist2PlayerTotal': 1,
               'awayScore': 2,
               'discreteClip': 6363056928112,
               'discreteClipFr': 6363057105112,
               'eventOwnerTeamId': 52,
               'goalieInNetId': 8479973,
               'highlightClip': 6363057494112,
               'highlightClipSharingUrl': 'https://nhl.com/video/wpg-edm-appleton-scores-goal-against-stuart-skinner-6363057494112',     
               'homeScore': 0,
               'scoringPlayerId': 8478891,
               'scoringPlayerTotal': 1,
               'shotType': 'wrist',
               'xCoord': -68,
               'yCoord': -16,
               'zoneCode': 'O'},
  'eventId': 429,
  'homeTeamDefendingSide': 'left',
  'periodDescriptor': {'maxRegulationPeriods': 3, 'number': 1, 'periodType': 'REG'},
  'pptReplayUrl': 'https://wsr.nhle.com/sprites/20242025/2024020008/ev429.json',
  'situationCode': '1551',
  'sortOrder': 222,
  'timeInPeriod': '18:35',
  'timeRemaining': '01:25',
  'typeCode': 505,
  'typeDescKey': 'goal'}

Details keys: ['xCoord', 'yCoord', 'zoneCode', 'shotType', 'scoringPlayerId', 'scoringPlayerTotal', 'assist1PlayerId', 'assist1PlayerTotal', 'assist2PlayerId', 'assist2PlayerTotal', 'eventOwnerTeamId', 'goalieInNetId', 'awayScore', 'homeScore', 'highlightClipSharingUrl', 'highlightClip', 'discreteClip', 'discreteClipFr']
  scoringPlayerId: 8478891
  scoringPlayerTotal: 1
  assist1PlayerId: 8475799
  assist1PlayerTotal: 2
  assist2PlayerId: 8480145
  assist2PlayerTotal: 1

--- GOAL #3 ---
{ 'details': { 'assist1PlayerId': 8477504,
               'assist1PlayerTotal': 1,
               'assist2PlayerId': 8480289,
               'assist2PlayerTotal': 1,
               'awayScore': 3,
               'discreteClip': 6363058594112,
               'discreteClipFr': 6363058117112,
               'eventOwnerTeamId': 52,
               'goalieInNetId': 8479973,
               'highlightClip': 6363058508112,
               'highlightClipSharingUrl': 'https://nhl.com/video/wpg-edm-kupari-scores-goal-against-stuart-skinner-6363058508112',       
               'homeScore': 0,
               'scoringPlayerId': 8480845,
               'scoringPlayerTotal': 1,
               'shotType': 'snap',
               'xCoord': 66,
               'yCoord': 12,
               'zoneCode': 'O'},
  'eventId': 490,
  'homeTeamDefendingSide': 'right',
  'periodDescriptor': {'maxRegulationPeriods': 3, 'number': 2, 'periodType': 'REG'},
  'pptReplayUrl': 'https://wsr.nhle.com/sprites/20242025/2024020008/ev490.json',
  'situationCode': '1551',
  'sortOrder': 289,
  'timeInPeriod': '04:17',
  'timeRemaining': '15:43',
  'typeCode': 505,
  'typeDescKey': 'goal'}

Details keys: ['xCoord', 'yCoord', 'zoneCode', 'shotType', 'scoringPlayerId', 'scoringPlayerTotal', 'assist1PlayerId', 'assist1PlayerTotal', 'assist2PlayerId', 'assist2PlayerTotal', 'eventOwnerTeamId', 'goalieInNetId', 'awayScore', 'homeScore', 'highlightClipSharingUrl', 'highlightClip', 'discreteClip', 'discreteClipFr']
  scoringPlayerId: 8480845
  scoringPlayerTotal: 1
  assist1PlayerId: 8477504
  assist1PlayerTotal: 1
  assist2PlayerId: 8480289
  assist2PlayerTotal: 1

============================================================
OTHER DATA SOURCES IN API RESPONSE
============================================================

============================================================
SUMMARY
============================================================
Total unique play types: 11
Total unique detail keys: 34
Pass-related references found: 25

Detail keys by event type:

blocked-shot:
  blockingPlayerId, eventOwnerTeamId, reason, shootingPlayerId, xCoord, yCoord, zoneCode

delayed-penalty:
  eventOwnerTeamId

faceoff:
  eventOwnerTeamId, losingPlayerId, winningPlayerId, xCoord, yCoord, zoneCode

giveaway:
  eventOwnerTeamId, playerId, xCoord, yCoord, zoneCode

goal:
  assist1PlayerId, assist1PlayerTotal, assist2PlayerId, assist2PlayerTotal, awayScore, discreteClip, discreteClipFr, eventOwnerTeamId, goalieInNetId, highlightClip, highlightClipSharingUrl, homeScore, scoringPlayerId, scoringPlayerTotal, shotType, xCoord, yCoord, zoneCode  

hit:
  eventOwnerTeamId, hitteePlayerId, hittingPlayerId, xCoord, yCoord, zoneCode

missed-shot:
  eventOwnerTeamId, goalieInNetId, reason, shootingPlayerId, shotType, xCoord, yCoord, zoneCode

penalty:
  committedByPlayerId, descKey, drawnByPlayerId, duration, eventOwnerTeamId, typeCode, xCoord, yCoord, zoneCode

shot-on-goal:
  awaySOG, eventOwnerTeamId, goalieInNetId, homeSOG, shootingPlayerId, shotType, xCoord, yCoord, zoneCode

stoppage:
  reason, secondaryReason
(penguins_env) PS C:\Users\Robert Wolfe\Desktop\renewed-solutions\penguins_ai> 