import argparse
import csv
import sys
import time
from pathlib import Path

from code.classifier import classify_ticket
from code.retriever import Retriever
from code.router import route
from code.responder import generate_response

# Maps flexible input header variants -> the field name we use internally
HEADER_ALIASES = {
    "issue": "issue", "Issue": "issue",
    "subject": "subject", "Subject": "subject",
    "company": "company", "Company": "company",
}

OUTPUT_COLS = ["issue", "subject", "company", "response", "product_area",
               "status", "request_type", "justification"]


def normalize_row(row: dict) -> dict:
    normalized = {}
    for k, v in row.items():
        key = HEADER_ALIASES.get(k, k.lower() if k else k)
        normalized[key] = v
    return normalized


def process_row(row: dict, retriever: Retriever) -> dict:
    row = normalize_row(row)
    issue = (row.get("issue") or "").strip()
    subject = (row.get("subject") or "").strip()
    company = (row.get("company") or "None").strip()

    base = {"issue": issue, "subject": subject, "company": company}

    if not issue:
        return {
            **base,
            "response": "No issue text provided; nothing to process.",
            "product_area": "out-of-scope",
            "status": "escalated",
            "request_type": "invalid",
            "justification": "Empty issue field; escalating for manual review.",
        }

    try:
        classification = classify_ticket(issue, subject, company)
        decision = route(issue, classification, retriever)
        response_text = generate_response(issue, classification, decision, retriever)

        return {
            **base,
            "response": response_text,
            "product_area": classification.product_area.value,
            "status": decision.status.value,
            "request_type": classification.request_type.value,
            "justification": decision.reason,
        }
    except Exception as e:
        return {
            **base,
            "response": "This ticket could not be processed automatically and has been "
                         "flagged for manual review.",
            "product_area": "out-of-scope",
            "status": "escalated",
            "request_type": "invalid",
            "justification": f"Processing error, escalating as a safety default: {e}",
        }


def main():
    parser = argparse.ArgumentParser(description="Multi-domain support triage agent")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print("Loading corpus and building retrieval index...")
    retriever = Retriever()
    print(f"Loaded {len(retriever.chunks)} chunks.")

    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if args.limit:
        rows = rows[:args.limit]

    print(f"Processing {len(rows)} tickets...")
    results = []
    for i, row in enumerate(rows, 1):
        result = process_row(row, retriever)
        results.append(result)
        print(f"[{i}/{len(rows)}] status={result['status']:10} product_area={result['product_area']}")
        time.sleep(0.1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLS)
        writer.writeheader()
        for r in results:
            writer.writerow({col: r.get(col, "") for col in OUTPUT_COLS})

    print(f"\nDone. Wrote {len(results)} rows to {output_path}")


if __name__ == "__main__":
    main()