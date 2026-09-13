from pathlib import Path
import joblib, numpy as np
MODEL=Path(__file__).resolve().parents[1]/'models'/'readiness.joblib'
def predict(features):
 if MODEL.exists():
  m=joblib.load(MODEL); probs=m.predict_proba([features])[0]; classes=list(m.classes_); i=int(np.argmax(probs)); return {"label":classes[i],"confidence":round(float(probs[i])*100,1)}
 score=round(sum(features)/len(features)); label='Industry Ready' if score>=80 else 'Nearly Ready' if score>=60 else 'Needs Improvement'; return {"label":label,"confidence":score}
