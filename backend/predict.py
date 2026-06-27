"""
Standalone Expected Goals (xG) predictor.

Loads the lightweight trained XGBoost model (models/production/xg_model_nhl.pkl)
and scores individual shots — no server, no database, no GPU required.

Run from the `backend/` directory:

    pip install -r requirements.txt        # or: pip install xgboost scikit-learn pandas joblib
    python predict.py                      # scores the built-in example shots

Or import and call predict_xg(...) from your own code.
"""

from pathlib import Path

import joblib
import pandas as pd

MODEL_DIR = Path(__file__).parent / "models" / "production"
MODEL_PATH = MODEL_DIR / "xg_model_nhl.pkl"
FEATURES_PATH = MODEL_DIR / "features.txt"

# Valid one-hot categories the model was trained on
SHOT_TYPES = ["BACK", "DEFL", "SLAP", "SNAP", "TIP", "WRAP", "WRIST"]
LAST_EVENTS = [
    "BLOCK", "CHL", "DELPEN", "FAC", "GIVE", "GOAL",
    "HIT", "MISS", "PENL", "SHOT", "STOP", "TAKE",
]

# League-average / neutral defaults for every model feature.
# Player-quality talent features default to neutral so a shot can be scored
# without per-player lookups; override any of them via predict_xg(**kwargs).
DEFAULTS = {
    "arenaAdjustedShotDistance": 35.0,
    "shotAngleAdjusted": 25.0,
    "arenaAdjustedXCordABS": 55.0,
    "arenaAdjustedYCordAbs": 10.0,
    "shooting_talent": 1.0,          # goals / xGoals ~ 1.0 for a league-average shooter
    "high_danger_conversion": 0.20,
    "shot_quality_ratio": 0.15,
    "save_talent": 0.0,              # neutral goalie
    "high_danger_save_talent": 0.0,
    "shotRebound": 0,
    "shotRush": 0,
    "shotWasOnGoal": 1,
    "speedFromLastEvent": 0.0,
    "timeSinceLastEvent": 5.0,
    "homeSkatersOnIce": 5,
    "awaySkatersOnIce": 5,
    "period": 1,
    "timeLeft": 600,
    "awayTeamGoals": 0,
    "homeTeamGoals": 0,
    "score_differential": 0,
    "is_home_shooting": 1,
    "strength_differential": 0,
}

_model = None
_feature_order = None


def _load():
    global _model, _feature_order
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. It ships with the repo — "
                "make sure you're running from the backend/ directory."
            )
        _model = joblib.load(MODEL_PATH)
        # Model was trained on GPU; force CPU for portable inference.
        try:
            _model.get_booster().set_param({"device": "cpu"})
        except Exception:
            pass
        _feature_order = FEATURES_PATH.read_text().split()
    return _model, _feature_order


def predict_xg(shot_type="WRIST", last_event="SHOT", **overrides):
    """Return the Expected Goals (probability 0-1) for a single shot.

    Pass any feature in DEFAULTS as a keyword to override it, e.g.:
        predict_xg(arenaAdjustedShotDistance=8, shotAngleAdjusted=5, shotRebound=1)
    """
    model, feature_order = _load()

    row = dict(DEFAULTS)
    row.update(overrides)

    # One-hot encode shot type and last event
    for st in SHOT_TYPES:
        row[f"shotType_{st}"] = 1 if st == shot_type.upper() else 0
    for ev in LAST_EVENTS:
        row[f"lastEvent_{ev}"] = 1 if ev == last_event.upper() else 0

    # Keep score_differential / strength_differential consistent if user set goals/skaters
    row["score_differential"] = row["homeTeamGoals"] - row["awayTeamGoals"]
    row["strength_differential"] = row["homeSkatersOnIce"] - row["awaySkatersOnIce"]

    X = pd.DataFrame([[row.get(f, 0) for f in feature_order]], columns=feature_order)
    return float(model.predict_proba(X)[:, 1][0])


if __name__ == "__main__":
    examples = [
        ("Slot one-timer off a rebound (high danger)",
         dict(shot_type="WRIST", last_event="SHOT",
              arenaAdjustedShotDistance=8, shotAngleAdjusted=5,
              arenaAdjustedXCordABS=82, arenaAdjustedYCordAbs=3,
              shotRebound=1, shotWasOnGoal=1)),
        ("Point slap shot from the blue line (low danger)",
         dict(shot_type="SLAP", last_event="SHOT",
              arenaAdjustedShotDistance=60, shotAngleAdjusted=15,
              arenaAdjustedXCordABS=30, arenaAdjustedYCordAbs=20,
              shotWasOnGoal=1)),
        ("Sharp-angle wrister, off the rush",
         dict(shot_type="WRIST", last_event="TAKE",
              arenaAdjustedShotDistance=30, shotAngleAdjusted=55,
              arenaAdjustedXCordABS=70, arenaAdjustedYCordAbs=30,
              shotRush=1, shotWasOnGoal=1)),
    ]

    print("\nNHL Expected Goals (xG) — sample predictions")
    print("=" * 52)
    for label, shot in examples:
        xg = predict_xg(**shot)
        print(f"{xg * 100:5.1f}% xG   {label}")
    print("=" * 52)
    print("Override any feature: predict_xg(arenaAdjustedShotDistance=8, shotRebound=1)\n")
