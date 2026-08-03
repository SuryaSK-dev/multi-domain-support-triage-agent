import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

from code.retriever import Retriever
from code.router import RoutingDecision
from code.schemas import Status, ClassificationResult
from code.cache import cache_get, cache_set
from code.rate_limiter import throttle
from code.key_manager import get_current_key, rotate_key

load_dotenv()

RESPONSE_SYSTEM_INSTRUCTION = """You write a single user-facing support response.

STRICT RULES:
- Use ONLY the provided support excerpts below as your source of truth.
- Do NOT use outside knowledge about HackerRank, Claude, or Visa, even if you
  believe you know the answer. If the excerpts don't cover it, say the specific
  step isn't covered in available documentation rather than guessing.
- Never state a policy, refund amount, deadline, or process step that isn't
  explicitly present in the excerpts.
- IMPORTANT: if the user's specific question is not directly answered by the
  excerpts (even if the excerpts are topically related), you MUST explicitly
  say the documentation doesn't cover that specific point, rather than
  answering with adjacent facts that could be mistaken for a direct answer.
- Keep the tone helpful, concise, and professional — 2-4 sentences typically.
- Do not mention "excerpts", "documents", or internal reasoning to the user;
  write as a normal support reply.
"""

ESCALATION_MESSAGE_TEMPLATES = {
    "fraud_or_security": "This involves a potential security or fraud concern, so we've flagged "
                          "it for immediate review by our support team rather than handling it "
                          "automatically.",
    "pii_or_legal": "This request involves sensitive personal or legal information, so it's "
                     "been routed to our support team for careful review.",
    "self_harm_or_crisis": "We've routed this to our support team directly for the personal "
                            "attention it deserves.",
    "adversarial_content": "We've flagged this request for manual review by our support team.",
    "assessment_integrity": "This involves an assessment integrity matter, which requires "
                             "review by our team rather than an automated response.",
    "default": "This request needs review by a member of our support team rather than an "
               "automated response. We've flagged it and someone will follow up.",
}


def _escalation_message(risk_categories: list[str]) -> str:
    for cat in risk_categories:
        if cat in ESCALATION_MESSAGE_TEMPLATES:
            return ESCALATION_MESSAGE_TEMPLATES[cat]
    return ESCALATION_MESSAGE_TEMPLATES["default"]


def _get_client():
    return genai.Client(api_key=get_current_key())


def _call_with_retry(build_call_fn, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return build_call_fn()
        except Exception as e:
            err_str = str(e)
            if "RESOURCE_EXHAUSTED" in err_str and "PerDay" in err_str:
                if rotate_key():
                    continue
                else:
                    raise
            elif "RESOURCE_EXHAUSTED" in err_str and attempt < max_retries - 1:
                wait = 40 * (attempt + 1)
                print(f"Rate limited, waiting {wait}s before retry...")
                time.sleep(wait)
            else:
                raise


def generate_response(
    issue_text: str,
    classification: ClassificationResult,
    decision: RoutingDecision,
    retriever: Retriever,
) -> str:
    if decision.status == Status.ESCALATED:
        for cat in ["fraud_or_security", "pii_or_legal", "self_harm_or_crisis",
                    "adversarial_content", "assessment_integrity"]:
            if cat in decision.reason:
                return _escalation_message([cat])
        return _escalation_message([])

    company = classification.company.value
    company = None if company == "none" else company

    cached = cache_get("respond", issue_text, company or "none")
    if cached:
        return cached

    results = retriever.search(issue_text, company=company, k=4)
    if not results:
        return ESCALATION_MESSAGE_TEMPLATES["default"]

    excerpts = "\n\n".join(
        f"[Source: {chunk.title}]\n{chunk.text[:800]}"
        for chunk, score in results
    )
    prompt = f"User's issue: {issue_text}\n\nRelevant support excerpts:\n{excerpts}"

    throttle()
    response = _call_with_retry(lambda: _get_client().models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=RESPONSE_SYSTEM_INSTRUCTION,
            temperature=0,
        ),
    ))
    result_text = response.text.strip()
    cache_set("respond", issue_text, company or "none", value=result_text)
    return result_text