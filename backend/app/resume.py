import re

import fitz
import httpx

from .skills import extract


def _result(text: str, source: str) -> dict:
    cleaned = text.strip()
    if not cleaned:
        return {"available": False, "source": source, "reason": "Resume contained no readable text", "skills": []}
    return {
        "available": True,
        "source": source,
        "skills": extract(cleaned),
        "text_length": len(cleaned),
        "text": cleaned[:16000],
    }


def parse_text(text: str, source: str = "text") -> dict:
    return _result(text or "", source)


def parse_pdf(data: bytes, source: str = "upload") -> dict:
    try:
        with fitz.open(stream=data, filetype="pdf") as document:
            text = "\n".join(page.get_text() for page in document)
        return _result(text, source)
    except Exception as exc:
        return {"available": False, "source": source, "reason": f"Could not read resume PDF: {exc}", "skills": []}


async def analyze(url: str = "", data: bytes | None = None, text: str = "") -> dict:
    if data:
        return parse_pdf(data)
    if text.strip():
        return parse_text(text)
    if not url.strip():
        return {"available": False, "reason": "No resume supplied", "skills": []}
    if not re.match(r"^https?://", url, re.IGNORECASE):
        return {"available": False, "source": url, "reason": "Resume URL must use http or https", "skills": []}
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": "student-skill-intelligence"}) as client:
            response = await client.get(url)
        if response.status_code != 200:
            return {"available": False, "source": url, "reason": f"Resume download failed with HTTP {response.status_code}", "skills": []}
        content_type = response.headers.get("content-type", "").lower()
        if "pdf" in content_type or url.lower().split("?")[0].endswith(".pdf"):
            return parse_pdf(response.content, url)
        return parse_text(response.text, url)
    except Exception as exc:
        return {"available": False, "source": url, "reason": f"Resume download failed: {exc}", "skills": []}
