#!/usr/bin/env python3
"""
Bytes News Pipeline
Fetches RSS feeds, scores for UPSC relevance, processes with AI, outputs stories.json
"""

import json
import os
import sys
import hashlib
import time
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup

from config import (
    RSS_FEEDS, UPSC_KEYWORDS, SKIP_KEYWORDS, RELEVANCE_THRESHOLD,
    ACTIVE_DAYS, MAX_NEW_PER_RUN, CATEGORY_KEYWORDS, SOURCE_TYPE_RULES,
    AI_PROMPT, suggest_directive
)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
STORIES_FILE = DATA_DIR / "stories.json"
ARCHIVE_DIR = DATA_DIR / "archive"

# API Keys (from environment)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")


def log(msg):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}")


# ═══ RSS FETCHING ═══

def fetch_all_feeds():
    """Fetch articles from all configured RSS feeds."""
    articles = []
    for feed_cfg in RSS_FEEDS:
        try:
            log(f"Fetching: {feed_cfg['source']} ...")
            feed = feedparser.parse(feed_cfg["url"])
            for entry in feed.entries:  # Process all entries from feed
                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                # Strip HTML tags from summary
                summary = BeautifulSoup(summary, "html.parser").get_text()
                link = entry.get("link", "")
                published = entry.get("published", entry.get("updated", ""))

                if not title:
                    continue

                articles.append({
                    "title": title,
                    "summary": summary[:500],
                    "link": link,
                    "published": published,
                    "source": feed_cfg["source"],
                    "source_weight": feed_cfg["weight"],
                    "feed_url": feed_cfg["url"],
                })
            log(f"  Got {len(feed.entries)} entries from {feed_cfg['source']}")
        except Exception as e:
            log(f"  ERROR fetching {feed_cfg['source']}: {e}")
    log(f"Total raw articles: {len(articles)}")
    return articles


# ═══ DEDUPLICATION ═══

def get_article_hash(title):
    """Generate a hash for deduplication."""
    normalized = re.sub(r'[^a-z0-9\s]', '', title.lower().strip())
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def deduplicate(articles, existing_hashes):
    """Remove duplicate articles and ones already in stories.json."""
    seen = set(existing_hashes)
    unique = []
    for article in articles:
        h = get_article_hash(article["title"])
        if h not in seen:
            seen.add(h)
            article["hash"] = h
            unique.append(article)
    log(f"After dedup: {len(unique)} unique new articles (removed {len(articles) - len(unique)} dupes)")
    return unique


# ═══ UPSC RELEVANCE SCORING ═══

def score_relevance(article):
    """Score an article 0-100 for UPSC relevance."""
    text = (article["title"] + " " + article["summary"]).lower()

    # Check skip keywords first
    for skip in SKIP_KEYWORDS:
        if skip in text:
            return 0

    score = 0
    for keyword in UPSC_KEYWORDS["high"]:
        if keyword in text:
            score += 5
    for keyword in UPSC_KEYWORDS["medium"]:
        if keyword in text:
            score += 3
    for keyword in UPSC_KEYWORDS["low"]:
        if keyword in text:
            score += 1

    # Apply source weight multiplier
    score = score * article.get("source_weight", 1.0)

    # Normalize to 0-100 scale (cap at 100)
    score = min(int(score * 2), 100)
    return score


def detect_category(article):
    """Detect the UPSC category of an article."""
    text = (article["title"] + " " + article["summary"]).lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw in text)
    if not any(scores.values()):
        return "india"  # default
    return max(scores, key=scores.get)


def detect_source_type(article):
    """Detect the source type by checking URL patterns first (strong signal),
    then title patterns (medium signal). Defaults to 'media' when nothing matches."""
    url = (article.get("link") or "").lower()
    title = (article.get("title") or "").lower()

    # SOURCE_TYPE_RULES is a list of (stype, rules_dict) in priority order
    rules_iter = SOURCE_TYPE_RULES if isinstance(SOURCE_TYPE_RULES, list) else SOURCE_TYPE_RULES.items()

    for stype, rules in rules_iter:
        # URL patterns are highest signal
        if isinstance(rules, dict):
            for u in rules.get("url_contains", []):
                if u in url:
                    # Special case: don't tag 'ministry' if URL was already a PIB match
                    if stype == "ministry" and ("pib.gov.in" in url or "pib.nic.in" in url):
                        continue
                    return stype
            for t in rules.get("title_contains", []):
                if t in title:
                    return stype
        elif isinstance(rules, list):
            # Legacy flat list (in case rules format wasn't migrated)
            for kw in rules:
                if kw in title or kw in url:
                    return stype
    return "media"


def filter_and_rank(articles):
    """Score, filter, and rank articles by UPSC relevance."""
    for article in articles:
        article["relevance_score"] = score_relevance(article)
        article["detected_cat"] = detect_category(article)
        article["detected_source_type"] = detect_source_type(article)

    # Filter by threshold
    relevant = [a for a in articles if a["relevance_score"] >= RELEVANCE_THRESHOLD]
    relevant.sort(key=lambda x: x["relevance_score"], reverse=True)

    log(f"After relevance filter (>={RELEVANCE_THRESHOLD}): {len(relevant)} articles")
    if relevant:
        log(f"  Top: [{relevant[0]['relevance_score']}] {relevant[0]['title'][:60]}")
        if len(relevant) > 1:
            log(f"  #2:  [{relevant[1]['relevance_score']}] {relevant[1]['title'][:60]}")

    return relevant[:MAX_NEW_PER_RUN]


# ═══ AI PROCESSING ═══

def call_groq(prompt, retries=3):
    """Call Groq API with Llama 3.3 70B. Retries on rate limit with backoff."""
    if not GROQ_API_KEY:
        return None
    for attempt in range(retries):
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 2000,
                    "response_format": {"type": "json_object"},
                },
                timeout=30,
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                return json.loads(content)
            elif resp.status_code == 429:
                wait = min(20 * (attempt + 1), 60)
                log(f"  Groq rate limited, waiting {wait}s (attempt {attempt+1}/{retries})...")
                time.sleep(wait)
                continue
            else:
                log(f"  Groq error {resp.status_code}: {resp.text[:200]}")
                return None
        except Exception as e:
            log(f"  Groq exception: {e}")
            return None
    return None


def call_gemini(prompt):
    """Call Google Gemini API as fallback."""
    if not GEMINI_API_KEY:
        return None
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 2000,
                    "responseMimeType": "application/json",
                },
            },
            timeout=30,
        )
        if resp.status_code == 200:
            content = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(content)
        else:
            log(f"  Gemini error {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        log(f"  Gemini exception: {e}")
        return None


def process_article_with_ai(article, existing_directives=None):
    """Send article to AI for UPSC analysis."""
    suggested = suggest_directive(existing_directives or [])
    prompt = AI_PROMPT.format(
        title=article["title"],
        summary=article["summary"][:400],
        source=article["source"],
        date=article.get("published", "today"),
        suggested_directive=suggested,
    )

    # Try Gemini first (more reliable), then Groq as fallback
    result = call_gemini(prompt)
    if result:
        log(f"  Processed via Gemini: {article['title'][:50]}")
        return result

    result = call_groq(prompt)
    if result:
        log(f"  Processed via Groq: {article['title'][:50]}")
        return result

    log(f"  FAILED to process: {article['title'][:50]} (no AI available)")
    return None


# ═══ QUALITY VALIDATION ═══

def validate_ai_output(ai_data, article):
    """Validate and repair AI-generated data. Returns cleaned data."""
    if not ai_data:
        return ai_data

    issues = []

    # --- Title Validation: enforce minimum quality ---
    title = (ai_data.get("title") or "").strip()
    if len(title) < 25:
        issues.append(f"Title too short ({len(title)} chars): '{title}' → using article title")
        ai_data["title"] = article.get("title", title)[:75]

    # --- story_fact + background validation ---
    sf = (ai_data.get("story_fact") or "").strip()
    if sf:
        words = len(sf.split())
        if words < 8 or words > 45:
            issues.append(f"story_fact wrong length ({words} words): clamping")
            # Trim to first sentence if too long
            if words > 45:
                ai_data["story_fact"] = re.split(r'(?<=[.!?])\s+', sf)[0][:300]
    bg = (ai_data.get("background") or "").strip()
    if bg:
        words = len(bg.split())
        if words > 80:
            # Trim to first 3 sentences
            sentences = re.split(r'(?<=[.!?])\s+', bg)
            ai_data["background"] = " ".join(sentences[:3])
            issues.append(f"background too long ({words} words): trimmed")

    # --- GS Tag Cap: ≥3 papers means hedge-tagging ---
    gs = ai_data.get("gs") or []
    if isinstance(gs, list) and len(gs) > 2:
        # Keep the first 2 (AI usually lists most relevant first)
        issues.append(f"GS over-tagged ({gs}): capping to 2")
        ai_data["gs"] = gs[:2]

    # --- Mains Q template detection (post-flag, doesn't block) ---
    mains = ai_data.get("mains", {})
    if mains:
        q = (mains.get("q") or "").strip()
        formulaic_starts = (
            "analyze the role of", "analyze the impact of",
            "analyze the significance of", "analyze the implications of",
            "discuss the importance of", "analyze the implications on",
        )
        if any(q.lower().startswith(s) for s in formulaic_starts):
            issues.append(f"Mains Q uses formulaic template: '{q[:80]}'")

    # --- Strip rigid hint template labels ---
    if mains and isinstance(mains.get("hints"), list):
        cleaned_hints = []
        # Patterns: "Introduction (2 marks):", "Body - X (3 marks):", "Conclusion (2 marks):"
        label_re = re.compile(
            r"^\s*(Introduction|Body\s*[-–—]\s*[^:]+|Conclusion)\s*\(\s*\d+\s*marks?\s*\)\s*[:\-–—]\s*",
            re.I,
        )
        for h in mains["hints"]:
            if not isinstance(h, str):
                continue
            new_h = label_re.sub("", h).strip()
            # If after stripping nothing meaningful remains, skip
            if len(new_h.split()) < 6:
                issues.append(f"Hint dropped (too thin after label strip): {h[:60]}")
                continue
            if new_h != h:
                issues.append("Hint label stripped")
            cleaned_hints.append(new_h)
        mains["hints"] = cleaned_hints[:5]
        ai_data["mains"] = mains

    # --- Summary Validation: strip UPSC meta-commentary ---
    summary = (ai_data.get("summary") or "").strip()
    if summary:
        # Sentences with these phrases are meta-commentary, not content.
        # Strip them from the summary; if nothing useful remains, fall back to article summary.
        forbidden_phrases = [
            r"\bfor UPSC\b",
            r"\bfor (UPSC )?aspirants\b",
            r"\bsignificant for UPSC\b",
            r"\bimportant for UPSC\b",
            r"\bcrucial for UPSC\b",
            r"\bmatters for UPSC\b",
            r"\b(this )?(matters|is significant|is crucial|is important) (because|as) it (highlights|underscores|relates|connects)\b",
            r"\b(connects? to|relates? to) the syllabus( area)?\b",
            r"\bsyllabus area of\b",
            r"\bin the context of GS[1-4]\b",
            r"\bthis development is crucial\b",
            r"\bthis development underscores\b",
            r"\bthis is significant for\b",
        ]
        sentences = re.split(r'(?<=[.!?])\s+', summary)
        kept = []
        for sent in sentences:
            if any(re.search(p, sent, re.I) for p in forbidden_phrases):
                continue
            kept.append(sent)
        cleaned = " ".join(kept).strip()
        if len(cleaned.split()) < 10:
            # Stripping removed too much — fall back
            issues.append(f"Summary mostly meta-commentary, falling back to article summary")
            ai_data["summary"] = (article.get("summary") or summary)[:300]
        elif cleaned != summary:
            issues.append("Summary stripped of UPSC meta-commentary")
            ai_data["summary"] = cleaned

    # --- Prelims Validation ---
    prelims = ai_data.get("prelims", [])
    clean_prelims = []
    source_name = article.get("source", "").lower()
    month_names = r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2}\b'

    for p in prelims:
        if not isinstance(p, str):
            continue
        # Normalize markdown bold to HTML strong
        p = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', p)

        stripped = re.sub(r'</?strong>', '', p).strip()

        # Reject if too short (need complete sentences, not fragments)
        if len(stripped.split()) < 10:
            issues.append(f"Prelims rejected (too short): {stripped[:60]}")
            continue

        # Reject if it contains publication date/source patterns
        if re.search(r'(^Source:|^Date:|^Published|Approved on:.*20\d{2}|signed on.*20\d{2}.*\d{2})', p, re.I):
            issues.append(f"Prelims rejected (date/source): {stripped[:60]}")
            continue

        # Reject if it's just "Source: <name>"
        if source_name and re.search(rf'^Source:?\s*.*{re.escape(source_name)}', stripped, re.I):
            issues.append(f"Prelims rejected (source mention): {stripped[:60]}")
            continue

        # Reject if the primary content is just a news date
        date_matches = re.findall(month_names, stripped, re.I)
        words_without_date = re.sub(month_names, '', stripped, flags=re.I).strip()
        if date_matches and len(words_without_date.split()) < 8:
            issues.append(f"Prelims rejected (date-centric): {stripped[:60]}")
            continue

        clean_prelims.append(p)

    ai_data["prelims"] = clean_prelims

    # --- Vdata Validation ---
    vdata = ai_data.get("vdata", [])
    clean_vdata = []
    current_year = datetime.now(timezone.utc).year

    for v in vdata:
        if not isinstance(v, dict):
            continue
        val = v.get("val")
        label = v.get("label", "").lower()

        # Reject non-numeric val
        if not isinstance(val, (int, float)):
            issues.append(f"Vdata rejected (non-numeric): {v}")
            continue

        # Reject trivial date-based values
        trivial_patterns = [
            "hour of", "day of", "month of", "date of",
            "year of approval", "year of incident",
            "year of planned", "year of inauguration",
            "year of announcement", "year of statement",
            "number of marks", "polling date",
            "date of the news", "year of the news",
        ]
        if any(tp in label for tp in trivial_patterns):
            issues.append(f"Vdata rejected (trivial): {label}")
            continue

        # Reject if val == current year and label suggests it's just the news year
        if val == current_year and "year" in label:
            has_historical = any(kw in label for kw in [
                "established", "signed", "enacted", "act", "founded",
                "launched", "created", "formed", "adopted",
            ])
            if not has_historical:
                issues.append(f"Vdata rejected (current year): {label}")
                continue

        # Reject tiny values (< 5) unless label suggests ranking/count/article number
        if isinstance(val, (int, float)) and val < 5 and val > 0:
            has_valid_small = any(kw in label for kw in [
                "rank", "position", "number of", "count", "article",
                "schedule", "bench", "tier", "phase", "pillar",
            ])
            if not has_valid_small:
                issues.append(f"Vdata rejected (trivially small): val={val}, {label}")
                continue

        clean_vdata.append(v)

    ai_data["vdata"] = clean_vdata

    # --- Connect Validation ---
    connect = ai_data.get("connect", [])
    generic_topics = {
        "economic growth", "sustainable development", "international relations",
        "infrastructure development", "economic diplomacy", "global governance",
        "environmental protection", "geopolitics", "global uncertainty",
        "digital transformation", "social development", "national security",
    }
    # Extract bold terms from prelims to detect connect-vs-prelim overlap
    prelim_bold_terms = set()
    for p in clean_prelims:
        for m in re.finditer(r'<strong>(.+?)</strong>', p, re.I):
            term = m.group(1).strip().lower()
            # Normalize: drop trailing punctuation, parens
            term = re.sub(r'\s*\(.+?\)\s*$', '', term).strip()
            if term:
                prelim_bold_terms.add(term)

    def norm_topic(t):
        return re.sub(r'\s*\(.+?\)\s*', '', t).strip().lower()

    clean_connect = []
    seen_topics = set()
    for c in connect:
        if isinstance(c, dict):
            topic = c.get("topic", "")
            context = c.get("context", "")
            if not topic or not context:
                issues.append(f"Connect rejected (missing fields): {c}")
                continue
            if topic.lower().strip() in generic_topics:
                issues.append(f"Connect rejected (too generic): {topic}")
                continue
            norm = norm_topic(topic)
            # Reject if topic restates a prelim's bold term
            if norm in prelim_bold_terms or any(norm in pb or pb in norm for pb in prelim_bold_terms if len(pb) > 8):
                issues.append(f"Connect rejected (restates prelim): {topic}")
                continue
            # Reject duplicates within connects
            if norm in seen_topics:
                issues.append(f"Connect rejected (duplicate): {topic}")
                continue
            seen_topics.add(norm)
            clean_connect.append(c)
        elif isinstance(c, str):
            clean_connect.append(c)
    if clean_connect:
        ai_data["connect"] = clean_connect

    # --- MCQ Validation ---
    # Canonical trap enum — AI sometimes invents labels; coerce them.
    TRAP_ENUM = {
        "wrong body", "wrong ministry", "absolute language", "timeline confusion",
        "wrong article", "wrong section", "compositional error", "quantitative trap",
        "scope confusion", "definitional trap", "recent update trap", "reversed causation",
    }
    TRAP_CANONICAL = {
        "wrong body": "Wrong Body",
        "wrong ministry": "Wrong Body",  # consolidate
        "absolute language": "Absolute Language",
        "timeline confusion": "Timeline Confusion",
        "wrong article": "Wrong Article",
        "wrong section": "Wrong Article",
        "compositional error": "Compositional Error",
        "quantitative trap": "Quantitative Trap",
        "scope confusion": "Scope Confusion",
        "definitional trap": "Definitional Trap",
        "recent update trap": "Recent Update Trap",
        "reversed causation": "Reversed Causation",
    }
    def coerce_trap(raw):
        if not raw:
            return None
        # Split on / and pick first matching enum value, else closest by substring
        parts = re.split(r'\s*/\s*', str(raw))
        for part in parts:
            key = part.strip().lower()
            if key in TRAP_CANONICAL:
                return TRAP_CANONICAL[key]
        # Fallback: substring match on canonical
        raw_lower = str(raw).lower()
        for canonical_key, canonical_val in TRAP_CANONICAL.items():
            if canonical_key in raw_lower:
                return canonical_val
        return "Definitional Trap"  # safe default

    mcqs = ai_data.get("mcqs", {})
    if isinstance(mcqs, dict) and mcqs:
        mcqs = [mcqs]
    if not isinstance(mcqs, list):
        mcqs = []
    valid_mcqs = []
    for mcq in mcqs:
        if not isinstance(mcq, dict):
            continue
        opts = mcq.get("options", [])
        correct = mcq.get("correct")
        if not (isinstance(opts, list) and len(opts) == 4 and isinstance(correct, int) and 0 <= correct <= 3):
            issues.append("MCQ rejected (malformed options or correct index)")
            continue
        # Coerce trap to enum
        original_trap = mcq.get("trap", "")
        mcq["trap"] = coerce_trap(original_trap)
        if original_trap and mcq["trap"] != original_trap:
            issues.append(f"Trap coerced: '{original_trap}' → '{mcq['trap']}'")
        valid_mcqs.append(mcq)
    ai_data["mcqs"] = valid_mcqs

    # --- Directive Normalization ---
    mains = ai_data.get("mains", {})
    if mains:
        directive = str(mains.get("directive", "discuss")).lower().strip()
        valid = {"discuss", "analyze", "examine", "critically_examine", "compare", "comment"}
        mapping = {"critically examine": "critically_examine", "critical": "critically_examine"}
        directive = mapping.get(directive, directive)
        if directive not in valid:
            directive = "discuss"
        mains["directive"] = directive
        ai_data["mains"] = mains

    if issues:
        log(f"  Validation: {len(issues)} issues fixed")
        for issue in issues[:5]:
            log(f"    - {issue}")

    return ai_data


# ═══ STORY CONSTRUCTION ═══

def build_story(article, ai_data, story_id):
    """Combine article data + AI analysis into a Bytes story object."""
    now = datetime.now(timezone.utc)

    # Store actual publish timestamp (ISO format) for frontend to compute relative time
    time_str = now.isoformat()
    if article.get("published"):
        try:
            pub = feedparser._parse_date(article["published"])
            if pub:
                from calendar import timegm
                pub_dt = datetime.fromtimestamp(timegm(pub), tz=timezone.utc)
                time_str = pub_dt.isoformat()
        except Exception:
            pass

    # Merge AI data with defaults — BACKEND source type takes priority (more reliable than AI guess)
    backend_source_type = article.get("detected_source_type", "media")
    ai_source_type = ai_data.get("sourceType", "media")
    # If backend detected anything other than media, trust it. AI only used when backend says media.
    final_source_type = backend_source_type if backend_source_type != "media" else ai_source_type

    story = {
        "id": story_id,
        "title": ai_data.get("title", article["title"][:60]),
        "cat": ai_data.get("cat", article["detected_cat"]),
        "upsc": ai_data.get("upsc", True),
        "time": time_str,
        "summary": ai_data.get("summary", article["summary"][:150]),
        # NEW: Story_fact = the single new fact. Background = the static framework.
        "story_fact": ai_data.get("story_fact", ""),
        "background": ai_data.get("background", ""),
        "visual": ai_data.get("visual", "stats"),
        "vdata": ai_data.get("vdata", []),
        "src": article["source"],
        "link": article.get("link", ""),
        "prelims": ai_data.get("prelims", []),
        "mains": ai_data.get("mains", {}),
        "connect": ai_data.get("connect", []),
        # Smart metadata
        "_hash": article.get("hash", ""),
        "_fetched": now.isoformat(),
        "_relevance": article.get("relevance_score", 50),
        "_gs": ai_data.get("gs", ["GS3"]),
        "_sourceType": final_source_type,
        "_difficulty": ai_data.get("difficulty", 2),
        "_directive": ai_data.get("mains", {}).get("directive", "discuss"),
        "_mcqs": ai_data.get("mcqs", []),
    }

    # Validate vdata
    if not story["vdata"] or not isinstance(story["vdata"], list):
        story["visual"] = "stats"
        story["vdata"] = [{"val": "NEW", "label": "Story"}]

    return story


# ═══ MAIN PIPELINE ═══

def load_existing_stories():
    """Load existing stories.json."""
    if STORIES_FILE.exists():
        try:
            with open(STORIES_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            log(f"Warning: Could not load existing stories: {e}")
    return []


def save_stories(stories):
    """Save stories to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(STORIES_FILE, "w") as f:
        json.dump(stories, f, indent=2, ensure_ascii=False)
    log(f"Saved {len(stories)} stories to {STORIES_FILE}")


def archive_old_stories(stories):
    """Move stories older than ACTIVE_DAYS to monthly archive files.
    Stories are never deleted — archived stories remain accessible."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(timezone.utc) - timedelta(days=ACTIVE_DAYS)
    keep = []
    archived_count = 0
    # Batch archive writes by month
    to_archive = {}

    for story in stories:
        fetched = story.get("_fetched", "")
        try:
            if fetched and datetime.fromisoformat(fetched) < cutoff:
                month_key = datetime.fromisoformat(fetched).strftime('%Y-%m')
                to_archive.setdefault(month_key, []).append(story)
                archived_count += 1
                continue
        except (ValueError, TypeError):
            pass
        keep.append(story)

    # Write each month's archive in one pass
    for month_key, month_stories in to_archive.items():
        month_file = ARCHIVE_DIR / f"{month_key}.json"
        existing = []
        if month_file.exists():
            try:
                with open(month_file) as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        # Deduplicate by hash within the archive
        existing_hashes = {s.get("_hash") for s in existing if s.get("_hash")}
        for s in month_stories:
            if s.get("_hash") not in existing_hashes:
                existing.append(s)
        with open(month_file, "w") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    if archived_count:
        log(f"Archived {archived_count} stories older than {ACTIVE_DAYS} days")

    # Write archive index so frontend can discover available months
    _write_archive_index()

    return keep


def _write_archive_index():
    """Write an index of available archive months with story counts."""
    if not ARCHIVE_DIR.exists():
        return
    index = []
    for f in sorted(ARCHIVE_DIR.glob("*.json"), reverse=True):
        if f.name == "index.json":
            continue
        try:
            with open(f) as fh:
                stories = json.load(fh)
            index.append({
                "month": f.stem,
                "file": f"archive/{f.name}",
                "count": len(stories),
            })
        except (json.JSONDecodeError, IOError):
            pass
    with open(ARCHIVE_DIR / "index.json", "w") as f:
        json.dump(index, f, indent=2)


def run_pipeline():
    """Main pipeline execution."""
    log("=" * 60)
    log("BYTES NEWS PIPELINE - Starting")
    log("=" * 60)

    # 1. Load existing stories
    existing = load_existing_stories()
    existing_hashes = {s.get("_hash", "") for s in existing if s.get("_hash")}
    next_id = max((s.get("id", 0) for s in existing), default=0) + 1
    log(f"Existing stories: {len(existing)}, next ID: {next_id}")

    # 2. Fetch RSS feeds
    raw_articles = fetch_all_feeds()
    if not raw_articles:
        log("No articles fetched. Exiting.")
        return

    # 3. Deduplicate
    unique = deduplicate(raw_articles, existing_hashes)
    if not unique:
        log("No new unique articles. Exiting.")
        return

    # 4. Score and filter for UPSC relevance
    top_articles = filter_and_rank(unique)
    if not top_articles:
        log("No articles met the relevance threshold. Exiting.")
        return

    # 5. Process with AI
    new_stories = []
    ai_available = bool(GROQ_API_KEY or GEMINI_API_KEY)
    existing_directives = [s.get("_directive", "discuss") for s in existing]

    if not ai_available:
        log("WARNING: No AI API keys configured. Generating basic stories without AI analysis.")

    for i, article in enumerate(top_articles):
        log(f"\nProcessing [{i+1}/{len(top_articles)}]: {article['title'][:60]}")

        if ai_available:
            ai_data = process_article_with_ai(article, existing_directives)
            if ai_data:
                ai_data = validate_ai_output(ai_data, article)
                existing_directives.append(
                    ai_data.get("mains", {}).get("directive", "discuss")
                )
            else:
                # Fall back to basic story without AI
                ai_data = _basic_story_data(article)
            time.sleep(12)  # Groq free: 12K TPM, ~2K tokens/call = ~5-6/min
        else:
            ai_data = _basic_story_data(article)

        story = build_story(article, ai_data, next_id)
        new_stories.append(story)
        next_id += 1

    log(f"\nGenerated {len(new_stories)} new stories")

    # 6. Merge with existing, archive old (no cap — archive handles rotation)
    all_stories = new_stories + existing
    all_stories = archive_old_stories(all_stories)

    # Re-assign sequential IDs
    for i, story in enumerate(all_stories):
        story["id"] = i + 1

    # 7. Save
    save_stories(all_stories)

    log("=" * 60)
    log(f"PIPELINE COMPLETE: {len(new_stories)} new, {len(all_stories)} total")
    log("=" * 60)


def _basic_story_data(article):
    """Generate a basic story without AI (fallback)."""
    return {
        "title": article["title"][:60],
        "cat": article["detected_cat"],
        "summary": article["summary"][:150],
        "upsc": article["relevance_score"] >= 50,
        "gs": ["GS3"],
        "sourceType": article["detected_source_type"],
        "difficulty": 2,
        "relevance": article["relevance_score"],
        "prelims": [],
        "mains": {},
        "connect": [],
        "mcqs": [],
        "visual": "stats",
        "vdata": [],
    }


def regenerate_existing():
    """Re-process all existing stories through the improved AI prompt."""
    existing = load_existing_stories()
    if not existing:
        log("No existing stories to regenerate.")
        return

    log(f"Regenerating {len(existing)} existing stories with improved prompt...")

    regenerated = []
    existing_directives = []

    for i, story in enumerate(existing):
        log(f"\nRegenerate [{i+1}/{len(existing)}]: {story['title']}")

        # Build article dict from existing story data
        article = {
            "title": story["title"],
            "summary": story["summary"],
            "source": story.get("src", "Unknown"),
            "published": story.get("_fetched", "today"),
            "link": story.get("link", ""),
            "hash": story.get("_hash", ""),
            "relevance_score": story.get("_relevance", 50),
            "detected_cat": story.get("cat", "india"),
            "detected_source_type": story.get("_sourceType", "media"),
        }

        ai_data = process_article_with_ai(article, existing_directives)
        if ai_data:
            ai_data = validate_ai_output(ai_data, article)
            existing_directives.append(
                ai_data.get("mains", {}).get("directive", "discuss")
            )
            new_story = build_story(article, ai_data, story["id"])
            # Preserve original metadata
            new_story["_hash"] = story.get("_hash", "")
            new_story["_fetched"] = story.get("_fetched", "")
            new_story["link"] = story.get("link", "")
            regenerated.append(new_story)
        else:
            log(f"  AI failed, keeping original")
            regenerated.append(story)

        time.sleep(12)  # Rate limit

    save_stories(regenerated)
    log(f"\nRegeneration complete: {len(regenerated)} stories updated")


def backfill_unenriched():
    """Re-process only stories that have empty prelims/MCQs."""
    stories = load_existing()
    unenriched = [s for s in stories if not s.get("prelims") or len(s.get("prelims", [])) == 0]
    log(f"Found {len(unenriched)} unenriched stories out of {len(stories)} total")

    if not unenriched:
        log("Nothing to backfill!")
        return

    existing_directives = [s.get("_directive", "discuss") for s in stories if s.get("prelims")]
    updated = 0

    for i, story in enumerate(unenriched):
        log(f"\n[{i+1}/{len(unenriched)}] Backfilling: {story.get('title', 'unknown')[:60]}")
        article = {
            "title": story.get("title", ""),
            "summary": story.get("summary", ""),
            "source": story.get("src", "media"),
            "published": story.get("time", ""),
            "detected_cat": story.get("cat", "india"),
            "detected_source_type": story.get("_sourceType", "media"),
            "relevance_score": story.get("_relevance", 50),
            "hash": story.get("_hash", ""),
        }

        ai_data = process_article_with_ai(article, existing_directives)
        if ai_data:
            ai_data = validate_ai_output(ai_data, article)
            existing_directives.append(ai_data.get("mains", {}).get("directive", "discuss"))
            new_story = build_story(article, ai_data, story["id"])
            new_story["_hash"] = story.get("_hash", "")
            new_story["_fetched"] = story.get("_fetched", "")
            new_story["link"] = story.get("link", "")
            # Replace in main stories list
            for j, s in enumerate(stories):
                if s["id"] == story["id"]:
                    stories[j] = new_story
                    break
            updated += 1
        else:
            log(f"  AI failed, skipping")

        time.sleep(8)

    save_stories(stories)
    log(f"\nBackfill complete: {updated}/{len(unenriched)} stories enriched")


def regenerate_recent(days=7):
    """Re-process stories from the last N days using the improved AI prompt.
    Useful after prompt changes — refreshes the active surface without
    re-doing the entire archive."""
    stories = load_existing_stories() if 'load_existing_stories' in globals() else load_existing()
    if not stories:
        log("No existing stories.")
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    targets = []
    for s in stories:
        f = s.get("_fetched", "")
        try:
            if datetime.fromisoformat(f.replace('Z', '+00:00')) >= cutoff:
                targets.append(s)
        except Exception:
            pass
    log(f"Regenerating {len(targets)} stories from the last {days} days "
        f"(out of {len(stories)} total)")
    if not targets:
        return

    existing_directives = [s.get("_directive", "discuss") for s in stories]
    updated = 0
    for i, story in enumerate(targets):
        log(f"\n[{i+1}/{len(targets)}] {story.get('title', '')[:70]}")
        article = {
            "title": story.get("title", ""),
            "summary": story.get("summary", ""),
            "source": story.get("src", "Unknown"),
            "published": story.get("_fetched", ""),
            "link": story.get("link", ""),
            "hash": story.get("_hash", ""),
            "relevance_score": story.get("_relevance", 50),
            "detected_cat": story.get("cat", "india"),
            "detected_source_type": story.get("_sourceType", "media"),
        }
        ai_data = process_article_with_ai(article, existing_directives)
        if ai_data:
            ai_data = validate_ai_output(ai_data, article)
            existing_directives.append(ai_data.get("mains", {}).get("directive", "discuss"))
            new_story = build_story(article, ai_data, story["id"])
            new_story["_hash"] = story.get("_hash", "")
            new_story["_fetched"] = story.get("_fetched", "")
            new_story["link"] = story.get("link", "")
            for j, s in enumerate(stories):
                if s["id"] == story["id"]:
                    stories[j] = new_story
                    break
            updated += 1
        else:
            log("  AI failed, keeping original")
        time.sleep(8)

    save_stories(stories)
    log(f"\nDone: {updated}/{len(targets)} stories regenerated")


def purge_empty_stories():
    """Remove stories that have no prelims (empty shells). They were generated
    when AI failed and they pollute the data file without ever being shown.
    The next pipeline run will re-fetch genuinely current stories."""
    stories = load_existing_stories() if 'load_existing_stories' in globals() else load_existing()
    before = len(stories)
    keep = [s for s in stories if s.get("prelims") and len(s.get("prelims", [])) > 0]
    removed = before - len(keep)
    if removed == 0:
        log("No empty stories to purge.")
        return
    log(f"Purging {removed} empty stories (kept {len(keep)} enriched)")
    save_stories(keep)
    log(f"data/stories.json now has {len(keep)} stories")


def _git_push_checkpoint(label: str):
    """Commit and push data/stories.json from within the pipeline script.
    Only runs when the GIT_PUSH_CHECKPOINT env var is set (i.e. in CI)."""
    import os, subprocess
    if not os.environ.get("GIT_PUSH_CHECKPOINT"):
        return
    try:
        subprocess.run(["git", "add", "../data/stories.json"], check=True)
        result = subprocess.run(
            ["git", "diff", "--staged", "--quiet"], capture_output=True
        )
        if result.returncode == 0:
            log(f"  [git] No changes at checkpoint — skipping commit")
            return
        subprocess.run(
            ["git", "commit", "-m", f"Regen checkpoint: {label}"],
            check=True,
        )
        subprocess.run(["git", "push"], check=True)
        log(f"  [git] Pushed checkpoint: {label}")
    except subprocess.CalledProcessError as e:
        log(f"  [git] Push failed (non-fatal): {e}")


def regenerate_all_enriched(from_index: int = 0, count: int = 0):
    """Regenerate enriched stories with the current prompt.

    Args:
        from_index: 0-based index into the sorted enriched-story list to start
                    from. Allows resuming after a timeout or failure.
        count:      How many stories to process. 0 = all remaining from
                    from_index. Keep to ~140 per run to stay within free-tier
                    API quotas (Gemini 1500 RPD, Groq 14400 RPD).
    """
    stories = load_existing_stories() if 'load_existing_stories' in globals() else load_existing()
    if not stories:
        log("No existing stories.")
        return
    targets = [s for s in stories if s.get("prelims") and len(s.get("prelims", [])) > 0]
    total_enriched = len(targets)
    log(f"Total enriched stories in corpus: {total_enriched} (out of {len(stories)} total)")

    # Apply batch window
    if from_index:
        targets = targets[from_index:]
        log(f"Resuming from index {from_index} → {len(targets)} stories remaining")
    if count:
        targets = targets[:count]
        log(f"Processing up to {count} stories this batch")

    log(f"This run will process {len(targets)} stories (indices {from_index}–{from_index + len(targets) - 1})")

    existing_directives = [s.get("_directive", "discuss") for s in stories]
    updated = 0
    for i, story in enumerate(targets):
        abs_idx = from_index + i + 1
        log(f"\n[{abs_idx}/{total_enriched}] {story.get('title', '')[:70]}")
        article = {
            "title": story.get("title", ""),
            "summary": story.get("summary", ""),
            "source": story.get("src", "Unknown"),
            "published": story.get("_fetched", ""),
            "link": story.get("link", ""),
            "hash": story.get("_hash", ""),
            "relevance_score": story.get("_relevance", 50),
            "detected_cat": story.get("cat", "india"),
            "detected_source_type": detect_source_type({
                "title": story.get("title", ""),
                "summary": story.get("summary", ""),
                "link": story.get("link", ""),
            }),
        }
        ai_data = process_article_with_ai(article, existing_directives)
        if ai_data:
            ai_data = validate_ai_output(ai_data, article)
            existing_directives.append(ai_data.get("mains", {}).get("directive", "discuss"))
            new_story = build_story(article, ai_data, story["id"])
            new_story["_hash"] = story.get("_hash", "")
            new_story["_fetched"] = story.get("_fetched", "")
            new_story["link"] = story.get("link", "")
            for j, s in enumerate(stories):
                if s["id"] == story["id"]:
                    stories[j] = new_story
                    break
            updated += 1
        else:
            log("  AI failed, keeping original")
        time.sleep(7)
        # Save + push every 50 stories so a timeout doesn't lose progress
        if (i + 1) % 50 == 0:
            save_stories(stories)
            label = f"{abs_idx}/{total_enriched} ({updated} rebuilt)"
            log(f"  ... checkpoint at {label}")
            _git_push_checkpoint(label)

    save_stories(stories)
    log(f"\nRegeneration complete: {updated}/{len(targets)} stories rebuilt")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--regenerate":
        regenerate_existing()
    elif len(sys.argv) > 1 and sys.argv[1] == "--backfill-unenriched":
        backfill_unenriched()
    elif len(sys.argv) > 1 and sys.argv[1] == "--regenerate-recent":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        regenerate_recent(days)
    elif len(sys.argv) > 1 and sys.argv[1] == "--regenerate-all-enriched":
        import argparse as _ap
        _p = _ap.ArgumentParser()
        _p.add_argument("--regenerate-all-enriched", action="store_true")
        _p.add_argument("--from-index", type=int, default=0)
        _p.add_argument("--count", type=int, default=0)
        _args, _ = _p.parse_known_args()
        regenerate_all_enriched(from_index=_args.from_index, count=_args.count)
    elif len(sys.argv) > 1 and sys.argv[1] == "--purge-empty":
        purge_empty_stories()
    else:
        run_pipeline()
