import fitz
import re
from .skills import extract

def _problem_solving_required(text):
	return bool(re.search(r"problem[- ]solving|data structures and algorithms|algorithmic thinking|competitive programming|leetcode|coding challenges", text or "", re.IGNORECASE))

def parse_text(text):
	return {"text":text,"skills":extract(text),"problem_solving_required":_problem_solving_required(text)}
def parse_pdf(data:bytes):
 doc=fitz.open(stream=data,filetype='pdf'); text='\n'.join(p.get_text() for p in doc); return parse_text(text)
