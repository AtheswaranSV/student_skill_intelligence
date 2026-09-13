import re,httpx
QUERY="""query userProblemsSolved($username: String!) { matchedUser(username: $username) { submitStatsGlobal { acSubmissionNum { difficulty count } } } }"""
async def analyze(url:str):
 m=re.search(r'leetcode\.com/(?:u/)?([A-Za-z0-9_.-]+)',url or '')
 if not m: return {"available":False,"reason":"Invalid LeetCode URL","problem_solving_score":None}
 user=m.group(1)
 try:
  async with httpx.AsyncClient(timeout=15,headers={"User-Agent":"Mozilla/5.0","Referer":"https://leetcode.com/"}) as c:
   r=await c.post("https://leetcode.com/graphql",json={"query":QUERY,"variables":{"username":user}})
  data=r.json().get('data',{}).get('matchedUser') if r.status_code==200 else None
  if not data: return {"available":False,"username":user,"reason":"Public LeetCode statistics unavailable","problem_solving_score":None}
  vals={x['difficulty'].lower():x['count'] for x in data['submitStatsGlobal']['acSubmissionNum']}; e=vals.get('easy',0); md=vals.get('medium',0); h=vals.get('hard',0); total=vals.get('all',e+md+h)
  weighted=e+2*md+4*h; score=min(100,round(weighted/6))
  return {"available":True,"username":user,"total_solved":total,"easy":e,"medium":md,"hard":h,"problem_solving_score":score}
 except Exception as e: return {"available":False,"username":user,"reason":str(e),"problem_solving_score":None}
