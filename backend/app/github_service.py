import re,httpx
from collections import Counter
from .config import settings
from .skills import extract,norm
async def analyze(url:str):
 m=re.search(r'github\.com/([A-Za-z0-9_.-]+)',url or '')
 if not m: return {"available":False,"reason":"Invalid GitHub URL","skills":[]}
 user=m.group(1); headers={"Accept":"application/vnd.github+json","User-Agent":"career-readiness-app"}
 if settings.github_token: headers["Authorization"]=f"Bearer {settings.github_token}"
 try:
  async with httpx.AsyncClient(timeout=15,headers=headers) as c:
   pr=await c.get(f"https://api.github.com/users/{user}"); rr=await c.get(f"https://api.github.com/users/{user}/repos",params={"per_page":100,"sort":"updated"})
  if pr.status_code!=200 or rr.status_code!=200: return {"available":False,"username":user,"reason":"GitHub API unavailable","skills":[]}
  repos=[r for r in rr.json() if not r.get('fork')]; langs=Counter(); skills=set(); stars=0; recent=0; projects=[]
  for r in repos:
   if r.get('language'): langs[norm(r['language'])]+=1
  text=' '.join([r.get('name') or '',r.get('description') or '',' '.join(r.get('topics') or []),r.get('language') or ''])
  repo_skills=extract(text); skills.update(repo_skills); stars+=r.get('stargazers_count',0)
  projects.append({"name":r['name'],"description":r.get('description'),"language":r.get('language'),"url":r.get('html_url'),"skills":repo_skills,"stars":r.get('stargazers_count',0)})
  skills.update(langs.keys())
  quality=min(100, round(len(repos)*3 + min(stars,30) + min(len(skills)*4,40)))
  return {"available":True,"username":user,"public_repos":len(repos),"languages":dict(langs),"skills":sorted(skills),"stars":stars,"quality_score":quality,"top_repositories":projects[:6],"projects":projects}
 except Exception as e: return {"available":False,"username":user,"reason":str(e),"skills":[]}
