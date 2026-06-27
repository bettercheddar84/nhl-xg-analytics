"""
Advanced xG Model API Service
Integrates all innovations: player embeddings, on-ice quality, shot decay, BABIP, fast break risk
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import torch
# import torch.nn as nn  # Unused import
import joblib
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NHL Advanced xG Model API", version="2.0")

class ShotRequest(BaseModel):
    """Input data for xG prediction"""
    
    # Required shot features
    shot_distance: float = Field(..., description="Distance from net in feet")
    shot_angle: float = Field(..., description="Angle from center in degrees")
    shot_type: str = Field(..., description="Wrist, Slap, Snap, Backhand, Tip-In, Deflection")
    period: int = Field(..., ge=1, le=4, description="Period (1-3, 4=OT)")
    time_in_period: int = Field(..., description="Seconds elapsed in period")
    
    # Game state
    score_differential: int = Field(..., description="Shooting team score - opponent score")
    is_powerplay: bool = Field(False, description="Power play situation")
    is_penalty_kill: bool = Field(False, description="Penalty kill situation")
    is_empty_net: bool = Field(False, description="Empty net situation")
    
    # Player IDs
    shooter_id: int = Field(..., description="Shooter player ID")
    goalie_id: int = Field(..., description="Goalie player ID")
    assist1_id: Optional[int] = Field(None, description="Primary assist player ID")
    assist2_id: Optional[int] = Field(None, description="Secondary assist player ID")
    
    # Advanced features
    offensive_zone_time: Optional[float] = Field(0, description="Seconds in offensive zone")
    is_rush: Optional[bool] = Field(False, description="Rush chance")
    is_rebound: Optional[bool] = Field(False, description="Rebound opportunity")
    royal_road_pass: Optional[bool] = Field(False, description="Cross-slot pass")
    
    # On-ice players (optional - will be inferred if not provided)
    offensive_players: Optional[List[int]] = Field(None, description="Offensive player IDs on ice")
    defensive_players: Optional[List[int]] = Field(None, description="Defensive player IDs on ice")

class XGResponse(BaseModel):
    """xG prediction response with detailed breakdown"""
    
    xg: float = Field(..., description="Expected goal probability (0-1)")
    shot_value: float = Field(..., description="Net shot value including fast break risk")
    confidence: float = Field(..., description="Model confidence (0-1)")
    
    # Component breakdowns
    components: Dict[str, float] = Field(..., description="xG component breakdown")
    adjustments: Dict[str, float] = Field(..., description="All adjustments applied")
    
    # Risk assessment
    fast_break_risk: float = Field(..., description="Probability of opponent fast break")
    rebound_potential: float = Field(..., description="Probability of rebound goal")
    
    # Strategic recommendation
    should_shoot: bool = Field(..., description="Whether shot is recommended")
    recommendation: str = Field(..., description="Strategic recommendation")

class ModelService:
    """Service class for xG predictions"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.player_encoders = None
        self.player_embeddings = None
        self.feature_names = None
        self.shot_decay_factors = None
        self.babip_data = None
        self.is_loaded = False
        
    def load_models(self):
        """Load all model artifacts"""
        try:
            logger.info("Loading model artifacts...")
            
            # Load neural network
            self.model = self._load_neural_model()
            
            # Load preprocessing artifacts
            self.scaler = joblib.load('models/production/neural_xg_scaler.pkl')
            self.player_encoders = joblib.load('models/production/neural_xg_encoders.pkl')
            
            # Load player embeddings
            with open('models/player_embeddings_combined.json', 'r') as f:
                self.player_embeddings = json.load(f)
            
            # Load feature configuration
            with open('models/production/neural_xg_config.pkl', 'rb') as f:
                self.config = joblib.load(f)
            
            # Load auxiliary data
            self._load_auxiliary_data()
            
            self.is_loaded = True
            logger.info("All models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    def _load_neural_model(self):
        """Load PyTorch neural network"""
        # Import model architecture
        from train.train_neural_xg_model import HierarchicalXGModel
        
        # Initialize model
        model = HierarchicalXGModel(
            input_dim=self.config['input_dim'],
            num_players=self.config['num_players'],
            embed_dim=self.config['embed_dim']
        )
        
        # Load weights
        model.load_state_dict(torch.load('models/production/neural_xg_final.pth'))
        model.eval()
        
        return model
    
    def _load_auxiliary_data(self):
        """Load supporting data for adjustments"""
        
        # Shot decay factors
        self.shot_decay_factors = {
            (0, 10): 1.0,
            (10, 20): 0.95,
            (20, 30): 0.90,
            (30, 45): 0.82,
            (45, 60): 0.78,
            (60, 120): 0.75
        }
        
        # BABIP data
        try:
            self.babip_data = pd.read_csv('data/nhl/processed/player_babip_stats.csv')
            self.league_babip = 0.30  # 30% of shots on net score
        except:
            self.babip_data = None
            self.league_babip = 0.30
    
    def calculate_on_ice_quality(self, shot_request: ShotRequest) -> Dict[str, float]:
        """Calculate on-ice quality differential"""
        
        # If players provided, calculate quality
        if shot_request.offensive_players and shot_request.defensive_players:
            # This would connect to the on-ice quality calculator
            # For now, return placeholder
            offensive_quality = 0.5 + np.random.normal(0, 0.1)
            defensive_quality = 0.5 + np.random.normal(0, 0.1)
        else:
            # Infer from shooter quality
            if shot_request.shooter_id and self.player_embeddings and shot_request.shooter_id in self.player_embeddings:
                offensive_quality = 0.6  # Above average shooter
            else:
                offensive_quality = 0.5
            defensive_quality = 0.5
        
        return {
            'offensive_quality': offensive_quality,
            'defensive_quality': defensive_quality,
            'quality_differential': offensive_quality - defensive_quality
        }
    
    def calculate_fast_break_risk(self, shot_request: ShotRequest) -> float:
        """Calculate probability of opponent fast break"""
        
        # Base risk factors
        distance_factor = min(shot_request.shot_distance / 60, 1.0)  # Normalize to 0-1
        angle_factor = min(abs(shot_request.shot_angle) / 90, 1.0)
        
        # Shot type risk
        risky_shots = ['Slap', 'Wrist']  # From distance
        shot_type_risk = 1.2 if shot_request.shot_type in risky_shots else 1.0
        
        # Situation modifiers
        if shot_request.is_powerplay:
            situation_risk = 0.8  # Less risk on PP
        elif shot_request.is_penalty_kill:
            situation_risk = 1.3  # More risk on PK
        else:
            situation_risk = 1.0
        
        # Calculate base risk
        base_risk = 0.021  # 2.1% average from analysis
        
        # Adjust for factors
        fast_break_risk = base_risk * distance_factor * angle_factor * shot_type_risk * situation_risk
        
        # Cap at reasonable maximum
        return min(fast_break_risk, 0.10)  # Max 10% risk
    
    def get_shot_decay_factor(self, zone_time: float) -> float:
        """Get shot quality decay factor based on zone time"""
        
        if self.shot_decay_factors:
            for (min_time, max_time), factor in self.shot_decay_factors.items():
                if min_time <= zone_time < max_time:
                    return factor
        return 0.75  # Default for very long zone time
    
    def get_babip_adjustment(self, shooter_id: int) -> float:
        """Get BABIP-based adjustment for shooter"""
        
        if self.babip_data is not None:
            player_babip = self.babip_data[self.babip_data['player_id'] == shooter_id]
            if not player_babip.empty:
                return player_babip.iloc[0]['babip_multiplier']
        
        return 1.0  # No adjustment if no data
    
    def prepare_features(self, shot_request: ShotRequest) -> tuple:
        """Prepare features for neural network"""
        
        # Create feature vector matching training features
        features = {
            'shot_distance': shot_request.shot_distance,
            'shot_angle': shot_request.shot_angle,
            'period': shot_request.period,
            'time_in_period': shot_request.time_in_period,
            'score_differential': shot_request.score_differential,
            'is_rebound': int(shot_request.is_rebound or False),
            'is_rush': int(shot_request.is_rush or False),
            'offensive_zone_time': shot_request.offensive_zone_time,
            'royal_road_pass': int(shot_request.royal_road_pass or False),
            # Add more features as needed
        }
        
        # One-hot encode shot type
        shot_types = ['Wrist', 'Slap', 'Snap', 'Backhand', 'Tip-In', 'Deflection']
        for st in shot_types:
            features[f'shot_type_{st}'] = int(shot_request.shot_type == st)
        
        # Add quality features
        quality = self.calculate_on_ice_quality(shot_request)
        features.update(quality)
        
        # Add decay factor
        decay_factor = self.get_shot_decay_factor(shot_request.offensive_zone_time or 0.0)
        features['quality_decay_factor'] = decay_factor
        
        # Add BABIP adjustment
        features['babip_multiplier'] = self.get_babip_adjustment(shot_request.shooter_id)
        
        # Create feature array
        feature_array = np.array([features.get(fn, 0) for fn in self.config['feature_names']])
        
        # Encode player IDs
        player_features = {}
        for player_type, player_id in [
            ('shooter', shot_request.shooter_id),
            ('goalie', shot_request.goalie_id),
            ('assist1', shot_request.assist1_id),
            ('assist2', shot_request.assist2_id)
        ]:
            if player_id and self.player_encoders and player_type in self.player_encoders:
                encoded_id = self.player_encoders[player_type].get(player_id, 0)
                player_features[player_type] = torch.LongTensor([encoded_id])
        
        # Create situation vector
        situations = torch.FloatTensor([[
            int(not (shot_request.is_powerplay or False) and not (shot_request.is_penalty_kill or False) and not (shot_request.is_empty_net or False)),
            int(shot_request.is_powerplay or False),
            int(shot_request.is_penalty_kill or False),
            int(shot_request.is_empty_net or False),
            0  # Other
        ]])
        
        return feature_array, player_features, situations, features
    
    def predict(self, shot_request: ShotRequest) -> XGResponse:
        """Generate xG prediction with all components"""
        
        if not self.is_loaded:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Prepare features
        feature_array, player_features, situations, raw_features = self.prepare_features(shot_request)
        
        # Scale features
        if self.scaler is not None:
            feature_scaled = self.scaler.transform(feature_array.reshape(1, -1))
        else:
            feature_scaled = feature_array.reshape(1, -1)
        
        # Get neural network prediction
        with torch.no_grad():
            feature_tensor = torch.FloatTensor(feature_scaled)
            if self.model is not None:
                xg_base = self.model(feature_tensor, player_features, situations).item()
            else:
                xg_base = 0.1  # Default fallback
        
        # Calculate components
        components = {
            'base_xg': xg_base,
            'location_danger': self._calculate_location_danger(shot_request),
            'shot_type_modifier': self._get_shot_type_modifier(shot_request.shot_type),
            'decay_adjustment': raw_features['quality_decay_factor'],
            'babip_adjustment': raw_features['babip_multiplier'],
            'quality_differential': raw_features['quality_differential']
        }
        
        # Apply adjustments
        adjustments = {
            'zone_time_decay': (raw_features['quality_decay_factor'] - 1.0) * xg_base,
            'shooter_babip': (raw_features['babip_multiplier'] - 1.0) * xg_base,
            'on_ice_quality': raw_features['quality_differential'] * 0.05,  # 5% per 0.1 differential
        }
        
        # Final xG with all adjustments
        final_xg = xg_base + sum(adjustments.values())
        final_xg = np.clip(final_xg, 0.001, 0.999)
        
        # Calculate shot value including fast break risk
        fast_break_risk = self.calculate_fast_break_risk(shot_request)
        rebound_potential = final_xg * 0.15 if shot_request.shot_distance < 20 else final_xg * 0.05
        
        shot_value = final_xg + rebound_potential - fast_break_risk
        
        # Strategic recommendation
        should_shoot = shot_value > 0.02  # 2% threshold
        
        if not should_shoot:
            if shot_request.shot_distance > 45:
                recommendation = "Keep possession - Too far, likely to miss high/wide"
            elif abs(shot_request.shot_angle) > 50:
                recommendation = "Cycle puck - Bad angle, high miss probability"
            else:
                recommendation = "Work for better shot - Maintain possession"
        else:
            if final_xg > 0.15:
                recommendation = "Shoot - High danger, focus on hitting net"
            elif shot_request.is_rebound:
                recommendation = "Shoot - Quick release on net"
            elif shot_request.shot_distance < 25:
                recommendation = "Shoot - Close range, hit the net"
            else:
                recommendation = "Shoot - Good opportunity, accuracy over power"
        
        # Model confidence based on data availability
        confidence = 0.9
        if not (shot_request.shooter_id and self.player_embeddings and shot_request.shooter_id in self.player_embeddings):
            confidence -= 0.1
        if not shot_request.offensive_players:
            confidence -= 0.1
        
        return XGResponse(
            xg=round(final_xg, 4),
            shot_value=round(shot_value, 4),
            confidence=round(confidence, 2),
            components=components,
            adjustments=adjustments,
            fast_break_risk=round(fast_break_risk, 4),
            rebound_potential=round(rebound_potential, 4),
            should_shoot=should_shoot,
            recommendation=recommendation
        )
    
    def _calculate_location_danger(self, shot_request: ShotRequest) -> float:
        """Calculate base danger from location"""
        
        # Simple danger model
        distance_danger = np.exp(-shot_request.shot_distance / 30)
        angle_danger = np.cos(np.radians(shot_request.shot_angle))
        
        return distance_danger * angle_danger
    
    def _get_shot_type_modifier(self, shot_type: str) -> float:
        """Get shot type effectiveness modifier"""
        
        modifiers = {
            'Wrist': 1.0,
            'Snap': 1.1,
            'Slap': 0.9,
            'Backhand': 1.2,
            'Tip-In': 1.5,
            'Deflection': 1.3
        }
        
        return modifiers.get(shot_type, 1.0)

# Initialize model service
model_service = ModelService()

@app.on_event("startup")
async def startup_event():
    """Load models on startup"""
    model_service.load_models()

@app.get("/")
def read_root():
    """API information"""
    return {
        "name": "NHL Advanced xG Model API",
        "version": "2.0",
        "features": [
            "Neural network with player embeddings",
            "On-ice quality differentials", 
            "Shot value decay",
            "BABIP adjustments",
            "Fast break risk assessment",
            "Strategic recommendations"
        ],
        "endpoints": {
            "/predict": "Single shot xG prediction",
            "/batch": "Batch predictions",
            "/health": "Service health check"
        }
    }

@app.get("/health")
def health_check():
    """Service health check"""
    return {
        "status": "healthy" if model_service.is_loaded else "not ready",
        "model_loaded": model_service.is_loaded,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/predict", response_model=XGResponse)
def predict_single(shot_request: ShotRequest):
    """Predict xG for a single shot"""
    
    try:
        prediction = model_service.predict(shot_request)
        return prediction
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch")
def predict_batch(shots: List[ShotRequest]):
    """Predict xG for multiple shots"""
    
    results = []
    for shot in shots:
        try:
            prediction = model_service.predict(shot)
            results.append(prediction.dict())
        except Exception as e:
            results.append({"error": str(e)})
    
    return {"predictions": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)