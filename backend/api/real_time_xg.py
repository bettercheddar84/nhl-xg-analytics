"""
Real-time xG integration for live NHL games
Connects to NHL API and provides live xG analysis
"""

import asyncio
import aiohttp
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import json
from api.xg_client import XGModelClient, Shot
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NHLGameTracker:
    """Track NHL games and calculate real-time xG"""
    
    def __init__(self, xg_client: Optional[XGModelClient] = None):
        self.xg_client = xg_client or XGModelClient()
        self.nhl_base_url = "https://api-web.nhle.com/v1"
        self.tracked_games = {}
        self.player_cache = {}
        
    async def fetch_json(self, session: aiohttp.ClientSession, url: str) -> Dict:
        """Fetch JSON data from URL"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch {url}: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return {}
    
    async def get_todays_games(self) -> List[Dict]:
        """Get all games for today"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.nhl_base_url}/score/{today}"
            data = await self.fetch_json(session, url)
            
            games = []
            for game in data.get('games', []):
                games.append({
                    'game_id': game['id'],
                    'home_team': game['homeTeam']['abbrev'],
                    'away_team': game['awayTeam']['abbrev'],
                    'status': game['gameState'],
                    'period': game.get('period', 0),
                    'time_remaining': game.get('clock', '00:00')
                })
            
            return games
    
    async def get_game_plays(self, game_id: str) -> List[Dict]:
        """Get play-by-play data for a game"""
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.nhl_base_url}/gamecenter/{game_id}/play-by-play"
            data = await self.fetch_json(session, url)
            
            plays = []
            for play in data.get('plays', []):
                if play['typeDescKey'] in ['shot-on-goal', 'goal', 'missed-shot', 'blocked-shot']:
                    plays.append(self._parse_shot_play(play, game_id))
            
            return plays
    
    def _parse_shot_play(self, play: Dict, game_id: str) -> Dict:
        """Parse shot play into format for xG model"""
        
        details = play.get('details', {})
        
        # Extract coordinates
        x_coord = details.get('xCoord', 0)
        y_coord = details.get('yCoord', 0)
        
        # Calculate distance and angle
        # NHL rink: goals at x=±89, y=0
        goal_x = 89 if x_coord > 0 else -89
        goal_y = 0
        
        distance = ((x_coord - goal_x)**2 + (y_coord - goal_y)**2) ** 0.5
        angle = abs(np.arctan2(y_coord - goal_y, goal_x - x_coord) * 180 / np.pi)
        
        return {
            'game_id': game_id,
            'event_id': play.get('eventId'),
            'period': play.get('period', 1),
            'time_in_period': self._parse_time(play.get('timeInPeriod', '00:00')),
            'shot_type': details.get('shotType', 'Wrist'),
            'shot_distance': distance,
            'shot_angle': angle,
            'shooter_id': details.get('shootingPlayerId', 0),
            'goalie_id': details.get('goalieInNetId', 0),
            'is_goal': play['typeDescKey'] == 'goal',
            'event_type': play['typeDescKey'],
            'situation_code': play.get('situationCode', ''),
            'home_score': play.get('homeScore', 0),
            'away_score': play.get('awayScore', 0),
            'shooting_team': details.get('shootingTeamId'),
            'zone_code': details.get('zoneCode', ''),
            'assist1_id': details.get('assist1PlayerId'),
            'assist2_id': details.get('assist2PlayerId')
        }
    
    def _parse_time(self, time_str: str) -> int:
        """Convert MM:SS to seconds"""
        try:
            parts = time_str.split(':')
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return 0
    
    def _parse_situation(self, situation_code: str) -> Dict[str, bool]:
        """Parse situation code (e.g., '1551' = 5v5 at even strength)"""
        
        if not situation_code or len(situation_code) < 4:
            return {
                'is_powerplay': False,
                'is_penalty_kill': False,
                'is_empty_net': False
            }
        
        # Format: home_skaters|away_skaters|home_goalie|away_goalie
        home_skaters = int(situation_code[0])
        away_skaters = int(situation_code[1])
        home_goalie = int(situation_code[2])
        away_goalie = int(situation_code[3])
        
        return {
            'is_powerplay': home_skaters > away_skaters or away_skaters > home_skaters,
            'is_penalty_kill': home_skaters < away_skaters or away_skaters < home_skaters,
            'is_empty_net': home_goalie == 0 or away_goalie == 0
        }
    
    async def track_game_realtime(self, game_id: str, callback=None):
        """Track a game in real-time and calculate xG"""
        
        logger.info(f"Starting real-time tracking for game {game_id}")
        
        processed_events = set()
        game_xg = {'home': 0, 'away': 0, 'home_goals': 0, 'away_goals': 0}
        shot_log = []
        
        while True:
            try:
                # Get current plays
                plays = await self.get_game_plays(game_id)
                
                for play in plays:
                    event_id = play['event_id']
                    
                    if event_id not in processed_events:
                        processed_events.add(event_id)
                        
                        # Calculate xG for shot
                        xg_data = self.calculate_shot_xg(play)
                        
                        # Update totals
                        if play['shooting_team'] == 'home':
                            game_xg['home'] += xg_data['xg']
                            if play['is_goal']:
                                game_xg['home_goals'] += 1
                        else:
                            game_xg['away'] += xg_data['xg']
                            if play['is_goal']:
                                game_xg['away_goals'] += 1
                        
                        # Add to shot log
                        shot_log.append({
                            **play,
                            **xg_data,
                            'cumulative_xg_home': game_xg['home'],
                            'cumulative_xg_away': game_xg['away']
                        })
                        
                        # Callback for real-time updates
                        if callback:
                            callback(play, xg_data, game_xg)
                        
                        # Log interesting shots
                        if xg_data['xg'] > 0.3:
                            logger.info(f"High danger shot: {xg_data['xg']:.3f} xG - {xg_data['recommendation']}")
                
                # Check if game is final
                game_info = await self.get_game_status(game_id)
                if game_info.get('status') == 'Final':
                    logger.info(f"Game {game_id} finished. Final xG: Home {game_xg['home']:.2f} - Away {game_xg['away']:.2f}")
                    break
                
                # Wait before next update
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error tracking game: {e}")
                await asyncio.sleep(30)  # Wait longer on error
        
        return shot_log, game_xg
    
    def calculate_shot_xg(self, play: Dict) -> Dict:
        """Calculate xG for a shot play"""
        
        # Parse situation
        situation = self._parse_situation(play.get('situation_code', ''))
        
        # Determine score differential
        home_score = play.get('home_score', 0)
        away_score = play.get('away_score', 0)
        
        if play['shooting_team'] == 'home':
            score_differential = home_score - away_score
        else:
            score_differential = away_score - home_score
        
        # Create shot object
        shot = Shot(
            shot_distance=play['shot_distance'],
            shot_angle=play['shot_angle'],
            shot_type=play['shot_type'],
            period=play['period'],
            time_in_period=play['time_in_period'],
            score_differential=score_differential,
            shooter_id=play['shooter_id'],
            goalie_id=play['goalie_id'],
            is_powerplay=situation['is_powerplay'],
            is_penalty_kill=situation['is_penalty_kill'],
            is_empty_net=situation['is_empty_net'],
            assist1_id=play.get('assist1_id'),
            assist2_id=play.get('assist2_id')
        )
        
        # Get prediction
        try:
            prediction = self.xg_client.predict(shot)
            
            return {
                'xg': prediction.xg,
                'shot_value': prediction.shot_value,
                'should_shoot': prediction.should_shoot,
                'recommendation': prediction.recommendation,
                'fast_break_risk': prediction.fast_break_risk
            }
        except Exception as e:
            logger.error(f"Error calculating xG: {e}")
            # Fallback to simple calculation
            basic_xg = self._calculate_basic_xg(play['shot_distance'], play['shot_angle'])
            return {
                'xg': basic_xg,
                'shot_value': basic_xg,
                'should_shoot': basic_xg > 0.05,
                'recommendation': 'Basic calculation',
                'fast_break_risk': 0.02
            }
    
    def _calculate_basic_xg(self, distance: float, angle: float) -> float:
        """Basic xG calculation as fallback"""
        # Simple exponential decay model
        distance_factor = np.exp(-distance / 30)
        angle_factor = np.cos(np.radians(angle))
        return distance_factor * angle_factor * 0.15  # ~15% baseline
    
    async def get_game_status(self, game_id: str) -> Dict:
        """Get current game status"""
        games = await self.get_todays_games()
        for game in games:
            if game['game_id'] == game_id:
                return game
        return {}
    
    def generate_game_report(self, shot_log: List[Dict], game_xg: Dict) -> Dict:
        """Generate comprehensive game report"""
        
        df = pd.DataFrame(shot_log)
        
        report = {
            'summary': {
                'total_shots': len(df),
                'home_shots': len(df[df['shooting_team'] == 'home']),
                'away_shots': len(df[df['shooting_team'] == 'away']),
                'home_xg': game_xg['home'],
                'away_xg': game_xg['away'],
                'home_goals': game_xg['home_goals'],
                'away_goals': game_xg['away_goals'],
                'home_shooting_luck': game_xg['home_goals'] - game_xg['home'],
                'away_shooting_luck': game_xg['away_goals'] - game_xg['away']
            },
            'shot_quality': {
                'home_avg_xg': df[df['shooting_team'] == 'home']['xg'].mean(),
                'away_avg_xg': df[df['shooting_team'] == 'away']['xg'].mean(),
                'high_danger_shots': len(df[df['xg'] > 0.20]),
                'bad_shots': len(df[df['should_shoot'] == False])
            },
            'momentum': self._calculate_momentum_swings(df),
            'key_moments': self._identify_key_moments(df)
        }
        
        return report
    
    def _calculate_momentum_swings(self, df: pd.DataFrame) -> List[Dict]:
        """Identify momentum swings in the game"""
        
        swings = []
        
        # Calculate rolling xG differential
        df['xg_diff'] = df['cumulative_xg_home'] - df['cumulative_xg_away']
        
        # Find large swings
        for i in range(10, len(df)):
            recent_swing = df.iloc[i]['xg_diff'] - df.iloc[i-10]['xg_diff']
            
            if abs(recent_swing) > 0.5:  # 0.5 xG swing
                swings.append({
                    'time': f"Period {df.iloc[i]['period']} - {df.iloc[i]['time_in_period']//60}:{df.iloc[i]['time_in_period']%60:02d}",
                    'swing_magnitude': recent_swing,
                    'favors': 'home' if recent_swing > 0 else 'away'
                })
        
        return swings
    
    def _identify_key_moments(self, df: pd.DataFrame) -> List[Dict]:
        """Identify key moments in the game"""
        
        moments = []
        
        # High xG shots
        high_xg = df[df['xg'] > 0.3].head(5)
        for _, shot in high_xg.iterrows():
            moments.append({
                'type': 'high_danger_shot',
                'time': f"Period {shot['period']} - {shot['time_in_period']//60}:{shot['time_in_period']%60:02d}",
                'xg': shot['xg'],
                'result': 'GOAL' if shot['is_goal'] else 'SAVE',
                'team': shot['shooting_team']
            })
        
        # Bad shots that led to fast breaks
        risky_shots = df[df['fast_break_risk'] > 0.05].head(3)
        for _, shot in risky_shots.iterrows():
            moments.append({
                'type': 'risky_shot',
                'time': f"Period {shot['period']} - {shot['time_in_period']//60}:{shot['time_in_period']%60:02d}",
                'fast_break_risk': shot['fast_break_risk'],
                'recommendation': shot['recommendation'],
                'team': shot['shooting_team']
            })
        
        return moments

# Live game dashboard
class LiveGameDashboard:
    """Simple text-based dashboard for live xG tracking"""
    
    def __init__(self):
        self.current_game = None
        
    def update_display(self, play: Dict, xg_data: Dict, game_totals: Dict):
        """Update console display with latest data"""
        
        # Clear screen (works on most terminals)
        print("\033[2J\033[H")
        
        print("=" * 60)
        print("NHL LIVE xG TRACKER")
        print("=" * 60)
        
        # Score and xG
        print(f"\nHOME: {game_totals['home_goals']} goals ({game_totals['home']:.2f} xG)")
        print(f"AWAY: {game_totals['away_goals']} goals ({game_totals['away']:.2f} xG)")
        
        # Latest shot
        print(f"\n LATEST SHOT:")
        print(f"Team: {play['shooting_team'].upper()}")
        print(f"Type: {play['shot_type']}")
        print(f"Distance: {play['shot_distance']:.1f} ft")
        print(f"xG: {xg_data['xg']:.3f}")
        print(f"Recommendation: {xg_data['recommendation']}")
        
        if play['is_goal']:
            print(" GOAL!!!")
        
        # Shot quality indicator
        quality_bar = "█" * int(xg_data['xg'] * 20)
        print(f"\nShot Quality: [{quality_bar:<20}] {xg_data['xg']:.1%}")
        
        print("\n" + "=" * 60)

# Example usage
async def main():
    """Example: Track tonight's Penguins game"""
    
    tracker = NHLGameTracker()
    dashboard = LiveGameDashboard()
    
    # Get today's games
    games = await tracker.get_todays_games()
    
    # Find Penguins game
    pens_game = None
    for game in games:
        if 'PIT' in [game['home_team'], game['away_team']]:
            pens_game = game
            break
    
    if pens_game and pens_game['status'] in ['Live', 'Pre-Game']:
        print(f"Tracking {pens_game['away_team']} @ {pens_game['home_team']}")
        
        # Track game with live updates
        shot_log, final_xg = await tracker.track_game_realtime(
            pens_game['game_id'],
            callback=dashboard.update_display
        )
        
        # Generate final report
        report = tracker.generate_game_report(shot_log, final_xg)
        print("\nFINAL REPORT:")
        print(json.dumps(report, indent=2))
    else:
        print("No live Penguins game found")

if __name__ == "__main__":
    # Run real-time tracker
    asyncio.run(main())