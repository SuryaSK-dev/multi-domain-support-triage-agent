from fastapi import FastAPI
from pydantic import BaseModel

from src.retriever import Retriever
from src.classifier import classify_ticket
from src.router import route
from src.responder import generate_response

app = FastAPI(
    title="Multi-Domain Support Triage Agent",
    description="Classifies and routes support tickets across HackerRank, Claude, and Visa.",
    version="1.0.0",
)

_retriever: Retriever | None = None


@app.on_event("startup")
def load_retriever():
    global _retriever
    _retriever = Retriever()


class TriageRequest(BaseModel):
    issue: str
    subject: str = ""
    company: str = "None"


class TriageResponse(BaseModel):
    status: str
    product_area: str
    request_type: str
    response: str
    justification: str


@app.post("/triage", response_model=TriageResponse)
def triage(req: TriageRequest):
    classification = classify_ticket(req.issue, req.subject, req.company)
    decision = route(req.issue, classification, _retriever)
    response_text = generate_response(req.issue, classification, decision, _retriever)

    return TriageResponse(
        status=decision.status.value,
        product_area=classification.product_area.value,
        request_type=classification.request_type.value,
        response=response_text,
        justification=decision.reason,
    )


@app.get("/health")
def health():
    return {"status": "ok", "corpus_chunks": len(_retriever.chunks) if _retriever else 0}