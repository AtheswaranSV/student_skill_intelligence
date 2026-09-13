@echo off
cd backend
if not exist .venv python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
if not exist models\readiness.joblib python train_model.py
uvicorn app.main:app --reload
