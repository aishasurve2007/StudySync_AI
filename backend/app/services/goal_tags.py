"""
Deterministic goal-tag extraction (spec §2).

`goal_tags` is the input to matching's `goal_similarity` (§4). It is
deliberately NOT AI-generated: this function runs on every profile
create/update so matching keeps working even if the AI provider is down.

Algorithm:
  1. Normalise text (lowercase, strip punctuation) from the goal + subjects.
  2. Match against a fixed vocabulary of canonical skill/subject tags, where
     each canonical tag has a list of aliases (incl. multi-word phrases and
     abbreviations like "ml" -> "machine learning").
  3. If nothing matches the vocabulary, fall back to content tokens with
     stopwords removed, so the result is never empty when there is signal.

Output is a sorted, de-duplicated list of canonical tags (lowercase).
"""
import re

# canonical_tag -> aliases (the canonical form is matched too)
_VOCABULARY: dict[str, list[str]] = {
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl", "neural network", "neural networks"],
    "artificial intelligence": ["artificial intelligence", "ai"],
    "data science": ["data science", "data analysis", "data analytics"],
    "statistics": ["statistics", "stats", "probability"],
    "mathematics": ["mathematics", "maths", "math", "calculus", "linear algebra"],
    "algorithms": ["algorithms", "algorithm", "dsa", "data structures"],
    "programming": ["programming", "coding"],
    "python": ["python"],
    "javascript": ["javascript", "js", "typescript", "ts"],
    "web development": ["web development", "web dev", "frontend", "front-end",
                        "backend", "back-end", "full stack", "fullstack", "react"],
    "databases": ["databases", "database", "sql", "postgres", "postgresql"],
    "interview": ["interview", "interviews", "placement", "placements"],
    "exam": ["exam", "exams", "test", "tests", "finals", "midterm", "midterms"],
    "certification": ["certification", "certificate", "cert"],
    "project": ["project", "projects", "portfolio", "dissertation", "thesis"],
    "physics": ["physics"],
    "chemistry": ["chemistry"],
    "biology": ["biology"],
    "economics": ["economics", "econ"],
    "finance": ["finance", "accounting"],
    "languages": ["spanish", "french", "german", "mandarin", "japanese"],
}

_STOPWORDS = {
    "the", "a", "an", "to", "for", "of", "and", "or", "my", "i", "in", "on",
    "with", "prepare", "preparing", "study", "studying", "learn", "learning",
    "get", "getting", "improve", "improving", "want", "need", "better", "up",
    "do", "doing", "be", "is", "am", "this", "that", "next", "ready",
}


def _normalise(text: str) -> str:
    text = text.lower()
    # keep word characters, spaces, and hyphens (so "front-end" survives)
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_goal_tags(current_goal: str | None, subjects: list[str] | None) -> list[str]:
    parts: list[str] = []
    if current_goal:
        parts.append(current_goal)
    if subjects:
        parts.extend(subjects)
    haystack = _normalise(" ".join(parts))
    if not haystack:
        return []

    tags: set[str] = set()
    for canonical, aliases in _VOCABULARY.items():
        for alias in aliases:
            # whole-word / whole-phrase match against the normalised text
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", haystack):
                tags.add(canonical)
                break

    if tags:
        return sorted(tags)

    # Fallback: no vocabulary hit -> emit meaningful content tokens.
    tokens = [t for t in haystack.split() if t not in _STOPWORDS and len(t) > 2]
    return sorted(set(tokens))
