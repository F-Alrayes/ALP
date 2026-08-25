"""Offline intent matching.

No model downloads, no API calls: a blend of exact/fuzzy keyword hits
(rapidfuzz), fuzzy string similarity against the process name and description,
and a hand-rolled TF-IDF cosine over the process corpus. Every match carries the
evidence that produced it so the UI can show *why* something matched.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from .models import Process

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "can", "could", "do", "does", "for", "from",
    "get", "getting", "give", "has", "have", "help", "how", "i", "if", "in", "is", "it",
    "just", "like", "me", "my", "need", "needs", "of", "on", "or", "our", "please", "so",
    "someone", "that", "the", "their", "there", "this", "to", "up", "want", "was", "we",
    "what", "when", "which", "who", "will", "with", "would", "you", "your",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")

# How much each signal contributes to the final confidence.
WEIGHTS = {
    "keywords": 0.45,
    "name": 0.20,
    "tfidf": 0.25,
    "description": 0.10,
}


@dataclass
class Match:
    process_id: int
    process_name: str
    category: str
    confidence: float                       # 0-100
    matched_keywords: list[str] = field(default_factory=list)
    signals: dict[str, float] = field(default_factory=dict)

    @property
    def confidence_label(self) -> str:
        if self.confidence >= 70:
            return "High confidence"
        if self.confidence >= 45:
            return "Likely"
        if self.confidence >= 25:
            return "Weak"
        return "No usable match"

    def why(self) -> str:
        bits = []
        if self.matched_keywords:
            shown = ", ".join(f"'{k}'" for k in self.matched_keywords[:4])
            bits.append(f"matched {len(self.matched_keywords)} keyword(s): {shown}")
        if self.signals.get("name", 0) >= 0.5:
            bits.append(f"process name similarity {self.signals['name'] * 100:.0f}%")
        if self.signals.get("tfidf", 0) >= 0.15:
            bits.append(f"term-overlap score {self.signals['tfidf'] * 100:.0f}%")
        if self.signals.get("description", 0) >= 0.5:
            bits.append(f"description similarity {self.signals['description'] * 100:.0f}%")
        if not bits:
            return "Nothing in the request text lined up with a known process."
        joined = "; ".join(bits)
        return joined[0].upper() + joined[1:] + "."


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall((text or "").lower()) if t not in STOPWORDS and len(t) > 1]


def _corpus_for(process: Process) -> str:
    return " ".join(
        [process.name, process.category or "", process.keywords or "", process.description or ""]
    )


def _tf(tokens: list[str]) -> dict[str, float]:
    counts: dict[str, float] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0.0) + 1.0
    total = float(len(tokens)) or 1.0
    return {k: v / total for k, v in counts.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _word_matches(word: str, query_tokens: list[str]) -> bool:
    """One keyword word against the query's tokens, tolerant of inflections."""
    for token in query_tokens:
        if token == word:
            return True
        if fuzz.ratio(word, token) >= 88:
            return True
        # 'renew' vs 'renewal', 'reimburse' vs 'reimbursement'
        shorter, longer = sorted((word, token), key=len)
        if len(shorter) >= 4 and longer.startswith(shorter):
            return True
    return False


def _keyword_hits(query: str, query_tokens: list[str], keywords: list[str]) -> list[str]:
    """Exact phrase containment first, then a fuzzy fallback for typos/inflections."""
    lowered = query.lower()
    hits: list[str] = []
    for keyword in keywords:
        kw = keyword.strip().lower()
        if not kw:
            continue
        if kw in lowered:
            hits.append(keyword)
            continue
        words = [w for w in TOKEN_RE.findall(kw) if len(w) > 1]
        if not words:
            continue
        if len(words) > 1:
            if fuzz.partial_ratio(kw, lowered) >= 92:
                hits.append(keyword)
                continue
            covered = sum(1 for w in words if _word_matches(w, query_tokens))
            if covered / len(words) >= 0.75:
                hits.append(keyword)
        elif _word_matches(words[0], query_tokens):
            hits.append(keyword)
    seen: set[str] = set()
    unique = []
    for hit in hits:
        if hit.lower() not in seen:
            seen.add(hit.lower())
            unique.append(hit)
    return unique


def match_processes(session: Session, query: str, limit: int = 3) -> list[Match]:
    """Rank processes against a free-text request. Highest confidence first."""
    query = (query or "").strip()
    processes = session.query(Process).order_by(Process.name).all()
    if not query or not processes:
        return []

    query_tokens = tokenize(query)
    query_tf = _tf(query_tokens)

    # Document frequencies for the IDF term of TF-IDF.
    doc_tokens = {p.id: tokenize(_corpus_for(p)) for p in processes}
    doc_count = len(processes)
    df: dict[str, int] = {}
    for tokens in doc_tokens.values():
        for token in set(tokens):
            df[token] = df.get(token, 0) + 1
    idf = {t: math.log((1 + doc_count) / (1 + n)) + 1.0 for t, n in df.items()}

    query_vec = {t: v * idf.get(t, 1.0) for t, v in query_tf.items()}

    matches: list[Match] = []
    for process in processes:
        hits = _keyword_hits(query, query_tokens, process.keyword_list)
        # Saturating: three solid keyword hits is already a confident match.
        keyword_score = min(1.0, len(hits) / 3.0) if hits else 0.0

        name_score = fuzz.token_set_ratio(query.lower(), process.name.lower()) / 100.0
        desc_score = (
            fuzz.token_set_ratio(query.lower(), (process.description or "").lower()) / 100.0
        )

        doc_tf = _tf(doc_tokens[process.id])
        doc_vec = {t: v * idf.get(t, 1.0) for t, v in doc_tf.items()}
        tfidf_score = _cosine(query_vec, doc_vec)

        signals = {
            "keywords": keyword_score,
            "name": name_score,
            "tfidf": tfidf_score,
            "description": desc_score,
        }
        raw = sum(WEIGHTS[k] * signals[k] for k in WEIGHTS)
        # Fuzzy ratios sit well above zero even for unrelated text, so pull the
        # floor down before scaling the blend to a percentage.
        confidence = max(0.0, min(100.0, (raw - 0.12) / 0.72 * 100.0))

        matches.append(
            Match(
                process_id=process.id,
                process_name=process.name,
                category=process.category or "General",
                confidence=round(confidence, 1),
                matched_keywords=hits,
                signals={k: round(v, 4) for k, v in signals.items()},
            )
        )

    matches.sort(key=lambda m: (m.confidence, len(m.matched_keywords)), reverse=True)
    return matches[:limit]


def suggest_title(query: str, process_name: str | None) -> str:
    """A short human title for the drafted request."""
    text = " ".join((query or "").split())
    if not text:
        return process_name or "New request"
    if len(text) <= 70:
        return text.rstrip(".!?")
    return text[:67].rsplit(" ", 1)[0] + "..."
