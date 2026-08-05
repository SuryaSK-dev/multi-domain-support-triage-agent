from dataclasses import dataclass

from src.schemas import ClassificationResult, Status
from src.risk_rules import should_force_escalate, is_urgent_outage
from src.retriever import Retriever

CONFIDENCE_ESCALATE_THRESHOLD = 0.3

# Only these are escalated NO MATTER what the corpus says — they inherently
# require human judgment, not information lookup (self-harm needs a person,
# not an article; adversarial input can't be trusted; a disputed integrity
# finding needs case-by-case human review).
ALWAYS_ESCALATE_CATEGORIES = {"self_harm_or_crisis", "adversarial_content", "assessment_integrity"}

@dataclass
class RoutingDecision:
    status: Status
    reason: str


def route(issue_text: str, classification: ClassificationResult, retriever: Retriever) -> RoutingDecision:
    # 1. Absolute hard gate — no grounding check can override these
    force, risk_categories = should_force_escalate(issue_text)
    always_hit = [c for c in risk_categories if c in ALWAYS_ESCALATE_CATEGORIES]
    if always_hit:
        return RoutingDecision(
            status=Status.ESCALATED,
            reason=f"Escalated due to categories requiring human judgment: {', '.join(always_hit)}."
        )

    # 2. Out-of-scope handling
    if classification.product_area.value == "out-of-scope":
        if is_urgent_outage(issue_text):
            return RoutingDecision(
                status=Status.ESCALATED,
                reason="Ticket describes an urgent outage/broken-site issue; the corpus "
                       "has no live-status information, so this is escalated for immediate "
                       "human attention rather than replied to with a generic notice."
            )
        if not classification.risk_flags:
            return RoutingDecision(
                status=Status.REPLIED,
                reason="Ticket falls outside HackerRank/Claude/Visa support scope; "
                       "replying with an out-of-scope notice rather than escalating "
                       "since no risk or urgency signals were present."
            )
        return RoutingDecision(
            status=Status.ESCALATED,
            reason="Ticket is out of scope AND carries risk signals; escalating rather than guessing."
        )

    # 3. Grounding check — this is now the primary decision driver for
    # sensitive-sounding tickets (fraud, PII, billing, account access):
    # if the corpus has a real documented process, use it; if not, escalate.
    company = classification.company.value
    company = None if company == "none" else company
    results = retriever.search(issue_text, company=company, k=5)
    confidence = retriever.confidence(results, query=issue_text)

    if confidence < CONFIDENCE_ESCALATE_THRESHOLD:
        return RoutingDecision(
            status=Status.ESCALATED,
            reason=f"Retrieval confidence too low ({confidence:.3f}) to ground a safe "
                   f"answer in the support corpus; escalating instead of guessing."
        )

    if classification.risk_flags or (risk_categories and not always_hit):
        flags_str = ", ".join(set(classification.risk_flags) | set(risk_categories))
        return RoutingDecision(
            status=Status.REPLIED,
            reason=f"Ticket has sensitive signals ({flags_str}) but the support corpus "
                   f"contains a documented process for it (confidence {confidence:.3f}); "
                   f"replying with that documented process rather than escalating."
        )

    return RoutingDecision(
        status=Status.REPLIED,
        reason=f"Standard FAQ-type request with strong corpus match (confidence {confidence:.3f})."
    )