"""
Lightweight FastAPI server for the bundled Expected Goals (xG) model.

Serves the ~1 MB XGBoost model (via predict.py) over HTTP — no GPU, no big
AutoGluon download. This is the easy way to call the model from the frontend
or any client.

Run from the `backend/` directory:

    pip install -r requirements.txt
    uvicorn serve:app --reload

Then open http://127.0.0.1:8000/docs for interactive API docs, or:

    curl -X POST http://127.0.0.1:8000/predict \
         -H "Content-Type: application/json" \
         -d '{"arenaAdjustedShotDistance": 8, "shotAngleAdjusted": 5, "shotRebound": 1}'
"""

from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from predict import DEFAULTS, LAST_EVENTS, SHOT_TYPES, predict_xg

app = FastAPI(
    title="NHL Expected Goals (xG) API",
    description="Predict shot-success probability with the bundled XGBoost model.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Shot(BaseModel):
    """A single shot. Every field is optional and falls back to a league-average
    default, so you can send as little or as much context as you have."""

    shot_type: str = Field("WRIST", description=f"One of {SHOT_TYPES}")
    last_event: str = Field("SHOT", description=f"One of {LAST_EVENTS}")

    arenaAdjustedShotDistance: Optional[float] = Field(None, description="Feet from net")
    shotAngleAdjusted: Optional[float] = Field(None, description="Angle in degrees")
    arenaAdjustedXCordABS: Optional[float] = None
    arenaAdjustedYCordAbs: Optional[float] = None
    shotRebound: Optional[int] = Field(None, description="1 if shot followed a recent shot")
    shotRush: Optional[int] = Field(None, description="1 if shot came off the rush")
    shotWasOnGoal: Optional[int] = None
    homeSkatersOnIce: Optional[int] = None
    awaySkatersOnIce: Optional[int] = None
    period: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "shot_type": "WRIST",
                "last_event": "SHOT",
                "arenaAdjustedShotDistance": 8,
                "shotAngleAdjusted": 5,
                "shotRebound": 1,
            }
        }
    }


@app.get("/")
def health():
    return {"status": "ok", "model": "xg_model_nhl (XGBoost)", "docs": "/docs"}


@app.get("/features")
def features():
    """List every model feature and its default value."""
    return {"n_features": len(DEFAULTS) + len(SHOT_TYPES) + len(LAST_EVENTS),
            "tunable_defaults": DEFAULTS,
            "shot_types": SHOT_TYPES,
            "last_events": LAST_EVENTS}


@app.post("/predict")
def predict(shot: Shot):
    """Return the Expected Goals probability for a shot."""
    overrides = {k: v for k, v in shot.model_dump().items()
                 if v is not None and k not in ("shot_type", "last_event")}
    xg = predict_xg(shot_type=shot.shot_type, last_event=shot.last_event, **overrides)
    return {
        "xg": round(xg, 4),
        "xg_pct": f"{xg * 100:.1f}%",
        "inputs": shot.model_dump(),
    }
