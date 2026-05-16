#!/usr/bin/env python3
"""
discover-paper.py — auto-discover a recent AI/ML arxiv paper for the
study-paper skill, deduped against ~/ai-research-studies/*/metadata.json
and ranked into a "matched + explore" mix.

Default: 5 candidates from the last 30 days across cs.LG / cs.AI / cs.CL,
3 matching your historical study interests + 2 in adjacent territory.

Stdlib only. No third-party deps.

CLI:
    python3 discover-paper.py                     # JSON to stdout (default 5 candidates)
    python3 discover-paper.py --pretty            # human-readable numbered menu
    python3 discover-paper.py --days N            # widen/narrow time window (default 30)
    python3 discover-paper.py --max-results N     # candidate count (default 5)
    python3 discover-paper.py --matched K         # split: K matched + (max - K) explore (default 3)
    python3 discover-paper.py --topic "kw1 kw2"   # override topic profile entirely
    python3 discover-paper.py --offset N          # pagination ("next" page)
    python3 discover-paper.py --studies-dir DIR   # alt location for prior studies
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}
ARXIV_API = "http://export.arxiv.org/api/query"
DEFAULT_STUDIES_DIR = Path.home() / "ai-research-studies"

STOPWORDS = {
    "the", "a", "an", "of", "for", "and", "or", "in", "on", "to", "with",
    "from", "by", "via", "is", "are", "as", "at", "be", "we", "our",
    "this", "that", "these", "those", "it", "its", "their", "they", "them",
    "can", "will", "may", "have", "has", "but", "not", "so", "if", "then",
    "into", "over", "under", "more", "less", "than", "such", "any", "all",
    "based", "using", "use", "uses", "new", "novel", "study", "paper",
    "approach", "method", "framework", "model", "models", "results",
}

# Always-on seed terms. These ensure the user's known directions are
# represented in the topic profile even if a particular keyword hasn't
# appeared in a study title yet.
SEED_TOPIC_TERMS = {
    "rl", "reinforcement", "rlhf", "rlaif", "grpo", "dpo", "ppo", "trpo",
    "alignment", "reward", "policy", "gradient", "value", "bellman",
    "reasoning", "agent", "agentic", "tool", "tools", "rlm", "recursive",
    "transformer", "attention", "moe", "mixture", "experts", "lora",
    "qlora", "fine", "tune", "tuning", "post", "training", "pretrain",
    "pretraining", "inference", "kv", "cache", "speculative", "decoding",
    "quantization", "int4", "int8", "diffusion", "flow", "matching",
    "constitutional", "ai", "rubric", "judge", "context", "long",
    "scale", "scaling", "law", "laws", "mdp", "kl", "entropy",
}


def _normalize_arxiv_id(raw: str) -> str:
    """Strip version + URL prefix to a bare ID like '2511.12345' or '2503.01234v2' -> '2503.01234'."""
    if not raw:
        return ""
    s = raw.strip()
    # Strip URL prefix
    s = re.sub(r"^https?://(www\.)?arxiv\.org/(abs|pdf)/", "", s, flags=re.IGNORECASE)
    s = s.replace(".pdf", "")
    # Strip version suffix
    s = re.sub(r"v\d+$", "", s)
    return s.strip()


def _normalize_title(t: str) -> str:
    if not t:
        return ""
    s = re.sub(r"\s+", " ", t.strip().lower())
    s = re.sub(r"[^a-z0-9\s]", "", s)
    return s.strip()


def _tokens(s: str) -> list[str]:
    """Lowercased token stream, no stopwords, length >= 3."""
    s = s.lower()
    raw = re.findall(r"[a-z][a-z0-9\-]+", s)
    return [t for t in raw if len(t) >= 3 and t not in STOPWORDS]


# ---------------------------------------------------------------- dedupe ---

def load_existing_studies(studies_dir: Path) -> dict[str, set[str]]:
    """Return {'arxiv_ids': set, 'titles': set} from all metadata.json files."""
    arxiv_ids: set[str] = set()
    titles: set[str] = set()
    if not studies_dir.exists():
        return {"arxiv_ids": arxiv_ids, "titles": titles}
    for meta_path in studies_dir.glob("*/metadata.json"):
        try:
            d = json.loads(meta_path.read_text())
        except Exception:
            continue
        if d.get("arxiv_id"):
            arxiv_ids.add(_normalize_arxiv_id(str(d["arxiv_id"])))
        if d.get("source_url"):
            arxiv_ids.add(_normalize_arxiv_id(str(d["source_url"])))
        if d.get("title"):
            titles.add(_normalize_title(str(d["title"])))
    return {"arxiv_ids": arxiv_ids, "titles": titles}


# --------------------------------------------------------- topic profile ---

def derive_topic_profile(studies_dir: Path, override: str | None) -> set[str]:
    if override:
        return set(_tokens(override)) | SEED_TOPIC_TERMS
    profile: set[str] = set(SEED_TOPIC_TERMS)
    if studies_dir.exists():
        for meta_path in studies_dir.glob("*/metadata.json"):
            try:
                d = json.loads(meta_path.read_text())
            except Exception:
                continue
            for field in ("title", "headline"):
                if d.get(field):
                    profile.update(_tokens(str(d[field])))
    return profile


# -------------------------------------------------------------- arxiv ---

def fetch_arxiv(max_results: int, days: int, offset: int) -> list[dict[str, Any]]:
    """Return list of candidate dicts. Stdlib-only HTTP."""
    cats = "cat:cs.LG+OR+cat:cs.AI+OR+cat:cs.CL"
    qs = (
        f"search_query={cats}"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&start={offset}&max_results={max_results}"
    )
    url = f"{ARXIV_API}?{qs}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "study-paper-skill/1.0 (https://github.com/pleyva2004/claude-skill-study-paper)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            xml_body = r.read()
    except (urllib.error.URLError, TimeoutError) as e:
        raise RuntimeError(f"arxiv API unreachable: {e}") from None

    root = ET.fromstring(xml_body)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out: list[dict[str, Any]] = []
    for entry in root.findall("a:entry", ATOM_NS):
        try:
            pub_str = entry.find("a:published", ATOM_NS).text
            pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            if pub_dt < cutoff:
                continue
            title = (entry.find("a:title", ATOM_NS).text or "").strip()
            title = re.sub(r"\s+", " ", title)
            summary = (entry.find("a:summary", ATOM_NS).text or "").strip()
            summary = re.sub(r"\s+", " ", summary)
            id_url = (entry.find("a:id", ATOM_NS).text or "").strip()
            arxiv_id = _normalize_arxiv_id(id_url)
            authors = [
                (a.find("a:name", ATOM_NS).text or "").strip()
                for a in entry.findall("a:author", ATOM_NS)
            ]
            cats = [
                c.attrib.get("term", "")
                for c in entry.findall("a:category", ATOM_NS)
                if c.attrib.get("term")
            ]
            out.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": summary,
                "published": pub_dt.isoformat(),
                "authors": authors,
                "categories": cats,
                "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            })
        except Exception:
            continue
    return out


# ------------------------------------------------------------- ranking ---

def score_candidate(c: dict[str, Any], profile: set[str]) -> float:
    title_toks = set(_tokens(c["title"]))
    abs_toks = set(_tokens(c["abstract"]))
    return 2.0 * len(title_toks & profile) + 1.0 * len(abs_toks & profile)


def split_matched_explore(
    candidates: list[dict[str, Any]],
    profile: set[str],
    matched_count: int,
    total: int,
) -> list[dict[str, Any]]:
    scored = [(score_candidate(c, profile), c) for c in candidates]
    scored.sort(key=lambda sc: (-sc[0], sc[1]["published"]), reverse=False)
    # ^ sort by score DESC, then published DESC: invert by sorting twice
    scored.sort(key=lambda sc: sc[1]["published"], reverse=True)
    scored.sort(key=lambda sc: sc[0], reverse=True)

    matched = [sc for sc in scored if sc[0] >= 1.0][:matched_count]
    matched_ids = {sc[1]["arxiv_id"] for sc in matched}
    explore_pool = [sc for sc in scored if sc[1]["arxiv_id"] not in matched_ids and sc[0] == 0.0]
    # explore: most-recent novel papers
    explore_pool.sort(key=lambda sc: sc[1]["published"], reverse=True)
    explore_count = total - len(matched)
    explore = explore_pool[:explore_count]

    # If matched is short of target, fill from leftover scored (excluding existing).
    if len(matched) + len(explore) < total:
        chosen_ids = {sc[1]["arxiv_id"] for sc in matched + explore}
        leftover = [sc for sc in scored if sc[1]["arxiv_id"] not in chosen_ids]
        for sc in leftover:
            if len(matched) + len(explore) >= total:
                break
            (matched if sc[0] >= 1.0 else explore).append(sc)

    presented: list[dict[str, Any]] = []
    rank = 1
    for tag, group in (("matched", matched), ("explore", explore)):
        for score, c in group:
            preview = c["abstract"]
            if len(preview) > 220:
                preview = preview[:220].rstrip() + "..."
            presented.append({
                "rank": rank,
                "tag": tag,
                "score": score,
                "arxiv_id": c["arxiv_id"],
                "title": c["title"],
                "authors": c["authors"],
                "published": c["published"],
                "categories": c["categories"],
                "abstract_preview": preview,
                "abs_url": c["abs_url"],
                "pdf_url": c["pdf_url"],
            })
            rank += 1
    return presented


# ----------------------------------------------------------- main flow ---

def discover(args: argparse.Namespace) -> dict[str, Any]:
    studies_dir = Path(args.studies_dir).expanduser()
    existing = load_existing_studies(studies_dir)
    profile = derive_topic_profile(studies_dir, args.topic)

    # Pull more than we need, then dedupe + rank.
    raw_max = max(args.max_results * 6, 50)
    days = args.days
    candidates = fetch_arxiv(max_results=raw_max, days=days, offset=args.offset)

    # Dedupe vs prior studies.
    deduped = []
    skipped = 0
    for c in candidates:
        if c["arxiv_id"] in existing["arxiv_ids"]:
            skipped += 1
            continue
        if _normalize_title(c["title"]) in existing["titles"]:
            skipped += 1
            continue
        deduped.append(c)

    # If no candidates after dedupe, expand window once to 90 days.
    expanded = False
    if not deduped and days < 90:
        expanded = True
        candidates = fetch_arxiv(max_results=raw_max, days=90, offset=args.offset)
        for c in candidates:
            if c["arxiv_id"] in existing["arxiv_ids"]:
                skipped += 1
                continue
            if _normalize_title(c["title"]) in existing["titles"]:
                skipped += 1
                continue
            deduped.append(c)

    presented = split_matched_explore(
        deduped,
        profile=profile,
        matched_count=args.matched,
        total=args.max_results,
    )

    return {
        "queried_at": datetime.now(timezone.utc).isoformat(),
        "search_window_days": 90 if expanded else days,
        "expanded_window": expanded,
        "topic_profile_size": len(profile),
        "candidates_seen": len(candidates),
        "candidates_after_dedupe": len(deduped),
        "skipped_duplicates": skipped,
        "presented": presented,
        "next_offset": args.offset + raw_max,
        "exhausted": len(presented) == 0,
    }


def print_pretty(result: dict[str, Any]) -> None:
    pres = result["presented"]
    if not pres:
        print(
            f"No new candidates (skipped {result['skipped_duplicates']} duplicates, "
            f"queried {result['candidates_seen']}). "
            "Try `--days 90` or paste a URL/PDF path directly."
        )
        return
    print(
        f"Top {len(pres)} candidates from the last {result['search_window_days']} days "
        f"(skipped {result['skipped_duplicates']} duplicates):"
    )
    print()
    for c in pres:
        authors = ", ".join(c["authors"][:3])
        if len(c["authors"]) > 3:
            authors += f" + {len(c['authors']) - 3} more"
        pub = c["published"][:10]
        cats = ", ".join(c["categories"][:3])
        tag = "MATCHED" if c["tag"] == "matched" else "EXPLORE"
        print(f"  [{c['rank']}] [{tag} score={c['score']:.0f}] {c['title']}")
        print(f"      {authors} · arxiv:{c['arxiv_id']} · {pub} · {cats}")
        print(f"      {c['abstract_preview']}")
        print(f"      {c['abs_url']}")
        print()
    print(
        "Reply with: 1-{n} to study, `next` for more, `topic <keywords>` to refine, "
        "or paste a URL/PDF path.".format(n=len(pres))
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--max-results", type=int, default=5)
    p.add_argument("--matched", type=int, default=3, help="Matched-bucket count (rest are explore)")
    p.add_argument("--topic", type=str, default=None)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--studies-dir", default=str(DEFAULT_STUDIES_DIR))
    p.add_argument("--pretty", action="store_true")
    args = p.parse_args()

    if args.matched > args.max_results:
        args.matched = args.max_results

    try:
        result = discover(args)
    except RuntimeError as e:
        err = {"error": str(e), "presented": [], "exhausted": True}
        if args.pretty:
            print(f"Error: {e}", file=sys.stderr)
        else:
            print(json.dumps(err, indent=2))
        return 2

    if args.pretty:
        print_pretty(result)
    else:
        print(json.dumps(result, indent=2))
    return 0 if result["presented"] else 1


if __name__ == "__main__":
    sys.exit(main())
