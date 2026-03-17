"""
Bytes News Pipeline Configuration
RSS feeds, UPSC keyword scoring, and AI prompt templates.
"""

# ═══ RSS FEED SOURCES ═══
RSS_FEEDS = [
    # The Hindu
    {"url": "https://www.thehindu.com/news/national/feeder/default.rss", "source": "The Hindu", "weight": 1.3},
    {"url": "https://www.thehindu.com/opinion/editorial/feeder/default.rss", "source": "The Hindu Editorial", "weight": 1.5},
    {"url": "https://www.thehindu.com/opinion/op-ed/feeder/default.rss", "source": "The Hindu Op-Ed", "weight": 1.4},
    {"url": "https://www.thehindu.com/business/feeder/default.rss", "source": "The Hindu Business", "weight": 1.2},
    {"url": "https://www.thehindu.com/sci-tech/science/feeder/default.rss", "source": "The Hindu Science", "weight": 1.3},
    {"url": "https://www.thehindu.com/news/international/feeder/default.rss", "source": "The Hindu International", "weight": 1.2},

    # Indian Express
    {"url": "https://indianexpress.com/section/explained/feed/", "source": "IE Explained", "weight": 1.4},
    {"url": "https://indianexpress.com/section/india/feed/", "source": "Indian Express", "weight": 1.2},
    {"url": "https://indianexpress.com/section/business/feed/", "source": "IE Business", "weight": 1.1},
    {"url": "https://indianexpress.com/section/world/feed/", "source": "IE World", "weight": 1.1},

    # PIB (Government)
    {"url": "https://www.pib.gov.in/ViewRss.aspx?reg=3&lang=2", "source": "PIB", "weight": 1.5},

    # LiveMint
    {"url": "https://www.livemint.com/rss/news", "source": "LiveMint", "weight": 1.1},
    {"url": "https://www.livemint.com/rss/politics", "source": "LiveMint Politics", "weight": 1.2},
    {"url": "https://www.livemint.com/rss/industry", "source": "LiveMint Industry", "weight": 1.0},

    # Economic Times
    {"url": "https://economictimes.indiatimes.com/rssfeedsdefault.cms", "source": "Economic Times", "weight": 1.0},
    {"url": "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms", "source": "ET Economy", "weight": 1.2},
]

# ═══ UPSC RELEVANCE SCORING ═══

# Keywords scored by weight tiers
UPSC_KEYWORDS = {
    "high": [  # 5 points each
        "supreme court", "parliament", "lok sabha", "rajya sabha", "budget",
        "rbi", "reserve bank", "amendment", "constitutional", "commission",
        "tribunal", "niti aayog", "election commission", "finance commission",
        "fundamental rights", "directive principles", "monetary policy",
        "fiscal deficit", "fiscal policy", "gdp", "inflation", "deflation",
        "cop28", "cop29", "cop30", "unfccc", "paris agreement", "ndc",
        "biodiversity", "endangered species", "national park", "wildlife",
        "isro", "drdo", "nuclear", "missile", "satellite", "chandrayaan",
        "gaganyaan", "article 14", "article 21", "article 370",
        "raj bhavan", "president of india", "prime minister", "cabinet",
        "panchayati raj", "73rd amendment", "74th amendment",
        "gst", "goods and services tax", "fdi", "fii",
        "wto", "imf", "world bank", "un general assembly",
        "national green tribunal", "eia", "environmental impact",
        "ncert", "nep", "education policy", "right to education",
        # GS1 — History, Culture, Society
        "heritage site", "intangible cultural", "pvtg",
        "scheduled tribe", "women empowerment", "gender equality",
        # GS4 — Ethics
        "ethics", "integrity", "emotional intelligence", "aptitude",
    ],
    "medium": [  # 3 points each
        "government", "ministry", "scheme", "policy", "act", "bill", "governor",
        "india", "bilateral", "summit", "trade", "agreement", "treaty",
        "climate", "renewable", "solar", "hydrogen", "ev", "electric vehicle",
        "ai", "artificial intelligence", "semiconductor", "digital", "cyber",
        "data protection", "poverty", "health", "education", "tribal",
        "women", "reservation", "obc", "sc st", "scheduled caste",
        "census", "population", "demographic", "urbanization",
        "defence", "security", "border", "lac", "loc",
        "farmers", "agriculture", "msp", "procurement",
        "infrastructure", "railway", "highway", "port",
        "start-up", "unicorn", "fintech", "upi",
        "embargo", "sanctions", "tariff", "export", "import",
        "quad", "brics", "g20", "asean", "sco", "nato",
        "pli", "production linked", "make in india",
        "sustainable", "carbon", "emission", "green",
        "space", "quantum", "biotechnology", "genome",
        # GS1 — Culture, Society
        "culture", "archaeology", "monument", "historical",
        "society", "caste", "migration", "diaspora",
        "communalism", "secularism", "demographic dividend",
        # GS4 — Ethics, Governance
        "code of conduct", "whistleblower", "conflict of interest",
        "transparency", "accountability", "public service",
    ],
    "low": [  # 1 point each
        "technology", "science", "economy", "world", "global",
        "report", "study", "research", "development", "growth",
        "investment", "market", "stock", "industry", "sector",
        "reform", "initiative", "program", "project",
        "international", "foreign", "diplomatic",
        "environment", "pollution", "waste", "water",
        "energy", "power", "fuel", "oil", "gas",
    ],
}

# Articles containing these words are likely NOT UPSC-relevant
SKIP_KEYWORDS = [
    "cricket", "ipl", "bollywood", "celebrity", "entertainment",
    "horoscope", "astrology", "recipe", "cooking", "lifestyle",
    "fashion", "beauty", "gossip", "reality show", "movie review",
    "book review", "music review", "web series", "ott",
    "match score", "scorecard", "batting", "bowling",
    "wedding", "divorce", "dating",
    # Non-India political noise
    "illinois", "pritzker", "california governor", "texas governor",
    "florida governor", "new york governor", "state legislature",
    "pentagon contest", "spacex starlink",
    # US domestic politics (not relevant to UPSC IR)
    "democrat primary", "republican primary", "midterm election",
    "congressional hearing", "super pac",
    # Horse-race political coverage
    "opinion poll", "exit poll", "poll prediction", "election rally",
    "campaign trail", "vote share",
]

# Minimum relevance score to process an article (out of 100)
# 30 = matched a few UPSC keywords; filters out entertainment/sports noise
RELEVANCE_THRESHOLD = 30

# Days to keep stories in the active feed before archiving to monthly files
ACTIVE_DAYS = 30

# Maximum new stories to process per pipeline run
# Groq free tier: 12K TPM, ~2K tokens/call = ~6/min
# At 12s/call, 200 articles = ~40 min — fine for background GitHub Actions
MAX_NEW_PER_RUN = 200

# ═══ CATEGORY DETECTION ═══
CATEGORY_KEYWORDS = {
    "economy": ["gdp", "inflation", "rbi", "budget", "fiscal", "monetary", "trade",
                 "tax", "gst", "investment", "market", "bank", "finance", "economic",
                 "rupee", "dollar", "export", "import", "fdi", "stock", "nifty", "sensex"],
    "india": ["india", "delhi", "parliament", "lok sabha", "rajya sabha", "governor",
              "supreme court", "high court", "election", "bjp", "congress", "modi",
              "state government", "chief minister", "panchayat", "municipal"],
    "world": ["us ", "usa", "china", "russia", "europe", "eu ", "un ", "nato",
              "bilateral", "summit", "g20", "g7", "brics", "asean", "quad",
              "diplomatic", "foreign", "international", "global", "geopolitical"],
    "tech": ["ai", "artificial intelligence", "semiconductor", "chip", "digital",
             "cyber", "data", "5g", "6g", "quantum", "blockchain", "crypto",
             "startup", "unicorn", "app", "software", "cloud"],
    "science": ["isro", "nasa", "space", "satellite", "mission", "research",
                "discovery", "climate", "species", "hydrogen", "nuclear", "energy",
                "renewable", "solar", "wind", "battery", "genome", "vaccine"],
    "policy": ["act", "bill", "amendment", "regulation", "tribunal", "commission",
               "reservation", "quota", "nep", "eia", "notification", "ordinance",
               "fundamental rights", "constitutional", "judicial"],
}

# ═══ SOURCE TYPE DETECTION ═══
SOURCE_TYPE_RULES = {
    "budget": ["budget", "fiscal deficit", "finance bill", "economic survey",
               "union budget", "annual financial statement"],
    "pib": ["pib.gov.in"],
    "sc-judgment": ["supreme court", "high court", "bench", "verdict", "judgment",
                    "petition", "writ", "appeal", "constitutional bench"],
    "intl-report": ["imf", "world bank", "un report", "ipcc", "who report",
                    "undp", "wef", "fao", "unep", "oecd", "global report"],
    "ministry": ["ministry of", "cabinet approves", "government launches",
                 "rbi announces", "sebi", "niti aayog", "commission recommends"],
}

# ═══ AI PROMPT TEMPLATE ═══
AI_PROMPT = """You are a senior UPSC faculty member creating exam-preparation content from current affairs. Your content will be used by serious aspirants. Return ONLY valid JSON.

=== ARTICLE ===
Title: {title}
Summary: {summary}
Source: {source} | Date: {date}

=== OUTPUT FORMAT ===
Return a single JSON object with ALL these fields:

"title": Rewrite for UPSC relevance (max 60 chars)
"cat": One of: economy / india / world / tech / science / policy
"summary": 2-3 sentences. First sentence: what happened. Second: WHY it matters for UPSC. Third (optional): which syllabus area it connects to.
"gs": Array of ALL applicable GS papers. Use this guide:
  - GS1: History, Art & Culture, Society (social issues, women, population, urbanization, communalism, secularism, geographical features)
  - GS2: Governance, Constitution, Polity, IR (government policies, India & neighbours, bilateral/multilateral, international organizations)
  - GS3: Economy, Science & Tech, Environment, Security (economic development, agriculture, infrastructure, science, disaster management)
  - GS4: Ethics, Integrity, Aptitude (ethics in public life, attitude, emotional intelligence, case studies, corporate governance)
  IMPORTANT: Do NOT default to GS3. A story about a treaty = GS2. A story about tribal rights = GS1+GS2. A story about corruption = GS4. Think carefully.
"sourceType": One of: budget / pib / intl-report / sc-judgment / ministry / media
"difficulty": 1 (foundational) / 2 (intermediate) / 3 (advanced)
"relevance": 0-100 integer
"upsc": true/false

=== PRELIMS: 5 DEEP-KNOWLEDGE FACTS ===

You are writing for students who need to LEARN, not just read headlines. Each fact must teach something a student wouldn't know just from reading the article.

RULES:
- Each fact MUST be 2-3 complete sentences (minimum 15 words total)
- Each fact MUST contain one key term in <strong> tags (HTML only, NEVER markdown **)
- At least 4 of 5 facts MUST go BEYOND the article — add constitutional provisions, establishment years, related acts/schemes, geographical data, historical context, institutional mandates, or related precedents
- NEVER include: publication date, source name, "approved on [date]", or any article metadata
- NEVER return just a bold term or a sentence fragment

EXCELLENT prelims examples (THIS IS THE QUALITY STANDARD):

- "<strong>National Green Tribunal (NGT)</strong> was established in 2010 under the National Green Tribunal Act, 2010. It has its principal bench in New Delhi and four regional benches (Bhopal, Pune, Kolkata, Chennai). NGT is mandated to dispose of cases within 6 months, making it one of the fastest environmental courts globally."

- "<strong>Great Nicobar Island</strong> is the southernmost island of the Andaman and Nicobar archipelago, covering approximately 1,045 sq km. It is home to the Shompen tribe (population ~250), classified as a Particularly Vulnerable Tribal Group (PVTG) under the Ministry of Tribal Affairs. The island's Indira Point is the southernmost tip of India."

- "The <strong>Coastal Regulation Zone (CRZ) Notification, 2019</strong> replaced the 2011 notification and classifies the coast into CRZ-I (ecologically sensitive), CRZ-II (developed urban areas), CRZ-III (rural areas), and CRZ-IV (water area up to 12 nautical miles). CRZ-I prohibits new construction except for strategic projects cleared by the MoEFCC."

- "<strong>Article 48A</strong> (Directive Principles) directs the State to protect and improve the environment and safeguard forests and wildlife. Read with <strong>Article 51A(g)</strong> (Fundamental Duties), which makes it every citizen's duty to protect the natural environment. Together, these form the constitutional basis for environmental jurisprudence in India."

- "India's <strong>Indo-Pacific Oceans Initiative (IPOI)</strong> was launched at the East Asia Summit in 2019 with seven pillars: maritime security, maritime ecology, maritime resources, capacity building, disaster risk reduction, science & technology, and trade connectivity. The Great Nicobar project aligns with the maritime infrastructure pillar."

BAD prelims (NEVER do these):
- "**National Green Tribunal**" (just a term, no sentence — USELESS)
- "Source: **ET Economy**" (source name is not a fact)
- "Approved on: **17 Feb 2026**" (publication date is not a learning fact)
- "<strong>Trade agreement</strong> with the US" (fragment, teaches nothing)
- "<strong>GDP growth</strong> is strong" (vague, no data, no context)

=== MAINS ===
"mains": object with:
  - "q": A probable UPSC Mains question that tests analytical thinking and goes beyond surface-level recall. Frame it exactly as UPSC would — with a specific directive word.
  - "marks": "15 marks · GSx"
  - "directive": {suggested_directive} is suggested, but choose the best fit. MUST vary across stories:
    - discuss: policy debates with multiple stakeholder views
    - analyze: cause-effect in economic/scientific topics
    - examine: institutional mechanisms and their working
    - critically_examine: government schemes/policies needing evaluation
    - compare: bilateral relations, competing approaches
    - comment: opinion pieces, ethical dilemmas
  - "hints": Array of 5 STRUCTURED answer points. Each hint MUST be a complete sentence specifying WHAT to write and HOW MANY marks it carries. Follow this blueprint:

EXCELLENT hints example:
[
  "Introduction (2 marks): Define the National Green Tribunal, its establishment under the NGT Act 2010, and its constitutional basis in Article 48A and Article 51A(g).",
  "Body - Environmental concerns (3 marks): Discuss CRZ-I violations, mangrove destruction, impact on Shompen PVTG, coral reef ecosystems, and the Galathea National Park within the project zone.",
  "Body - Strategic importance (3 marks): Explain India's need for transshipment capacity (currently 75% of Indian cargo transships via Colombo/Singapore), Indo-Pacific maritime strategy, and counter to China's String of Pearls.",
  "Body - Institutional mechanism (3 marks): Analyze the role of NGT vs. MoEFCC in environmental clearance — does NGT rubber-stamp or genuinely review? Cite Subhash Kumar v. State of Bihar (1991) on right to pollution-free environment.",
  "Conclusion (2 marks): Balance development with sustainability — suggest conditional clearance with mandatory biodiversity offsets, tribal consent (FPIC under UN Declaration), and independent monitoring."
]

BAD hints (NEVER do these):
- "Introduction to National Green Tribunal" (tells student nothing about WHAT to write)
- "Role in environmental protection" (vague, no specific content)
- "Challenges in balancing economic development" (generic, applies to any topic)

=== MCQ ===
"mcqs": Single object (NOT array) with:
  - "q": "Consider the following statements:\\n1. [statement]\\n2. [statement]\\n3. [statement]\\nWhich of the above is/are correct?"
  - CRITICAL: At least 1 statement MUST test knowledge NOT directly stated in the article (constitutional provisions, related acts, institutional details)
  - At least 1 statement MUST be a common UPSC trap (absolute language like "always/only/never", wrong ministry, timeline confusion)
  - "options": Array of 4 strings (e.g., ["1 only", "1 and 2 only", "2 and 3 only", "1, 2 and 3"])
  - "correct": 0-based index of correct option
  - "explanation": For EACH statement, explain WHY it is correct or incorrect with specific evidence. Example: "Statement 1 is correct: NGT was indeed established in 2010. Statement 2 is INCORRECT: NGT has 5 benches (1 principal + 4 regional), not 3. Statement 3 is correct: Article 21 has been expanded to include environmental rights per M.C. Mehta v. Union of India."
  - "trap": UPSC trap type (Wrong Ministry / Absolute Language / Timeline Confusion / Scope Confusion / Reversed Causation)

=== VISUAL DATA: KEY NUMBERS TO REMEMBER ===
"visual": One of: stats / comparison / progress
"vdata": Array of 3 objects, each with "val" (number) and "label" (string)

Think: "What NUMBER would a student need to memorize for prelims?"

EXCELLENT vdata:
{{"val": 1045, "label": "Area of Great Nicobar Island (sq km)"}}
{{"val": 2010, "label": "Year NGT was established"}}
{{"val": 75, "label": "% of Indian cargo transshipped via foreign ports"}}
{{"val": 4, "label": "Number of NGT regional benches across India"}}
{{"val": 48, "label": "Article 48A — Directive Principle on environment"}}

BAD vdata (NEVER):
{{"val": 2026, "label": "Year of Approval"}} — news date, not a learning fact
{{"val": 17, "label": "Day of Approval (February)"}} — meaningless
{{"val": 12, "label": "Hour of Approval (IST)"}} — absurd
{{"val": 2026, "label": "Year of planned protests"}} — trivial metadata

=== CONNECT: SYLLABUS INTERLINKAGES ===
"connect": Array of 5 objects, each with "topic" (string) and "context" (string).

Each connect item must be a SPECIFIC UPSC syllabus term (not generic) with a one-line explanation of HOW it connects to this news story. This helps students do "rabbit hole learning" — discovering adjacent exam topics.

EXCELLENT connect examples (for an NGT/Great Nicobar story):
[
  {{"topic": "CRZ Notification 2019 & Coastal Zone Management", "context": "The project required CRZ clearance — a frequently tested topic in Environment & Ecology prelims and GS3 mains."}},
  {{"topic": "Particularly Vulnerable Tribal Groups (PVTGs)", "context": "The Shompen tribe of Great Nicobar is one of India's 75 PVTGs — connects to GS1 (society) and tribal rights under Fifth/Sixth Schedule."}},
  {{"topic": "Environmental Impact Assessment (EIA) Process", "context": "The project's EIA was challenged — understand the 4-stage EIA process (screening, scoping, public hearing, appraisal) for GS3."}},
  {{"topic": "India's Indo-Pacific Strategy & Maritime Infrastructure", "context": "Great Nicobar's strategic location near the Malacca Strait makes it key to India's Indo-Pacific maritime posture — relevant for GS2 (IR)."}},
  {{"topic": "Article 48A & 51A(g) — Constitutional Environmental Provisions", "context": "These Directive Principle and Fundamental Duty articles form the constitutional basis for environmental protection — tested in Polity prelims."}}
]

BAD connect (NEVER do these):
- "Environmental Protection" (too vague — which aspect? which act? which article?)
- "Sustainable Development" (appears in every other story — not specific)
- "Infrastructure Development" (generic, doesn't help the student study anything specific)
- "International Relations" (applies to 50% of stories — useless as a study pointer)
"""

# ═══ DIRECTIVE DISTRIBUTION ═══
# Target distribution of mains directives across stories
DIRECTIVE_DISTRIBUTION = {
    "discuss": 0.20,
    "analyze": 0.25,
    "examine": 0.15,
    "critically_examine": 0.15,
    "compare": 0.10,
    "comment": 0.15,
}


def suggest_directive(existing_directives):
    """Given directives already used, return the most underrepresented one."""
    from collections import Counter
    if not existing_directives:
        return "discuss"
    counts = Counter(existing_directives)
    total = max(len(existing_directives), 1)
    best = "discuss"
    best_gap = -1
    for d, target in DIRECTIVE_DISTRIBUTION.items():
        actual = counts.get(d, 0) / total
        gap = target - actual
        if gap > best_gap:
            best_gap = gap
            best = d
    return best


# ═══ VISUAL DATA GENERATION HINTS ═══
VISUAL_HINTS = {
    "stats": "Use when the article has 3-4 key numeric metrics. vdata format: [{val, label}]",
    "comparison": "Use when comparing countries, entities, or before/after. vdata format: [{flag, name, val, hl?}]",
    "progress": "Use when showing timeline or progress data. vdata format: [{label, val, pct}]",
}
