import argparse
import csv
import sys
from pathlib import Path
from collections import defaultdict


def normalize_status(s: str) -> str:
    return (s or "").strip().lower()


def normalize_request_type(s: str) -> str:
    return (s or "").strip().lower()


def load_csv(path: str, encoding: str = "utf-8-sig") -> list[dict]:
    with open(path, newline="", encoding=encoding) as f:
        return list(csv.DictReader(f))


def compute_metrics(y_true: list[str], y_pred: list[str]) -> dict:
    """Per-class precision/recall/F1 plus overall accuracy."""
    labels = sorted(set(y_true) | set(y_pred))
    metrics = {}
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)

    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        metrics[label] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "support": sum(1 for t in y_true if t == label),
        }

    metrics["_overall_accuracy"] = round(correct / len(y_true), 3) if y_true else 0.0
    return metrics


def confusion_matrix(y_true: list[str], y_pred: list[str]) -> dict:
    labels = sorted(set(y_true) | set(y_pred))
    matrix = {t: {p: 0 for p in labels} for t in labels}
    for t, p in zip(y_true, y_pred):
        matrix[t][p] += 1
    return matrix


def print_confusion_matrix(matrix: dict, labels: list[str]):
    print(f"\n{'':20}" + "".join(f"{l[:12]:>14}" for l in labels))
    for t in labels:
        row = "".join(f"{matrix[t][p]:>14}" for p in labels)
        print(f"{t[:20]:20}{row}")


def evaluate(predictions_path: str, ground_truth_path: str):
    preds = load_csv(predictions_path)
    truth = load_csv(ground_truth_path)

    if len(preds) != len(truth):
        print(f"WARNING: row count mismatch — predictions={len(preds)}, ground_truth={len(truth)}",
              file=sys.stderr)

    n = min(len(preds), len(truth))
    y_status_true = [normalize_status(truth[i].get("Status", truth[i].get("status", ""))) for i in range(n)]
    y_status_pred = [normalize_status(preds[i].get("status", "")) for i in range(n)]

    y_reqtype_true = [normalize_request_type(truth[i].get("Request Type", truth[i].get("request_type", ""))) for i in range(n)]
    y_reqtype_pred = [normalize_request_type(preds[i].get("request_type", "")) for i in range(n)]

    print("=" * 70)
    print("STATUS METRICS")
    print("=" * 70)
    status_metrics = compute_metrics(y_status_true, y_status_pred)
    overall_acc = status_metrics.pop("_overall_accuracy")
    for label, m in status_metrics.items():
        print(f"  {label:15} precision={m['precision']:.3f}  recall={m['recall']:.3f}  "
              f"f1={m['f1']:.3f}  support={m['support']}")
    print(f"  Overall accuracy: {overall_acc:.3f} ({int(overall_acc*n)}/{n})")

    labels = sorted(set(y_status_true) | set(y_status_pred))
    print_confusion_matrix(confusion_matrix(y_status_true, y_status_pred), labels)

    print("\n" + "=" * 70)
    print("REQUEST TYPE METRICS")
    print("=" * 70)
    reqtype_metrics = compute_metrics(y_reqtype_true, y_reqtype_pred)
    overall_acc2 = reqtype_metrics.pop("_overall_accuracy")
    for label, m in reqtype_metrics.items():
        print(f"  {label:15} precision={m['precision']:.3f}  recall={m['recall']:.3f}  "
              f"f1={m['f1']:.3f}  support={m['support']}")
    print(f"  Overall accuracy: {overall_acc2:.3f} ({int(overall_acc2*n)}/{n})")

    print("\n" + "=" * 70)
    print("MISMATCHES (status)")
    print("=" * 70)
    for i in range(n):
        if y_status_true[i] != y_status_pred[i]:
            issue = preds[i].get("issue", "")[:60]
            print(f"  Row {i+1}: expected={y_status_true[i]:12} got={y_status_pred[i]:12} | {issue}...")


def main():
    parser = argparse.ArgumentParser(description="Evaluate triage agent predictions against ground truth")
    parser.add_argument("--predictions", required=True, help="Path to your output CSV")
    parser.add_argument("--ground-truth", required=True, help="Path to CSV with expected Status/Request Type columns")
    args = parser.parse_args()
    evaluate(args.predictions, args.ground_truth)


if __name__ == "__main__":
    main()