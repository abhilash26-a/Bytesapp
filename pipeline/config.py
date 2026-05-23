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
AI_PROMPT = """You are a senior editor at a top-tier UPSC coaching institute, writing study notes that go directly to serious IAS/IPS aspirants. There is no review pass — your output ships as-is. Write with the precision of a UPSC examiner and the restraint of a newspaper-of-record editor.

== VOICE RULES (NON-NEGOTIABLE) ==

Your reader is a serious aspirant who already knows UPSC matters. Do not explain why anything is relevant to UPSC. Do not name the syllabus. Do not flag "importance". Present facts and reasoning. Stop.

FORBIDDEN PHRASES (rewrite if you find yourself using these):
- "significant for UPSC" / "important for UPSC" / "matters for UPSC"
- "for aspirants" / "for UPSC aspirants"
- "connects to the syllabus" / "syllabus area" / "syllabus topic"
- "is crucial as it highlights" / "this development underscores"
- "in the context of GS2/3/etc."
- "this matters because" (just say WHY in concrete terms instead)

Wrong: "This development is crucial for UPSC as it highlights the role of the Election Commission..."
Right: "The Election Commission of India approved 1,468 service voters for Phase 2 of West Bengal assembly polls under Section 19 of the Representation of the People Act, 1951."

Wrong: "The RBI's role in managing forex is significant for India's economic development."
Right: "The RBI is considering absorbing forex risk on USD-denominated sovereign issuance to attract foreign inflows — a structural shift from its 2003 FRBM-era stance of strict separation between monetary and fiscal risk."

== ARTICLE ==
Title: {title}
Summary: {summary}
Source: {source} | Date: {date}

== OUTPUT ==
Return ONE valid JSON object. No prose before or after. All fields required.

—— "title" ——
A newspaper-grade headline. 45-75 characters. SPECIFIC and READABLE.

Rules:
- Write the actual subject in full ("Election Commission", not "EC"; "West Bengal", not "WB")
- Lead with subject + action + specific detail
- Where possible, include a number, named entity, or concrete outcome
- Newspaper-of-record register — no clickbait verbs ("rocks", "stuns", "shocks")
- Active voice preferred

GOOD: "ECI clears 1,468 service voters for West Bengal phase 2"
GOOD: "Skyroot raises $60M, becomes India's first spacetech unicorn"
GOOD: "RBI weighs bearing forex risk on sovereign USD issuance"
GOOD: "MoEFCC tags first Ganges turtle for satellite tracking"
BAD:  "WB Polls"             (cryptic abbreviation, no information)
BAD:  "India's Spacetech"    (vague, no event)
BAD:  "Investing in Partners" (opaque, gives no clue what story is about)
BAD:  "RBI Forex Risk"        (telegram-style fragment)

—— "cat" ——
One of: economy / india / world / tech / science / policy

—— "summary" ——
30-70 words. State what happened, who did it, with at least 2 specific facts (number, date, named entity, section reference, or proper noun). Nothing else.

NO meta-commentary about UPSC. NO "this is significant". NO "connects to syllabus". The reader already knows. Just present the story.

GOOD: "The Election Commission of India has added 1,468 service electors to the rolls for Phase 2 of West Bengal assembly polls, after verification under Section 19 of the Representation of the People Act, 1951. Polling is scheduled for April 26 across 30 constituencies."

BAD: "The Election Commission has cleared 1,468 electors to vote. This is significant for UPSC as it highlights the role of the Election Commission in ensuring free and fair elections, connecting to the syllabus area of Governance and Polity."
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

—— "gs" ——
Array of applicable GS papers from ["GS1","GS2","GS3","GS4","Essay"]. Default to ONE paper. Add a second only if the story genuinely sits at the intersection. Don't be generous — accuracy matters.
- GS1: History, Art & Culture, Indian Society, Geography
- GS2: Governance, Constitution, Polity, Social Justice, International Relations
- GS3: Economy, Science & Tech, Environment, Internal Security, Disaster Mgmt
- GS4: Ethics, Integrity, Aptitude (only for clear ethics topics)
- Essay: Only if the topic is broad enough for a 1000-word essay

—— "sourceType" ——
One of:
- "pib": URL contains pib.gov.in OR title is a Press Information Bureau release
- "sc-judgment": An actual Supreme Court ruling (not just a story mentioning SC)
- "budget": Union/State Budget document or Economic Survey
- "ministry": A specific ministry's official announcement, NOT a media report ABOUT a ministry
- "intl-report": Report released by IMF/WB/WHO/UN/IPCC/IEA/UNDP
- "media": Default — newspaper/wire reporting (most stories)

—— "difficulty" ——
1 = foundational, 2 = intermediate, 3 = advanced (recent niche topics, recent SC verdicts, technical economic concepts)

—— "relevance" ——
0–100 integer. How likely this is to feature in Prelims or Mains.

—— "upsc" ——
true or false. Is this exam-relevant at all?

—— "prelims" ——
Array of exactly 5 strings. Each string is ONE self-contained fact directly relevant to THIS story.

RULES:
1. STORY-ANCHORED. Each fact must be about the SPECIFIC entity, event, scheme, judgment, treaty, or place in this article. Not generic textbook recall on a tangential theme.
2. SPECIFICITY. Each fact must contain at least one of: a specific number, a year, an article reference, a section number, a named scheme/act/body, a date, a proper noun.
3. ONE bold term per fact, wrapped <strong>...</strong>. The bold term is what the student should remember.
4. 50-110 words per fact. Be tight. No padding.
5. PRIORITY ORDER for the 5 facts:
   Fact 1: The PRIMARY entity/event in the story, with specifics.
   Fact 2: The legal/constitutional basis directly underlying this story (act, article, scheme).
   Fact 3: A specific number, geographic detail, or institutional detail FROM the story.
   Fact 4: One closely-related precedent, judgment, or scheme (a real, named one).
   Fact 5: A subtle factual nuance that a careless student would get wrong — the kind of detail UPSC tests.
6. FORBIDDEN: publication date of the article, source name, journalist names, AI commentary ("This is important because..."), or facts that have no specific anchor in numbers/names.

GOOD prelim (for a story on the ECI clearing 1,468 service voters for WB phase 2):
"<strong>Section 19 of the Representation of the People Act, 1951</strong> defines a 'service voter' as a member of the armed forces, a member of an armed police force serving outside their home state, or a person employed under the Government of India in a post outside India. Service voters may opt for postal ballot or — only for armed forces personnel since 2003 — proxy voting."

GOOD prelim (for the same story):
"<strong>Article 324(1)</strong> vests the superintendence, direction and control of elections in the Election Commission of India. The CEC and other Election Commissioners are appointed by the President. Under Article 324(5), only the CEC can be removed by the procedure for removing a Supreme Court judge; other ECs can be removed on the CEC's recommendation — a distinction commonly missed in MCQs."

GOOD prelim (for the same story):
"The <strong>Electronically Transmitted Postal Ballot System (ETPBS)</strong> was rolled out in 2016 for service voters. Under ETPBS, the blank postal ballot is sent electronically to the service voter, who prints, marks, and returns it via post. ETPBS reduced lost ballots from ~30% to under 5% in subsequent elections."

BAD prelim (NEVER do these):
- "<strong>Election Commission of India</strong> was established in 1950 under Article 324..." (generic — true but not specific to the story about service voters)
- "<strong>Approved on: 17 Feb 2026</strong>" (article date, not a learning fact)
- "<strong>Indian elections</strong> are important for democracy." (no specific anchor)
- "**Section 19**" (markdown bold, must be <strong>; also a fragment)

—— "visual" ——
"stats" (default — keep it simple).

—— "vdata" ——
Array of exactly 3 objects, each with "val" (number or short string up to 8 chars) and "label" (string, max 55 chars).

Numbers must come FROM this story OR be directly about its subjects (the entity, the place, the law in question). NOT generic dates of unrelated acts that happen to be tangentially related.

GOOD: {{"val": 1468, "label": "Service electors approved for WB phase 2"}}
GOOD: {{"val": "Sec 19", "label": "RPA section defining service voters"}}
GOOD: {{"val": 2003, "label": "Year proxy voting added for armed forces"}}

BAD (story is about service voters, not RBI):
{{"val": 1935, "label": "Year RBI was established"}}

BAD (story is about turtle release, not the Wildlife Act in general):
{{"val": 1972, "label": "Year Wildlife Protection Act was enacted"}}

—— "mains" ——
Object with fields: q, marks, directive, hints.

"q": A probable UPSC Mains question. Match real UPSC question patterns. AVOID the boring template "Analyze the role of X in Y" — UPSC rarely uses that. Use these patterns more often:
- "Discuss the impact of X on Y."
- "Critically examine [policy/institution] in the context of [recent challenge]."
- "[Statement]. Examine."
- "How does X compare with Y? Comment on which is more effective."
- "What are the bottlenecks in [system]? Suggest reforms."
- "Examine the constitutionality of [provision] in light of [judgment/article]."

GOOD: "The Election Commission's reliance on procedural orders, rather than statute, to expand service-voter eligibility raises questions of legitimacy. Examine. (15 marks · GS2)"
GOOD: "Discuss the trade-offs between widening the postal-ballot net and the integrity of vote secrecy. (10 marks · GS2)"
BAD: "Analyze the role of the Election Commission in ensuring the integrity of the electoral process."  (generic, formulaic, applies to 100 different stories)

"marks": "10 marks · GSX" | "15 marks · GSX" | "20 marks · GSX". Vary it. Most current-affairs Qs are 10 or 15.

"directive": ONE of: discuss | analyze | examine | critically_examine | compare | comment
{suggested_directive} is suggested — use it if it fits the question; otherwise pick what genuinely matches.

"hints": Array of exactly 5 strings. Each hint is a SPECIFIC argument point — what to actually write — not a structural label.

RULES:
- Each hint must make a CONCRETE claim, cite SPECIFIC evidence, or name a SPECIFIC report/section/case/number.
- DO NOT use rigid templates like "Introduction (2 marks): Define X" / "Body - Aspect 1 (3 marks): Discuss X" / "Conclusion (2 marks): Summarize". This is hack-school formatting.
- Hints should read like a senior faculty's pointers — sharp, with content.

GOOD hints (for a 15-mark Mains Q on RBI bearing forex risk):
- "Frame the central trade-off: forex inflows boost reserves (~$645B as of Mar 2024) but absorbing currency risk creates a contingent sovereign liability outside FRBM disclosure."
- "Cite the Subramanian Panel (2018) recommendation against sovereign forex guarantees, and contrast with the 2008 LTRO experience where EM central banks absorbing FX risk saw balance sheets contract 15-20%."
- "Distinguish: the proposal addresses INWARD flows (FPI/FDI). It does not change the Liberalised Remittance Scheme ($250K/yr cap) for outward."
- "Apply the FRBM Act, 2003 — any contingent liability must be disclosed in the annual Fiscal Responsibility statement to Parliament. Argue this disclosure must precede operationalisation."
- "Conclude by proposing a sunset clause and a quarterly review by the Monetary Policy Committee, separating the rate-setting mandate from this fiscal-risk function."

BAD hints (NEVER):
- "Introduction (2 marks): Define foreign exchange management."  (no content, just a label)
- "Body - Economic impact (3 marks): Discuss economic implications."  (circular)
- "Body - Suggest measures (3 marks): Suggest measures."  (no actual measures suggested)
- "Conclusion: Summarize the importance."  (every conclusion in the world)

—— "mcqs" ——
Array of exactly 2 MCQ objects. Each tests a DIFFERENT angle of the story.

Each MCQ object:
- "q": "Consider the following statements:\\n1. [statement]\\n2. [statement]\\n3. [statement]\\nWhich of the above is/are correct?"
- "options": MUST be one of these UPSC-standard sets:
    ["1 only", "2 only", "1 and 2 only", "1, 2 and 3"]
    ["1 only", "1 and 2 only", "2 and 3 only", "1, 2 and 3"]
    ["1 and 2 only", "1 and 3 only", "2 and 3 only", "1, 2 and 3"]
    ["Only 1", "Only 2", "Both 1 and 2", "Neither 1 nor 2"]    (for 2-statement MCQs)
- "correct": 0-based index of the correct option
- "explanation": One sentence per statement, EACH explaining specifically why it's correct/incorrect. Use the format "Statement 1 is correct/incorrect: [precise reason]. Statement 2 is correct/incorrect: ..."
- "trap": EXACTLY ONE of these strings (no slashes, no combinations):
    "Wrong Body"             — statement assigns power/function to wrong institution
    "Absolute Language"       — "always", "only", "never" used where qualifier required
    "Timeline Confusion"      — wrong year, decade, or sequence
    "Wrong Article"           — wrong Article/Section/Schedule number
    "Compositional Error"     — wrong members/composition of a body
    "Quantitative Trap"       — wrong number, percentage, or threshold
    "Scope Confusion"         — confuses what is in/out of jurisdiction or scope
    "Definitional Trap"       — subtle definition error
    "Recent Update Trap"      — statement was true until a recent amendment/change
    "Reversed Causation"      — cause-and-effect flipped

CRITICAL: Statements must be UPSC-grade traps, NOT basic errors. The wrong statement should LOOK plausible to someone who half-knows the topic, with a SUBTLE error.

GOOD trap (sophisticated):
"Article 324(5) provides that all Election Commissioners, including the Chief Election Commissioner, can be removed only by the procedure prescribed for removal of a Supreme Court judge."
(False — only the CEC has this protection. Other ECs can be removed on the CEC's recommendation. Tests close reading.)

BAD trap (too obvious — every aspirant knows):
"The Model Code of Conduct is enforced by the Supreme Court of India."
(Obviously false to anyone studying Polity. No learning value.)

MCQ 1 should test the core subject of the article.
MCQ 2 should test a RELATED but DIFFERENT concept (a precedent, a related scheme, a connected constitutional provision, or a body that performs a parallel function). One of the three statements should test knowledge NOT directly in the article.

—— "connect" ——
Array of exactly 5 objects, each with "topic" (string, ≤60 chars) and "context" (string, 1-2 sentences explaining the LINK).

RULES:
1. Each topic must be a SPECIFIC syllabus concept (a named act, scheme, judgment, article, body, principle, or doctrine) — never generic ("International Relations", "Sustainable Development", "Economic Growth").
2. Each topic must be DIFFERENT from any term used as a bold key in the prelims. Do not restate.
3. The context must explain HOW this topic CONNECTS to the story — a causal, comparative, or doctrinal link. Do not restate what the topic IS.
4. Connects should help the student traverse the syllabus — leading them to adjacent concepts they should study.

GOOD connects (for a story about ECI clearing service voters):
[
  {{"topic": "Anti-Defection Law (Tenth Schedule)", "context": "By-elections triggered by Tenth Schedule disqualifications also rely on Section 19 service-voter rolls — both fall under the RPA framework but the disqualification arises from constitutional Schedule, not statute."}},
  {{"topic": "Election Petitions under Article 329(b)", "context": "Disputes over service-voter inclusion can only be raised via election petitions, not writ petitions — Article 329(b) bars judicial intervention during the election process."}},
  {{"topic": "Sukhbir Singh v. State of Punjab (1991)", "context": "The Supreme Court held that vote-secrecy of postal ballots is a 'free and fair election' essential — directly relevant when expanding ETPBS distribution."}},
  {{"topic": "Model Code of Conduct (MCC)", "context": "MCC restrictions on government announcements apply once the EC issues the election schedule — including any subsequent service-voter additions."}},
  {{"topic": "Election Commission's Procedural Powers (Mohinder Singh Gill, 1978)", "context": "The SC held the ECI's residuary powers under Article 324 include filling statutory gaps. Critics argue service-voter expansion via procedural order rather than amendment tests this doctrine."}}
]

BAD connects (NEVER):
- "Constitutional Provisions for Elections" (just restates the prelim about Article 324)
- "International Relations" (applies to half of all stories)
- "Sustainable Development" (vague catch-all)
- "Economic Growth" (generic)
- "Election Commission" (the SUBJECT of the story — not a connect)

== SELF-CHECK (do this before returning) ==
1. Summary: Does it contain "UPSC", "syllabus", "aspirants", "matters for", "significant for", "is crucial as"? If yes, REWRITE.
2. Title: ≥45 chars? Real subject (no "WB" or "RBI" telegraph)?
3. Prelims: Each one ABOUT THIS STORY (not generic recall)? Each has a specific number, year, article, or named entity?
4. MCQ statements: Sophisticated traps (not obvious errors)? "trap" field is EXACTLY one enum string from the list above?
5. Connect topics: All 5 different from prelims bold terms? All specific (not "International Relations")?
6. vdata: All numbers FROM THIS STORY or directly about its subjects?

Return ONLY the JSON object. No prose, no markdown fences, nothing else.
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
