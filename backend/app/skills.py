import re
from .careers import CAREERS,ALIASES
EXTRA=["python","java","javascript","typescript","html","css","react","next.js","node.js","fastapi","flask","django","sql","database","mongodb","redis","machine learning","deep learning","scikit-learn","pytorch","tensorflow","pandas","numpy","statistics","data analysis","visualization","docker","kubernetes","aws","cloud","mlops","git","linux","networking","security","scripting","ci/cd","terraform","transformers","rag","api","data structures","testing","accessibility","selenium","power bi","spark","shell","go","scala","swift","kotlin"]
VOCAB=set(EXTRA)
for c in CAREERS.values(): VOCAB.update(c['required']+c['recommended']+c['languages'])
def norm(s):
 s=s.lower().strip(); return ALIASES.get(s,s)
def extract(text):
 t=text.lower(); out=set()
 for s in sorted(VOCAB,key=len,reverse=True):
  if re.search(r'(?<![a-z0-9])'+re.escape(s)+r'(?![a-z0-9])',t): out.add(norm(s))
 return sorted(out)
