import re
from dataclasses import dataclass
from pathlib import Path
from rank_bm25 import BM25Okapi

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
WORD_RE = re.compile(r"[a-z0-9]+")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def tokenize(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


@dataclass
class Chunk:
    text: str
    source_path: str
    title: str
    source_url: str
    company: str
    category: str


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(raw)
    if not m:
        return {}, raw
    fm_text, body = m.group(1), raw[m.end():]
    fm = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"')
    return fm, body


def _category_from_path(path: Path, company_dir: Path, company: str) -> str:
    rel_parts = path.relative_to(company_dir).parts
    if len(rel_parts) == 1:
        return "general"
    if company == "claude" and rel_parts[0] == "claude" and len(rel_parts) == 2:
        return "general"
    if company == "claude" and rel_parts[0] == "claude" and len(rel_parts) > 2:
        return rel_parts[1]
    return rel_parts[0]


def _split_by_headers(text: str) -> list[str]:
    sections = re.split(r"\n(?=#{1,3}\s)", text)
    sections = [s.strip() for s in sections if len(s.strip()) > 30]
    return sections if sections else [text.strip()]


def build_corpus() -> list[Chunk]:
    chunks = []
    for company in ("hackerrank", "claude", "visa"):
        company_dir = DATA_DIR / company
        if not company_dir.exists():
            continue
        for path in company_dir.rglob("*.md"):
            try:
                raw = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if len(raw.strip()) < 30:
                continue
            fm, body = _parse_frontmatter(raw)
            title = fm.get("title", path.stem)
            source_url = fm.get("source_url", "")
            category = _category_from_path(path, company_dir, company)
            rel_source = str(path.relative_to(DATA_DIR))
            for section in _split_by_headers(body):
                chunks.append(Chunk(
                    text=section, source_path=rel_source, title=title,
                    source_url=source_url, company=company, category=category,
                ))
    return chunks


class Retriever:
    def __init__(self):
        self.chunks = build_corpus()
        tokenized = [tokenize(c.text) for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str, company: str | None = None, k: int = 5) -> list[tuple[Chunk, float]]:
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self.chunks, scores), key=lambda x: x[1], reverse=True)
        if company and company.lower() != "none":
            filtered = [r for r in ranked if r[0].company == company.lower()]
            ranked = filtered if filtered else ranked
        return ranked[:k]

    def confidence(self, results: list[tuple], query: str = "") -> float:
        if not results:
            return 0.0
        top_chunk, top_score = results[0]
        query_terms = set(tokenize(query))
        if not query_terms:
            return min(top_score / 20.0, 1.0)
        chunk_terms = set(tokenize(top_chunk.text))
        overlap_ratio = len(query_terms & chunk_terms) / len(query_terms)
        score_component = min(top_score / 20.0, 1.0)
        return round(score_component * overlap_ratio, 3)

    def categories(self, company: str) -> set[str]:
        return {c.category for c in self.chunks if c.company == company}