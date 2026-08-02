from dataclasses import dataclass

from code.schemas import ClassificationResult, Status
from code.risk_rules import should_force_escalate
from code.retriever import Retriever

CONFIDENCE_ESCALATE_THRESHOLD = 0.3

@dataclass
class RoutingDecision:
    status: Status
    reason: str

def route(issue_text: str, classification: ClassificationResult, retriever: Retriever) -> RoutingDecision:
    force, risk_categories = should_force_escalate(issue_text)
    if force:
        return RoutingDecision(
            status=Status.ESCALATED,
            reason=f"Escalated due to detected risk categories: {', '.join(risk_categories)}."
        )

    if classification.product_area.value == "out-of-scope":
        if not classification.risk_flags:
            return RoutingDecision(
                status=Status.REPLIED,
                reason="Ticket falls outside HackerRank/Claude/Visa support scope; "
                       "replying with an out-of-scope notice rather than escalating "
                       "since no risk signals were present."
            )
        return RoutingDecision(
            status=Status.ESCALATED,
            reason="Ticket is out of scope AND carries risk signals; escalating rather than guessing."
        )

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

    if classification.risk_flags:
        return RoutingDecision(
            status=Status.REPLIED,
            reason=f"Ticket has soft risk signals ({', '.join(classification.risk_flags)}) "
                   f"but strong corpus grounding (confidence {confidence:.3f}); replying "
                   f"with documented process rather than escalating."
        )

    return RoutingDecision(
        status=Status.REPLIED,
        reason=f"Standard FAQ-type request with strong corpus match (confidence {confidence:.3f})."
    )