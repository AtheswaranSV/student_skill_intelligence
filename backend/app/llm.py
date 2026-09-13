import json
import re
import httpx
from .config import settings


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _clean_json(text: str):
    """
    Removes Gemini markdown fences and extracts a JSON object.
    """

    text = (text or "").strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    # Sometimes Gemini adds text before/after JSON
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:
        text = text[start:end + 1]

    return text.strip()


def _limit_words(text: str, maximum: int):
    text = str(text or "")

    text = (
        text
        .replace("*", "")
        .replace("#", "")
        .replace("`", "")
        .replace("\n", " ")
    )

    text = re.sub(
        r"(^|\s)\d+[.)]\s*",
        " ",
        text
    )

    words = " ".join(text.split()).split()

    return " ".join(words[:maximum]) + (
        "..." if len(words) > maximum else ""
    )


# ---------------------------------------------------------
# Gemini Core
# ---------------------------------------------------------

async def _generate(
    prompt: str,
    max_output_tokens: int = 1200,
    temperature: float = 0.15
):
    """
    Gemini ONLY.

    No Ollama.
    No predefined fallback.
    No fake AI response.
    """

    api_key = getattr(
        settings,
        "gemini_api_key",
        ""
    )

    model = getattr(
        settings,
        "gemini_model",
        ""
    )

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    if not model:
        raise RuntimeError(
            "GEMINI_MODEL is not configured."
        )

    url = (
        "https://generativelanguage.googleapis.com/"
        f"v1beta/models/{model}:generateContent"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        }
    }

    try:
        async with httpx.AsyncClient(
            timeout=60
        ) as client:

            response = await client.post(
                url,
                params={
                    "key": api_key
                },
                json=payload
            )

    except Exception as e:

        raise RuntimeError(
            f"Could not connect to Gemini: {e}"
        )


    if response.status_code != 200:

        try:
            error_data = response.json()

        except Exception:
            error_data = response.text

        raise RuntimeError(
            "Gemini request failed "
            f"HTTP {response.status_code}: "
            f"{error_data}"
        )


    data = response.json()

    candidates = data.get(
        "candidates",
        []
    )

    if not candidates:

        raise RuntimeError(
            f"Gemini returned no candidate: {data}"
        )


    try:

        parts = (
            candidates[0]
            ["content"]
            ["parts"]
        )

        text = "".join(
            part.get("text", "")
            for part in parts
        ).strip()

    except Exception as e:

        raise RuntimeError(
            f"Invalid Gemini response: {e}"
        )


    if not text:

        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return text


async def _generate_json(
    prompt: str,
    max_output_tokens: int = 1800
):
    """
    Calls Gemini and guarantees parsed JSON.
    """

    text = await _generate(
        prompt,
        max_output_tokens=max_output_tokens,
        temperature=0.10
    )

    cleaned = _clean_json(text)

    try:

        result = json.loads(
            cleaned
        )

    except json.JSONDecodeError as e:

        raise RuntimeError(
            "Gemini did not return valid JSON. "
            f"Response: {text[:800]}"
        ) from e


    if not isinstance(
        result,
        dict
    ):

        raise RuntimeError(
            "Gemini JSON response must be an object."
        )


    return result


# ---------------------------------------------------------
# Resume Parsing
# ---------------------------------------------------------

async def parse_resume(
    resume_text: str
):
    """
    Gemini extracts ALL technical evidence.

    It does NOT just look at Skills section.
    """

    if not resume_text.strip():

        return {
            "skills": [],
            "languages": [],
            "frameworks": [],
            "libraries": [],
            "databases": [],
            "cloud_devops": [],
            "ai_ml": [],
            "tools": [],
            "projects": [],
            "experience": [],
            "certifications": []
        }


    prompt = f"""
You are an expert technical resume parser.

Analyze the following candidate resume.

Your job is to extract ALL real technical evidence.

Do NOT only inspect the Skills section.

Look at:

1. Skills section
2. Projects
3. Internships
4. Work experience
5. Certifications
6. Education
7. Technical achievements

For EACH project determine which technologies were
actually used in that project.

For EACH work experience determine which technologies
were actually used.

Never invent technologies.

Normalize technology names.

Examples:

React.js -> React
ReactJS -> React
NextJS -> Next.js
NodeJS -> Node.js
FastAPI -> FastAPI
Sklearn -> Scikit-learn

Return ONLY JSON in this exact general structure:

{{
    "skills": [],
    "languages": [],
    "frameworks": [],
    "libraries": [],
    "databases": [],
    "cloud_devops": [],
    "ai_ml": [],
    "tools": [],

    "projects": [
        {{
            "name": "",
            "description": "",
            "technologies": [],
            "technical_evidence": []
        }}
    ],

    "experience": [
        {{
            "organization": "",
            "role": "",
            "technologies": [],
            "technical_evidence": []
        }}
    ],

    "certifications": []
}}

Do not include skills that cannot be supported by
the resume text.

RESUME:

{resume_text}
"""

    return await _generate_json(
        prompt,
        max_output_tokens=2200
    )


# ---------------------------------------------------------
# Career / Domain Requirement Generation
# ---------------------------------------------------------

async def get_domain_rubric(
    career: str
):
    """
    Gemini itself determines what skills matter
    for the selected career.

    No CAREERS required/recommended list controls this.
    """

    prompt = f"""
Act as a senior technical hiring manager.

Target career:

{career}

Build a technical competency rubric for a fresher or
entry-level candidate targeting this role.

Determine the skills CURRENTLY important for this role.

Include:

- programming languages
- frameworks
- libraries
- databases
- APIs
- cloud
- DevOps
- testing
- architecture concepts
- role-specific technologies
- core CS knowledge where appropriate

Give EACH skill a numeric weight.

The SUM of every skill weight MUST equal exactly 100.

Critical role-specific technologies must receive
higher weights.

For example, for frontend roles, important frameworks
such as React, Next.js, TypeScript or equivalent
modern frontend technologies can receive significant
weight when appropriate.

Do NOT use a generic identical rubric for every role.

Return ONLY JSON:

{{
    "target": "{career}",

    "skills": [
        {{
            "skill": "",
            "weight": 0,
            "importance": "critical|important|supporting",
            "reason": ""
        }}
    ],

    "project_expectations": [],

    "github_expectations": [],

    "problem_solving_importance":
        "low|medium|high"
}}

Rules:

- all skill weights together = 100
- avoid duplicate skills
- use practical hiring expectations
- keep between 8 and 18 skills
"""

    return await _generate_json(
        prompt,
        max_output_tokens=1800
    )


# ---------------------------------------------------------
# JD Parsing + Dynamic Weighting
# ---------------------------------------------------------

async def parse_jd(
    jd_text: str,
    title: str = "Job Description"
):
    """
    Gemini determines requirements directly from JD.
    """

    prompt = f"""
You are a senior technical recruiter.

Analyze this job description:

TITLE:
{title}

JOB DESCRIPTION:

{jd_text}

Extract the actual technical requirements.

Consider:

- mandatory skills
- preferred skills
- responsibilities
- frameworks
- programming languages
- libraries
- databases
- cloud platforms
- DevOps
- testing
- AI/ML skills
- system design
- DSA/problem solving

Give mandatory and strongly emphasized skills
higher weight.

Preferred or nice-to-have skills should receive
less weight.

Repeated technologies can receive greater importance.

The sum of skill weights MUST equal exactly 100.

Return ONLY JSON:

{{
    "title": "{title}",

    "skills": [
        {{
            "skill": "",
            "weight": 0,
            "importance":
                "mandatory|important|preferred",
            "reason": ""
        }}
    ],

    "responsibilities": [],

    "problem_solving_required": false,

    "experience_requirements": [],

    "education_requirements": []
}}
"""

    return await _generate_json(
        prompt,
        max_output_tokens=2000
    )


# ---------------------------------------------------------
# Complete Candidate Evidence Evaluation
# ---------------------------------------------------------

async def evaluate_candidate(
    target: str,
    rubric: dict,
    resume: dict,
    github: dict,
    leetcode: dict,
    jd_text: str = ""
):
    """
    This is the key function.

    Gemini evaluates EACH required skill against:

    - resume Skills section
    - resume project usage
    - work experience
    - GitHub
    - LeetCode where relevant
    """

    prompt = f"""
Act as a senior technical hiring evaluator.

Evaluate this candidate for:

TARGET:
{target}

TARGET REQUIREMENTS:

{json.dumps(rubric, indent=2)}

PARSED RESUME:

{json.dumps(resume, indent=2)}

GITHUB EVIDENCE:

{json.dumps(github, indent=2)}

LEETCODE EVIDENCE:

{json.dumps(leetcode, indent=2)}

JOB DESCRIPTION:

{jd_text or "No JD supplied. Career-domain mode."}


IMPORTANT EVIDENCE RULES

Do NOT treat all evidence equally.

A skill merely appearing in a resume Skills section
is weaker evidence than actual project usage.

Use approximately this evidence interpretation:

0-20:
No meaningful evidence.

30-50:
Skill only mentioned in Skills/tools list.

55-70:
Skill supported by certification, internship,
coursework or limited practical evidence.

65-85:
Skill clearly used in a meaningful project
or professional experience.

80-100:
Strong project/experience usage supported by
GitHub evidence or multiple independent examples.


EXAMPLE:

If candidate says:

Skills: React

but has no React project,
give moderate evidence.

If candidate has:

Built application using React and TypeScript

give significantly stronger React evidence.

If GitHub also shows React repositories,
that can further strengthen evidence.


SEMANTIC MATCHING

Understand equivalent or closely related terms.

Examples:

ReactJS == React
NextJS == Next.js
JS == JavaScript
TS == TypeScript
Sklearn == Scikit-learn

Do not require exact text matching.

But DO NOT treat unrelated technologies as equivalent.


For EVERY skill in the target rubric, return:

- skill
- weight
- resume_mentioned
- used_in_resume_project
- used_in_experience
- github_evidence
- certification_evidence
- evidence_score
- evidence
- gap
- improvement


Then separately assess project strength.

Return ONLY JSON:

{{
    "skill_assessments": [
        {{
            "skill": "",
            "weight": 0,

            "resume_mentioned": false,

            "used_in_resume_project": false,

            "used_in_experience": false,

            "github_evidence": false,

            "certification_evidence": false,

            "evidence_score": 0,

            "evidence": [],

            "gap": "",

            "improvement": ""
        }}
    ],

    "project_score": 0,

    "project_evidence": [],

    "github_score": 0,

    "github_summary": "",

    "problem_solving_score": 0,

    "problem_solving_summary": "",

    "strengths": [],

    "priority_gaps": [],

    "resume_improvements": [],

    "project_improvements": [],

    "career_summary": ""
}}

Evidence scores must be between 0 and 100.

Do not fabricate evidence.

If GitHub or LeetCode data is unavailable,
explicitly account for that instead of assuming zero skill.
"""

    return await _generate_json(
        prompt,
        max_output_tokens=3500
    )


# ---------------------------------------------------------
# Deterministic Final Score
# ---------------------------------------------------------

def calculate_final_score(
    assessment: dict
):
    """
    Gemini determines evidence strength.

    Python performs final arithmetic.

    70% technical skills
    15% projects
    10% GitHub
    5% problem solving
    """

    skill_items = assessment.get(
        "skill_assessments",
        []
    )

    weighted_skill_score = 0.0
    total_weight = 0.0


    for item in skill_items:

        try:

            weight = float(
                item.get(
                    "weight",
                    0
                )
            )

            evidence = float(
                item.get(
                    "evidence_score",
                    0
                )
            )

        except Exception:

            continue


        evidence = max(
            0,
            min(
                evidence,
                100
            )
        )

        weighted_skill_score += (
            weight * evidence
        )

        total_weight += weight


    if total_weight:

        technical_score = (
            weighted_skill_score /
            total_weight
        )

    else:

        technical_score = 0


    project_score = float(
        assessment.get(
            "project_score",
            0
        )
    )

    github_score = float(
        assessment.get(
            "github_score",
            0
        )
    )

    problem_score = float(
        assessment.get(
            "problem_solving_score",
            0
        )
    )


    final_score = (
        technical_score * 0.70
        + project_score * 0.15
        + github_score * 0.10
        + problem_score * 0.05
    )


    return {
        "technical_score":
            round(
                technical_score,
                1
            ),

        "project_score":
            round(
                project_score,
                1
            ),

        "github_score":
            round(
                github_score,
                1
            ),

        "problem_solving_score":
            round(
                problem_score,
                1
            ),

        "readiness_score":
            round(
                final_score,
                1
            )
    }


# ---------------------------------------------------------
# Readiness Label
# ---------------------------------------------------------

def readiness_label(
    score: float
):
    if score >= 85:
        return "Strong Fit"

    if score >= 70:
        return "Good Fit"

    if score >= 55:
        return "Developing Fit"

    return "Needs Improvement"


# ---------------------------------------------------------
# Compatibility with your existing main.py
# ---------------------------------------------------------

async def domain_guidance(
    career: str
):
    """
    Existing main.py can still call domain_guidance().
    """

    rubric = await get_domain_rubric(
        career
    )

    top_skills = sorted(
        rubric.get(
            "skills",
            []
        ),
        key=lambda x:
            x.get(
                "weight",
                0
            ),
        reverse=True
    )[:6]


    text = ", ".join(
        f"{x.get('skill')} "
        f"({x.get('weight')}%)"
        for x in top_skills
    )

    return (
        f"Highest-priority competencies for "
        f"{career}: {text}."
    )


async def assess_domain(
    result: dict
):
    """
    Compatibility function.

    Uses Gemini evidence evaluation instead of
    CAREERS predefined skill lists.
    """

    career = result.get(
        "career",
        "Full Stack Developer"
    )

    resume = result.get(
        "resume",
        {}
    )

    github = result.get(
        "github",
        {}
    )

    leetcode = result.get(
        "leetcode",
        {}
    )

    jd_requirements = result.get(
        "jd_requirements"
    )


    # JD mode
    if jd_requirements:

        if (
            isinstance(
                jd_requirements,
                dict
            )
            and jd_requirements.get(
                "skills"
            )
        ):

            rubric = jd_requirements

        else:

            jd_text = str(
                jd_requirements
            )

            rubric = await parse_jd(
                jd_text,
                career
            )

    # Career mode
    else:

        rubric = await get_domain_rubric(
            career
        )


    parsed_resume = (
        resume.get(
            "parsed"
        )
        if isinstance(
            resume,
            dict
        )
        else {}
    )


    assessment = await evaluate_candidate(
        target=career,
        rubric=rubric,
        resume=parsed_resume or resume,
        github=github,
        leetcode=leetcode,
        jd_text=result.get(
            "jd_text",
            ""
        )
    )


    scores = calculate_final_score(
        assessment
    )


    assessment.update(
        scores
    )


    assessment[
        "readiness_label"
    ] = readiness_label(
        scores[
            "readiness_score"
        ]
    )


    assessment[
        "rubric"
    ] = rubric


    assessment[
        "conversation"
    ] = assessment.get(
        "career_summary",
        ""
    )


    return assessment


# ---------------------------------------------------------
# Final Gemini Explanation
# ---------------------------------------------------------

async def explain(
    result: dict
):
    prompt = f"""
You are a concise technical career mentor.

Candidate analysis:

{json.dumps(result, indent=2)}

Provide exactly 2 or 3 short sentences.

Mention:

- overall readiness
- strongest evidence
- highest-priority improvement

Do not invent evidence.

Do not use markdown.

Maximum 55 words.
"""

    response = await _generate(
        prompt,
        max_output_tokens=160,
        temperature=0.20
    )

    return _limit_words(
        response,
        55
    )


# ---------------------------------------------------------
# Improvement Chat
# ---------------------------------------------------------

async def chat(
    result: dict,
    message: str,
    history: list
):
    recent_history = (
        history[-6:]
        if isinstance(
            history,
            list
        )
        else []
    )

    prompt = f"""
You are Gemini acting as the candidate's
technical career mentor.

TARGET:

{result.get("career")}

CANDIDATE ANALYSIS:

{json.dumps(result, indent=2)}

RECENT CHAT:

{json.dumps(recent_history, indent=2)}

USER QUESTION:

{message}

Give direct and personalized advice.

Base your answer only on available evidence.

You can discuss:

- missing skills
- project improvements
- resume improvements
- GitHub improvements
- LeetCode/problem solving
- career roadmap
- JD requirements

Do not fabricate technologies or experience.

Reply in 3 to 5 short sentences.

No markdown tables.

Maximum 100 words.
"""

    response = await _generate(
        prompt,
        max_output_tokens=300,
        temperature=0.25
    )

    return _limit_words(
        response,
        100
    )
