# NHL Expected Goals (xG) Analytics

A machine-learning system for predicting **Expected Goals (xG)** in NHL hockey — pairing a Python/FastAPI modeling backend with a Vue 3 visualization frontend. Originally built as a hockey analytics R&D project centered on the Pittsburgh Penguins.

> **xG (Expected Goals)** estimates the probability that a given shot becomes a goal, based on its context — location, angle, shot type, rebounds, rushes, pre-shot passing, goalie workload, and game state.

---

## Repository structure

```
nhl-xg-analytics/
├── backend/      Python · FastAPI · XGBoost xG model, training scripts, feature engineering
└── frontend/     Vue 3 · TypeScript · Vite — interactive rink + shot visualizations
```

Each side has its own README with deeper detail:
- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)

---

## What it does

- **xG model** — predicts shot-success probability from NHL play-by-play data
- **Feature engineering** — shot distance/angle, rebounds, rush quality, royal-road passes, on-ice quality differentials, goalie fatigue/workload, momentum, and pre-shot passing sequences
- **REST API** — FastAPI service for real-time predictions
- **Rink visualization** — Vue frontend rendering shot locations and heatmaps on an NHL rink

## Tech stack

| Layer | Tools |
|-------|-------|
| Modeling | Python, XGBoost, scikit-learn, pandas, numpy |
| API | FastAPI |
| Frontend | Vue 3, TypeScript, Vite |
| Data source | [NHL public API](https://api-web.nhle.com/v1/) |

---

## Getting started

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Note on data & models

Raw datasets, processed CSVs, and trained model binaries (`.pkl`) are **not** included in this repository — they are large and are regenerated from the NHL API via the scripts in [backend/scripts/](backend/scripts/) and [backend/train/](backend/train/). See [backend/training_docs/](backend/training_docs/) for the data dictionary and feature documentation.

## License

Released under the [MIT License](LICENSE).
