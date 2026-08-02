import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

from code.retriever import Retriever, Chunk
from code.router import RoutingDecision
from code.schemas import Status, ClassificationResult

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

RESPONSE_SYSTEM_INSTRUCTION = """You write a single user-facing support response.

STRICT RULES:
- Use ONLY the provided support excerpts below as your source of truth.
- Do NOT use outside knowledge about HackerRank, Claude, or Visa, even if you
  believe you know the answer. If the excerpts don't cover it, say the specific
  step isn't covered in available documentation rather than guessing.
- Never state a policy, refund amount, deadline, or process step that isn't
  explicitly present in the excerpts.
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

def generate_response(
    issue_text: str,
    classification: ClassificationResult,
    decision: RoutingDecision,
    retriever: Retriever,
) -> str:
    if decision.status == Status.ESCALATED:
        # Escalated tickets get a handoff message, not an attempted answer.
        # Pull risk category names out of the reason string for template matching.
        for cat in ["fraud_or_security", "pii_or_legal", "self_harm_or_crisis",
                    "adversarial_content", "assessment_integrity"]:
            if cat in decision.reason:
                return _escalation_message([cat])
        return _escalation_message([])

    # Reply path — ground the answer in retrieved chunks only
    company = classification.company.value
    company = None if company == "none" else company
    results = retriever.search(issue_text, company=company, k=4)

    if not results:
        return ESCALATION_MESSAGE_TEMPLATES["default"]

    excerpts = "\n\n".join(
        f"[Source: {chunk.title}]\n{chunk.text[:800]}"
        for chunk, score in results
    )

    prompt = f"User's issue: {issue_text}\n\nRelevant support excerpts:\n{excerpts}"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=RESPONSE_SYSTEM_INSTRUCTION,
            temperature=0,
        ),
    )
    return response.text.strip()