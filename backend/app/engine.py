from .careers import CAREERS
from .model import predict
def pct(a,b): return round(100*len(set(a)&set(b))/max(1,len(set(b))))
def analyze(github,leetcode,target,resume=None,custom_skills=None,jd_requirements=None):
 resume=resume or {"available":False,"skills":[]}
 profile=CAREERS.get(target,CAREERS['Full Stack Developer']); required=custom_skills or profile['required']; recommended=profile['recommended']; jd_requirements=jd_requirements or {}
 github_skills=set(github.get('skills',[])); resume_skills=set(resume.get('skills',[])); all_skills=github_skills | resume_skills
 req=pct(all_skills,required); rec=pct(all_skills,recommended); proj=github.get('quality_score',0) if github.get('available') else 0; problem=leetcode.get('problem_solving_score') if leetcode.get('available') else None
 resume_match=pct(resume_skills,required) if resume.get('available') else None
 resume_jd_match=pct(resume_skills,required) if resume.get('available') and custom_skills else None
 core_matched=sorted(all_skills & set(required)); core_missing=sorted(set(required)-all_skills); advanced_matched=sorted(all_skills & set(recommended)); advanced_missing=sorted(set(recommended)-all_skills)
 projects=[]
 for project in github.get('projects',[]):
  project_skills=set(project.get('skills',[])); project_core=sorted(project_skills & set(required)); project_advanced=sorted(project_skills & set(recommended))
  if project_core or project_advanced:
   projects.append({"name":project.get('name'),"url":project.get('url'),"description":project.get('description'),"matched_core_skills":project_core,"matched_advanced_skills":project_advanced,"project_fit_score":pct(project_skills,required)})
 # Missing external evidence is neutral (50), not zero.
 problem_required=bool(jd_requirements.get('problem_solving_required',False)); problem_feature=problem if problem is not None else 50; github_feature=proj if github.get('available') else 50; resume_feature=resume_match if resume_match is not None else 50
 features=[req,rec,github_feature,problem_feature,resume_feature,100 if all([github.get('available'),leetcode.get('available'),resume.get('available')]) else 50]
 pred=predict(features); score=round(req*.40+rec*.10+github_feature*.20+problem_feature*.15+resume_feature*.10+50*.05)
 matched=sorted(all_skills & set(required)); missing=sorted(set(required)-all_skills); bonus=sorted(all_skills & set(recommended))
 confidence="high" if github.get('available') and leetcode.get('available') and resume.get('available') else "medium" if any([github.get('available'),leetcode.get('available'),resume.get('available')]) else "low"
 return {"career":target,"readiness_score":score,"readiness":pred,"components":{"required_skill_match":req,"recommended_skill_match":rec,"github_quality":proj if github.get('available') else None,"problem_solving":problem,"resume_skill_match":resume_match,"resume_jd_match":resume_jd_match},"matched_required":matched,"missing_required":missing,"matched_recommended":bonus,"required_skills":required,"recommended_skills":recommended,"core_skills":{"matched":core_matched,"missing":core_missing},"advanced_skills":{"matched":advanced_matched,"missing":advanced_missing},"project_evidence":projects[:10],"jd_requirements":{"problem_solving_required":problem_required,"resume_skill_match_to_jd":resume_jd_match},"evidence_sources":{"github":github.get('available',False),"leetcode":leetcode.get('available',False),"resume":resume.get('available',False)},"evidence_confidence":confidence}
