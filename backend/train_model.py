from pathlib import Path
import numpy as np, joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
rng=np.random.default_rng(42); X=rng.integers(20,101,size=(2400,6)); avg=X[:,0]*.35+X[:,1]*.10+X[:,2]*.20+X[:,3]*.15+X[:,4]*.15+X[:,5]*.05
y=np.where(avg>=78,'Industry Ready',np.where(avg>=58,'Nearly Ready','Needs Improvement'))
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,random_state=42,stratify=y)
m=RandomForestClassifier(n_estimators=250,random_state=42,class_weight='balanced').fit(Xtr,ytr)
print(classification_report(yte,m.predict(Xte))); p=Path('models/readiness.joblib'); p.parent.mkdir(exist_ok=True); joblib.dump(m,p); print('saved',p)
