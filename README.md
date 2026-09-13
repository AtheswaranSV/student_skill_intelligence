# Student Skill Intelligence

A focused ML project: a student enters GitHub and LeetCode profile links, a resume link/text/PDF, and a target career domain, or uploads a JD. The system combines evidence from every supplied source, builds features, estimates role fit, identifies skill gaps, and uses a local Ollama LLM only to explain the structured result.

## Stack
- Frontend: Next.js 15 + TypeScript + Tailwind
- Backend: FastAPI + scikit-learn + PyMuPDF + httpx
- GitHub: official REST API
- LeetCode: public GraphQL connector with graceful fallback
- AI explanation: Ollama (`llama3.2:3b` by default)
- ML: RandomForestClassifier trained on a bundled synthetic/demo training set. Replace it with labeled student/outcome data for research-quality evaluation.

## Run backend (Windows)
```bat
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python train_model.py
uvicorn app.main:app --reload
```
Swagger: http://localhost:8000/docs

## Run Ollama (optional, free/local)
Install Ollama, then:
```bat
ollama pull llama3.2:3b
ollama serve
```
If Ollama is unavailable, the API returns a deterministic recommendation instead.

## Run frontend
```bat
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```
Open http://localhost:3000

## Main modes
1. **Career Readiness**: GitHub + LeetCode + target career/domain.
2. **JD Fit**: same profiles and resume evidence + PDF JD or pasted JD text.

The career selector covers software, AI/ML, data, cloud, cybersecurity, QA, mobile, and analytics domains. Resume input accepts a public `http(s)` PDF/text link, pasted text, or a PDF upload. Missing sources remain unavailable and are treated as neutral evidence rather than zero.

## Important
Only public technical profile information explicitly supplied by the student is analyzed. Missing LeetCode/GitHub data is marked unavailable, not treated as zero. The score is decision-support, not an automatic employment decision.
