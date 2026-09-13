import json
import re
import httpx
from .config import settings
from .careers import CAREERS

def _limit_words(text, maximum):
 text=text.replace('*','').replace('#','').replace('`','').replace('\n',' ')
 text=re.sub(r'(^|\s)\d+[.)]\s*', ' ', text)
 words=' '.join(text.split()).split()
 return ' '.join(words[:maximum]) + ('...' if len(words)>maximum else '')

def _short_list(value, maximum=3):
 return value[:maximum] if isinstance(value, list) else []

async def _generate(prompt, max_output_tokens=350):
 if settings.gemini_api_key and settings.gemini_api_key != "paste-your-gemini-api-key-here":
  models=[]
  for model in [settings.gemini_model]+settings.gemini_fallback_models.split(','):
   model=model.strip()
   if model and model not in models: models.append(model)
  async with httpx.AsyncClient(timeout=45) as c:
   for model in models:
    try:
     url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
     r=await c.post(url,params={"key":settings.gemini_api_key},json={"contents":[{"parts":[{"text":prompt}]}]})
     if r.status_code==200:
      text=r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
      if text: return text
    except Exception: pass
 try:
  async with httpx.AsyncClient(timeout=45) as c:
   r=await c.post(f"{settings.ollama_url}/api/generate",json={"model":settings.ollama_model,"prompt":prompt,"stream":False,"options":{"temperature":0.35,"num_predict":max_output_tokens}})
   if r.status_code==200: return r.json().get('response','').strip()
 except Exception: pass
 return ""

async def assess_domain(result):
 profile=CAREERS.get(result.get('career'),CAREERS['Full Stack Developer'])
 prompt=f"""Act as a senior hiring manager for {result.get('career')}. Compare the candidate's complete resume, projects, LeetCode, GitHub, and JD with the domain requirements. Return ONLY JSON. Keep every array to at most 3 short items and each item under 12 words. Use keys: domain_competencies, priority_gaps, resume_improvements, project_improvements, conversation. Do not invent facts. Core={profile['required']}; advanced={profile['recommended']}; evidence={result}"""
 response=await _generate(prompt, max_output_tokens=220)
 if response:
  try:
   cleaned=response.strip().removeprefix('```json').removesuffix('```').strip()
   parsed=json.loads(cleaned)
   if isinstance(parsed,dict):
    parsed['domain_competencies']=_short_list(parsed.get('domain_competencies'))
    parsed['priority_gaps']=_short_list(parsed.get('priority_gaps'))
    parsed['resume_improvements']=_short_list(parsed.get('resume_improvements'))
    parsed['project_improvements']=_short_list(parsed.get('project_improvements'))
    parsed['conversation']=_limit_words(str(parsed.get('conversation','')),35)
    return parsed
  except (json.JSONDecodeError,TypeError): pass
 return {"domain_competencies":[{"name":skill,"category":"core","importance":"high","evidence_expected":"Show practical use in resume or projects."} for skill in profile['required']],"priority_gaps":result.get('missing_required',[])[:6],"resume_improvements":["Rewrite bullets with measurable outcomes and clear personal contribution."],"project_improvements":["Add README architecture, tests, deployment details, and a live demonstration."],"conversation":result.get('ai_explanation','Start with the highest-impact missing core skills and strengthen project evidence.')}

async def domain_guidance(career):
 profile=CAREERS.get(career,CAREERS['Full Stack Developer'])
 prompt=f"""You are a technical hiring expert. For {career}, summarize the most important core skills, advanced skills, project evidence, and resume evidence needed to excel. Use the baseline core={profile['required']} and advanced={profile['recommended']}. Reply in 2 short sentences, maximum 45 words. Do not write an essay."""
 response=await _generate(prompt, max_output_tokens=100)
 return _limit_words(response,30) if response else f"Core: {', '.join(profile['required'])}. Advanced: {', '.join(profile['recommended'])}. Show them in measurable projects."

async def explain(result):
 prompt=f"""You are Gemini acting as a career coach. Return only 2 or 3 short plain-text sentences, maximum 45 words. No markdown, bullets, stars, headings, numbering, or long explanation. State the readiness, the top one or two improvements, and tell the candidate to use Improvement Chat for details. Use only this evidence: {result}"""
 response=await _generate(prompt, max_output_tokens=180)
 if response: return _limit_words(response,45)
 gaps=', '.join(result.get('missing_required',[])[:4]) or 'no major required-skill gaps detected'
 problem_note='The job description requests problem-solving evidence, so continue LeetCode practice.' if result.get('jd_requirements',{}).get('problem_solving_required') else 'Keep problem-solving practice consistent.'
 projects=', '.join(p['name'] for p in result.get('project_evidence',[])[:3]) or 'no matching GitHub projects detected'
 return f"Your current evidence gives a {result['readiness_score']}% fit for {result['career']}. Focus first on {gaps}. Core skill gaps should be addressed before advanced skills. {problem_note} Matching GitHub projects: {projects}. Improve resume bullets with measurable outcomes, clarify your technical contribution, strengthen project links and deployment evidence, build one deployable project, and re-run the analysis after adding evidence."

async def chat(result, message, history):
 prompt=f"""You are a conversational Gemini career mentor. Reply in 2 to 4 plain-text sentences and 40 to 70 words. No markdown symbols or numbered lists. Give direct, personalized actions using the candidate's resume, projects, domain, and evidence. Do not invent facts. Domain: {result.get('career')}. Evidence: {result}. Recent chat: {history}. Latest question: {message}"""
 response=await _generate(prompt, max_output_tokens=220)
 return _limit_words(response,65) if response else "Start with the highest-impact gap and improve one project with measurable results. Ask me about skills, resume, or projects for more detail."
