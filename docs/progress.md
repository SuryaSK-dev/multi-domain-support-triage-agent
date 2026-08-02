# Build Progress & Verification

| Stage | File | Verifies against | Status |
|---|---|---|---|
| Retrieval | retriever.py | BM25 returns relevant chunks for known queries; categories match corpus folders | done |
| Schemas | schemas.py | Enums cover real corpus taxonomy; Pydantic validates | done |
| Risk rules | risk_rules.py | Known-risky phrases trigger escalation; known-safe phrases don't | next |
| Classifier | classifier.py | Gemini structured output matches schema; company routing correct on sample tickets | pending |
| Router | router.py | reply/escalate decision matches sample_support_tickets.csv expected output | pending |
| Responder | responder.py | Generated response only uses retrieved text, no fabricated policy | pending |
| End-to-end | main.py | Full run on sample_support_tickets.csv scores well against expected columns | pending |
