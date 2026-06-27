"""
Client SDK for NHL Advanced xG Model API
Easy integration for applications
"""

import requests
from typing import List, Dict, Optional, Union
import pandas as pd
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Shot:
    """Shot data structure"""
    # Required fields
    shot_distance: float
    shot_angle: float
    shot_type: str
    period: int
    time_in_period: int
    score_differential: int
    shooter_id: int
    goalie_id: int
    
    # Optional fields
    is_powerplay: bool = False
    is_penalty_kill: bool = False
    is_empty_net: bool = False
    assist1_id: Optional[int] = None
    assist2_id: Optional[int] = None
    offensive_zone_time: float = 0
    is_rush: bool = False
    is_rebound: bool = False
    royal_road_pass: bool = False
    offensive_players: Optional[List[int]] = None
    defensive_players: Optional[List[int]] = None

@dataclass
class XGPrediction:
    """xG prediction result"""
    xg: float
    shot_value: float
    confidence: float
    should_shoot: bool
    recommendation: str
    fast_break_risk: float
    rebound_potential: float
    components: Dict[str, float]
    adjustments: Dict[str, float]

class XGModelClient:
    """Client for xG Model API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def health_check(self) -> Dict:
        """Check if service is healthy"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def predict(self, shot: Union[Shot, Dict]) -> XGPrediction:
        """Get xG prediction for a single shot"""
        
        # Convert Shot object to dict if needed
        if isinstance(shot, Shot):
            shot_data = {
                k: v for k, v in shot.__dict__.items() 
                if v is not None
            }
        else:
            shot_data = shot
        
        response = self.session.post(
            f"{self.base_url}/predict",
            json=shot_data
        )
        response.raise_for_status()
        
        result = response.json()
        return XGPrediction(**result)
    
    def predict_batch(self, shots: List[Union[Shot, Dict]]) -> List[XGPrediction]:
        """Get predictions for multiple shots"""
        
        # Convert Shot objects to dicts
        shots_data = []
        for shot in shots:
            if isinstance(shot, Shot):
                shot_dict = {
                    k: v for k, v in shot.__dict__.items() 
                    if v is not None
                }
                shots_data.append(shot_dict)
            else:
                shots_data.append(shot)
        
        response = self.session.post(
            f"{self.base_url}/batch",
            json=shots_data
        )
        response.raise_for_status()
        
        results = response.json()["predictions"]
        predictions = []
        
        for result in results:
            if "error" not in result:
                predictions.append(XGPrediction(**result))
            else:
                logger.error(f"Prediction error: {result['error']}")
                predictions.append(None)
        
        return predictions
    
    def predict_from_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add xG predictions to a dataframe"""
        
        # Required columns
        required = ['shot_distance', 'shot_angle', 'shot_type', 'period', 
                   'time_in_period', 'score_differential', 'shooter_id', 'goalie_id']
        
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Convert dataframe to shot objects
        shots = []
        for _, row in df.iterrows():
            shot_data = {col: row[col] for col in required}
            
            # Add optional fields if present
            optional = ['is_powerplay', 'is_penalty_kill', 'is_empty_net', 
                       'assist1_id', 'assist2_id', 'offensive_zone_time',
                       'is_rush', 'is_rebound', 'royal_road_pass']
            
            for col in optional:
                if col in df.columns and pd.notna(row[col]):
                    shot_data[col] = row[col]
            
            shots.append(shot_data)
        
        # Get predictions
        predictions = self.predict_batch(shots)
        
        # Add to dataframe
        df = df.copy()
        df['xg'] = [p.xg if p else np.nan for p in predictions]
        df['shot_value'] = [p.shot_value if p else np.nan for p in predictions]
        df['should_shoot'] = [p.should_shoot if p else np.nan for p in predictions]
        df['recommendation'] = [p.recommendation if p else '' for p in predictions]
        df['fast_break_risk'] = [p.fast_break_risk if p else np.nan for p in predictions]
        
        return df
    
    def analyze_game(self, game_shots_df: pd.DataFrame) -> Dict:
        """Analyze all shots from a game"""
        
        # Add predictions
        df_with_xg = self.predict_from_dataframe(game_shots_df)
        
        # Calculate team statistics
        teams = df_with_xg['shooting_team'].unique()
        
        analysis = {}
        for team in teams:
            team_shots = df_with_xg[df_with_xg['shooting_team'] == team]
            opp_shots = df_with_xg[df_with_xg['shooting_team'] != team]
            
            analysis[team] = {
                'shots': len(team_shots),
                'goals': team_shots['is_goal'].sum(),
                'expected_goals': team_shots['xg'].sum(),
                'goals_above_expected': team_shots['is_goal'].sum() - team_shots['xg'].sum(),
                'avg_shot_quality': team_shots['xg'].mean(),
                'bad_shots': (team_shots['shot_value'] < 0).sum(),
                'fast_break_risk_created': team_shots['fast_break_risk'].sum(),
                'shooting_recommendations': {
                    'should_have_shot': (team_shots['should_shoot'] == True).sum(),
                    'should_have_passed': (team_shots['should_shoot'] == False).sum()
                }
            }
        
        return analysis
    
    def get_player_report(self, player_id: int, shots_df: pd.DataFrame) -> Dict:
        """Generate shooting report for a player"""
        
        # Filter player shots
        player_shots = shots_df[shots_df['shooter_id'] == player_id].copy()
        
        if player_shots.empty:
            return {"error": "No shots found for player"}
        
        # Add predictions
        player_shots = self.predict_from_dataframe(player_shots)
        
        report = {
            'player_id': player_id,
            'total_shots': len(player_shots),
            'goals': player_shots['is_goal'].sum(),
            'shooting_percentage': player_shots['is_goal'].mean(),
            'expected_goals': player_shots['xg'].sum(),
            'goals_above_expected': player_shots['is_goal'].sum() - player_shots['xg'].sum(),
            'avg_shot_quality': player_shots['xg'].mean(),
            'avg_shot_distance': player_shots['shot_distance'].mean(),
            'shot_selection': {
                'good_shots': (player_shots['should_shoot'] == True).sum(),
                'bad_shots': (player_shots['should_shoot'] == False).sum(),
                'bad_shot_percentage': (player_shots['should_shoot'] == False).mean()
            },
            'fast_break_risk': player_shots['fast_break_risk'].mean(),
            'recommendations': player_shots['recommendation'].value_counts().to_dict()
        }
        
        return report

# Convenience functions
def quick_predict(shot_distance: float, shot_angle: float, shot_type: str = "Wrist",
                 shooter_id: int = 0, goalie_id: int = 0, **kwargs) -> float:
    """Quick xG prediction with minimal inputs"""
    
    client = XGModelClient()
    
    shot = Shot(
        shot_distance=shot_distance,
        shot_angle=shot_angle,
        shot_type=shot_type,
        period=kwargs.get('period', 2),
        time_in_period=kwargs.get('time_in_period', 600),
        score_differential=kwargs.get('score_differential', 0),
        shooter_id=shooter_id,
        goalie_id=goalie_id,
        **{k: v for k, v in kwargs.items() if k not in ['period', 'time_in_period', 'score_differential']}
    )
    
    prediction = client.predict(shot)
    return prediction.xg

def evaluate_shot_decision(shot_distance: float, shot_angle: float, 
                          shot_type: str = "Wrist", **kwargs) -> str:
    """Get strategic recommendation for a shot"""
    
    client = XGModelClient()
    
    shot = Shot(
        shot_distance=shot_distance,
        shot_angle=shot_angle,
        shot_type=shot_type,
        period=kwargs.get('period', 2),
        time_in_period=kwargs.get('time_in_period', 600),
        score_differential=kwargs.get('score_differential', 0),
        shooter_id=kwargs.get('shooter_id', 0),
        goalie_id=kwargs.get('goalie_id', 0),
        **{k: v for k, v in kwargs.items() if k not in ['period', 'time_in_period', 'score_differential', 'shooter_id', 'goalie_id']}
    )
    
    prediction = client.predict(shot)
    
    return f"{'SHOOT' if prediction.should_shoot else 'PASS'}: {prediction.recommendation}"

# Example usage
if __name__ == "__main__":
    # Initialize client
    client = XGModelClient()
    
    # Check health
    print("Service health:", client.health_check())
    
    # Example 1: Single shot prediction
    shot = Shot(
        shot_distance=15,
        shot_angle=20,
        shot_type="Wrist",
        period=2,
        time_in_period=600,
        score_differential=0,
        shooter_id=8478402,  # Connor McDavid
        goalie_id=8476883,   # Andrei Vasilevskiy
        is_rush=True,
        offensive_zone_time=5
    )
    
    prediction = client.predict(shot)
    print(f"\nxG: {prediction.xg:.3f}")
    print(f"Should shoot: {prediction.should_shoot}")
    print(f"Recommendation: {prediction.recommendation}")
    
    # Example 2: Quick prediction
    xg = quick_predict(shot_distance=45, shot_angle=30, shot_type="Slap")
    print(f"\nQuick prediction: {xg:.3f}")
    
    # Example 3: Shot decision
    decision = evaluate_shot_decision(shot_distance=50, shot_angle=45)
    print(f"\nShot decision: {decision}")