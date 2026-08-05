import json
import time
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict

METRICS_PATH = Path(__file__).resolve().parent.parent / "metrics.jsonl"

# Gemini Flash approximate pricing (USD per 1M tokens) — update if pricing changes
INPUT_COST_PER_M = 0.10
OUTPUT_COST_PER_M = 0.40


@dataclass
class CallMetric:
    stage: str              # "classify" or "respond"
    duration_s: float
    input_tokens: int = 0
    output_tokens: int = 0
    cache_hit: bool = False
    error: str = ""

    @property
    def estimated_cost_usd(self) -> float:
        if self.cache_hit:
            return 0.0
        return (self.input_tokens / 1_000_000 * INPUT_COST_PER_M) + \
               (self.output_tokens / 1_000_000 * OUTPUT_COST_PER_M)


def log_metric(metric: CallMetric):
    record = asdict(metric)
    record["estimated_cost_usd"] = round(metric.estimated_cost_usd, 6)
    record["timestamp"] = time.time()
    with open(METRICS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


@contextmanager
def timed_call(stage: str, cache_hit: bool = False):
    """Usage:
        with timed_call("classify") as m:
            response = client.models.generate_content(...)
            m.input_tokens = response.usage_metadata.prompt_token_count
            m.output_tokens = response.usage_metadata.candidates_token_count
    """
    start = time.time()
    metric = CallMetric(stage=stage, duration_s=0.0, cache_hit=cache_hit)
    try:
        yield metric
    except Exception as e:
        metric.error = str(e)[:200]
        raise
    finally:
        metric.duration_s = round(time.time() - start, 3)
        log_metric(metric)


def summarize() -> dict:
    if not METRICS_PATH.exists():
        return {"error": "No metrics recorded yet"}

    records = []
    with open(METRICS_PATH, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    if not records:
        return {"error": "metrics.jsonl is empty"}

    total_cost = sum(r["estimated_cost_usd"] for r in records)
    total_calls = len(records)
    cache_hits = sum(1 for r in records if r["cache_hit"])
    live_calls = total_calls - cache_hits
    durations = [r["duration_s"] for r in records if not r["cache_hit"]]
    avg_latency = sum(durations) / len(durations) if durations else 0.0
    errors = sum(1 for r in records if r.get("error"))

    return {
        "total_calls": total_calls,
        "cache_hits": cache_hits,
        "live_calls": live_calls,
        "cache_hit_rate": round(cache_hits / total_calls, 3) if total_calls else 0,
        "total_estimated_cost_usd": round(total_cost, 4),
        "avg_cost_per_live_call_usd": round(total_cost / live_calls, 6) if live_calls else 0,
        "avg_latency_s": round(avg_latency, 3),
        "errors": errors,
    }


if __name__ == "__main__":
    stats = summarize()
    print(json.dumps(stats, indent=2))