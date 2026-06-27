from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np
import asyncio
import aiohttp
from autogluon.tabular import TabularPredictor

app = FastAPI(
    title="Pittsburgh Penguins AI - Expected Goals API",
    description="Hockey analytics API for shot quality prediction",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model
model = None
features = None
model_info = None


# Load model on startup
def load_model():
    global model, features, model_info
    try:
        model = TabularPredictor.load("models/autogluon/")
        features = model.feature_metadata_in.get_features()

        # Get model performance from leaderboard
        leaderboard = model.leaderboard(silent=True)
        best_model_performance = leaderboard.iloc[0]

        model_info = {
            "features": features,
            "training_samples": "N/A",  # AutoGluon doesn't expose train_data
            "accuracy": float(best_model_performance.get("accuracy", 0.85)),
            "auc": float(best_model_performance.get("roc_auc", 0.85)),
            "best_model": best_model_performance.get("model", "Unknown"),
        }
        print("✓ AutoGluon model loaded successfully")
        print(f"  Best model: {model_info['best_model']}")
        print(f"  AUC: {model_info['auc']:.3f}")
    except Exception as e:
        print(f"⚠ Model not loaded: {str(e)}")
        print("Run train/train_autogluon.py first!")


# Load model when server starts
load_model()


# Request/Response models
class ShotData(BaseModel):
    # Match your actual feature names from the CSV
    shot_distance: float
    shot_angle: float
    x_coord: float
    y_coord: float

    # Shot characteristics
    shot_type: str = "wrist"
    is_rebound: int = 0
    is_rush: int = 0
    is_one_timer: int = 0
    speed_from_prev: float = 10.0
    time_since_prev_event: float = 5.0
    distance_from_prev_event: float = 0.0

    # Player IDs (for future player quality metrics)
    shooter_id: Optional[float] = None
    goalie_id: Optional[float] = None

    # Game state
    home_skaters: int = 5
    away_skaters: int = 5
    period: int = 2
    time_remaining: int = 1200
    home_score: int = 0
    away_score: int = 0
    score_differential: int = 0
    is_home_team: int = 1
    is_powerplay: int = 0
    is_shorthanded: int = 0
    empty_net: int = 0

    # Pre-shot context
    prev_event_type: str = "hit"
    prev_event_x: Optional[float] = None
    prev_event_y: Optional[float] = None
    time_since_faceoff: float = 30.0
    is_off_zone_faceoff: int = 0

    # Additional fields from your data
    zone_code: str = "O"
    is_penalty_shot: int = 0
    is_backhand: int = 0
    is_deflection: int = 0
    is_wraparound: int = 0
    playoff_game: int = 0
    strength_state: str = "1551"


class PredictionResponse(BaseModel):
    expected_goals: float
    shot_quality: str
    danger_zone: str
    percentile: float
    recommendation: str
    key_factors: list[str]
    shot_location: dict
    distance: float
    angle: float


async def fetch_game_data(game_id: str):
    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


def calculate_time_since_last_faceoff(play, pbp_data):
    for i in range(pbp_data["plays"].index(play) - 1, -1, -1):
        if pbp_data["plays"][i]["typeDescKey"] == "faceoff":
            return play["timeInPeriod"] - pbp_data["plays"][i]["timeInPeriod"]
    return 30.0


@app.websocket("/ws/game/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: str):
    await websocket.accept()

    while True:
        try:
            pbp_data = await fetch_game_data(game_id)

            for play in pbp_data.get("plays", []):
                if play.get("typeDescKey") == "shot-on-goal":
                    # Map API data to model features
                    shot_data = {
                        "shot_distance": play.get("details", {}).get("distance", 30),
                        "shot_angle": play.get("details", {}).get("angle", 0),
                        "x_coord": play.get("details", {}).get("xCoord", 0),
                        "y_coord": play.get("details", {}).get("yCoord", 0),
                        "shot_type": play.get("details", {}).get("shotType", "wrist").lower(),
                        "period": play.get("period", 2),
                        "time_remaining": play.get("timeRemaining", 1200),
                        # Add other features with defaults
                    }

                    shot_df = pd.DataFrame([shot_data])
                    if model is not None:
                        proba_result = model.predict_proba(shot_df)
                        # Handle both DataFrame and ndarray returns
                        if isinstance(proba_result, pd.DataFrame):
                            # Get the value and ensure it's a float
                            val = proba_result.iloc[0, 0]
                            if isinstance(val, (int, float)):
                                xg_probability = float(val)
                            else:
                                xg_probability = 0.1
                        elif isinstance(proba_result, np.ndarray):
                            xg_probability = float(proba_result[0])
                        else:
                            xg_probability = 0.1
                    else:
                        xg_probability = 0.1

                    await websocket.send_json(
                        {
                            "event": "shot",
                            "xG": xg_probability,
                            "location": {"x": shot_data["x_coord"], "y": shot_data["y_coord"]},
                            "shooter": play.get("playerId"),
                            "time": play.get("timeInPeriod"),
                        }
                    )

            await asyncio.sleep(5)

        except Exception as e:
            print(f"WebSocket error: {e}")
            await websocket.send_json({"error": str(e)})


@app.get("/")
def root():
    return {
        "message": "Pittsburgh Penguins AI - Expected Goals API",
        "status": "active" if model is not None else "model not loaded",
        "endpoints": {
            "POST /predict/expected-goals": "Predict xG for a shot",
            "GET /model/info": "Get model information",
            "GET /health": "Check API health",
            "WS /ws/game/{game_id}": "Real-time game tracking",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": model is not None}


@app.post("/predict/expected-goals", response_model=PredictionResponse)
def predict_xg(shot: ShotData):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Create dataframe from shot data
        shot_df = pd.DataFrame([shot.dict()])

        # AutoGluon handles preprocessing internally
        proba_result = model.predict_proba(shot_df)

        # Handle both DataFrame and ndarray returns
        if isinstance(proba_result, pd.DataFrame):
            # Get the value and ensure it's a float
            val = proba_result.iloc[0, 0]
            if isinstance(val, (int, float)):
                xg_probability = float(val)
            else:
                xg_probability = 0.1
        elif isinstance(proba_result, np.ndarray):
            xg_probability = float(proba_result[0])
        else:
            xg_probability = 0.1

        # Calculate percentile (simplified)
        percentile = min(99, max(1, xg_probability * 100 * 2.5))

        # Determine shot quality
        if xg_probability > 0.20:
            quality = "Excellent"
            recommendation = "High-danger chance! This shot location/type should be prioritized."
            danger = "High"
        elif xg_probability > 0.12:
            quality = "Good"
            recommendation = "Quality scoring chance. Continue creating these opportunities."
            danger = "High"
        elif xg_probability > 0.08:
            quality = "Average"
            recommendation = "Decent shot, but look for better positioning if possible."
            danger = "Medium"
        else:
            quality = "Poor"
            recommendation = "Low-percentage shot. Consider passing or improving position."
            danger = "Low"

        # Get feature importance if available
        try:
            importance = model.feature_importance()
            if isinstance(importance, pd.DataFrame):
                top_factors = importance.nlargest(3, columns="importance").index.tolist()
            else:
                top_factors = ["shot_distance", "shot_angle", "shot_type"]
        except Exception:
            top_factors = ["shot_distance", "shot_angle", "shot_type"]

        return PredictionResponse(
            expected_goals=round(xg_probability, 4),
            shot_quality=quality,
            danger_zone=danger,
            percentile=round(percentile, 1),
            recommendation=recommendation,
            key_factors=top_factors,
            shot_location={"x": shot.x_coord, "y": shot.y_coord},
            distance=shot.shot_distance,
            angle=shot.shot_angle,
        )

    except Exception as e:
        print(f"Error details: {str(e)}")
        print(f"Shot data columns: {shot_df.columns.tolist()}")
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")


@app.get("/model/info")
def get_model_info():
    if model_info is None:
        return {"status": "No model loaded"}

    return {
        "model_type": model_info.get("best_model", "AutoGluon Ensemble"),
        "accuracy": round(model_info["accuracy"], 3),
        "auc_score": round(model_info["auc"], 3),
        "n_features": len(model_info["features"]),
        "training_samples": model_info["training_samples"],
        "features": model_info["features"][:20],  # Show first 20 features
        "feature_categories": {
            "spatial": ["shot_distance", "shot_angle", "x_coord", "y_coord"],
            "shot_info": ["shot_type", "is_rebound", "is_rush", "is_one_timer"],
            "game_state": ["period", "score_differential", "is_powerplay"],
        },
    }


@app.post("/predict/batch")
def predict_batch(shots: list[ShotData]):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Create dataframe from all shots
    shots_df = pd.DataFrame([shot.dict() for shot in shots])

    # Get predictions
    proba_result = model.predict_proba(shots_df)

    # Handle both DataFrame and ndarray returns
    if isinstance(proba_result, pd.DataFrame):
        xg_probabilities = proba_result.iloc[:, 0].values
    else:
        xg_probabilities = proba_result

    predictions = []
    for shot, xg_prob in zip(shots, xg_probabilities):
        # Reuse the single prediction logic
        pred_response = predict_xg(shot)
        predictions.append(pred_response)

    return {
        "predictions": predictions,
        "average_xg": round(float(np.array(xg_probabilities).mean()), 4),
        "total_xg": round(float(np.array(xg_probabilities).sum()), 2),
        "shots_count": len(shots),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
