from fastapi import FastAPI,UploadFile,File,Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
from .github_service import analyze as github_analyze
from .leetcode_service import analyze as leetcode_analyze
from .engine import analyze
from .llm import explain,domain_guidance,assess_domain
from .jd import parse_pdf,parse_text
from .resume import analyze as resume_analyze
from .careers import CAREERS
app=FastAPI(title="Student Skill Intelligence",version="1.0")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:3000","http://127.0.0.1:3000"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
class CareerRequest(BaseModel): github_url:str=""; leetcode_url:str=""; career:str; resume_url:str=""; resume_text:str=""
class JDTextRequest(BaseModel): github_url:str=""; leetcode_url:str=""; jd_text:str; title:str="JD Fit"; resume_url:str=""; resume_text:str=""
class ChatRequest(BaseModel): result:dict[str,Any]; message:str; history:list[dict[str,str]]=[]
@app.get('/api/health')
def health(): return {"status":"ok"}
@app.get('/api/careers')
def careers(): return list(CAREERS.keys())
@app.post('/api/chat')
async def chat_endpoint(req:ChatRequest):
 from .llm import chat
 return {"reply":await chat(req.result,req.message,req.history)}
async def run(g,l,target,skills=None,resume_url="",resume_text="",resume_data=None,jd_requirements=None):
 gh=await github_analyze(g); lc=await leetcode_analyze(l); resume=await resume_analyze(resume_url,resume_data,resume_text); result=analyze(gh,lc,target,resume,skills,jd_requirements); result['github']=gh; result['leetcode']=lc; result['resume']=resume; result['domain_guidance']=await domain_guidance(target); result['llm_assessment']=await assess_domain(result); result['priority_gaps']=result['llm_assessment'].get('priority_gaps',result['missing_required']); result['resume_improvements']=result['llm_assessment'].get('resume_improvements',[]); result['project_improvements']=result['llm_assessment'].get('project_improvements',[]); result['ai_conversation']=result['llm_assessment'].get('conversation',''); result['ai_explanation']=await explain(result); return result
@app.post('/api/analyze/career')
async def career(req:CareerRequest): return await run(req.github_url,req.leetcode_url,req.career,resume_url=req.resume_url,resume_text=req.resume_text)
@app.post('/api/analyze/career-upload')
async def career_upload(github_url:str=Form(""),leetcode_url:str=Form(""),career:str=Form(...),resume_url:str=Form(""),resume_text:str=Form(""),resume_file:UploadFile|None=File(None)):
 data=await resume_file.read() if resume_file else None
 return await run(github_url,leetcode_url,career,resume_url=resume_url,resume_text=resume_text,resume_data=data)
@app.post('/api/analyze/jd-text')
async def jd_text(req:JDTextRequest):
 jd=parse_text(req.jd_text); out=await run(req.github_url,req.leetcode_url,req.title,jd['skills'],req.resume_url,req.resume_text,jd_requirements=jd); out['jd_skills']=jd['skills']; out['jd_requirements']=jd; return out
@app.post('/api/analyze/jd-pdf')
async def jd_pdf(github_url:str=Form(""),leetcode_url:str=Form(""),title:str=Form('JD Fit'),resume_url:str=Form(""),resume_text:str=Form(""),file:UploadFile=File(...),resume_file:UploadFile|None=File(None)):
 jd=parse_pdf(await file.read()); resume_data=await resume_file.read() if resume_file else None
 out=await run(github_url,leetcode_url,title,jd['skills'],resume_url,resume_text,resume_data,jd); out['jd_skills']=jd['skills']; out['jd_requirements']=jd; return out
