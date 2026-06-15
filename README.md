# APTIVA AI
## Intelligent Candidate Discovery & Ranking
### Redrob AI Hackathon — India.Runs Data & AI Challenge

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Add dataset
Place the hackathon ZIP file in `data/`:
```
d:\Aptiva AI\data\redrob_hackathon_dataset.zip
```
The app will auto-extract on first run. No manual extraction needed.

### 3. Run the ranker (primary deliverable)
```bash
python rank.py --candidates data/candidates.jsonl --out submission.csv
```
Or auto-detect from ZIP:
```bash
python rank.py --auto
```

### 4. Run the Streamlit demo
```bash
streamlit run app.py
```

---

## Architecture

```
APTIVA AI
├── rank.py              Primary deliverable — CLI ranker
├── app.py               Streamlit 6-page demo
├── config.yaml          Feature flags
│
├── core/
│   ├── jd_config.py     JD feature vector (all scoring targets)
│   ├── dataset_loader.py ZIP auto-detection + extraction
│   ├── scorer.py        6 component scorers + final score
│   ├── honeypot.py      Fraudulent profile detection
│   ├── behavioral.py    23-signal behavioral multiplier
│   ├── tfidf_engine.py  Career substance TF-IDF index
│   ├── hireability.py   Hireability Index™ (proprietary)
│   ├── skill_gap.py     Required/Present/Missing/Bonus skills
│   ├── reasoning.py     Template reasoning + AI insights
│   ├── judge_mode.py    Judge Mode verdicts
│   └── gemini_enricher.py Optional Gemini reasoning enrichment
│
└── ui/
    ├── styles.py         Apple-inspired CSS
    ├── components.py     Reusable UI components
    ├── charts.py         Plotly chart builders
    └── pages/
        ├── home.py           Rankings Dashboard
        ├── ai_analysis.py    AI Analysis (most important)
        ├── candidate_profile.py Candidate Deep Dive
        ├── comparison.py     Side-by-side comparison
        ├── judge_mode_page.py Judge Mode
        └── analytics.py      Analytics Dashboard
```

---

## Scoring Formula

| Component | Weight | Description |
|---|---|---|
| Title Match | 30% | Direct lookup against JD title dictionary |
| Skill Trust | 25% | Proficiency × Duration × Endorsements × Assessment |
| Career Substance | 20% | **Hybrid**: 0.7×TF-IDF + 0.3×Skill Relevance |
| Experience Window | 10% | Optimal: 6–8 years; JD target: 5–9 years |
| Education | 5% | Tier (1–4) × Degree level × Field relevance |
| Location | 5% | Preferred cities (Pune, Noida, Delhi, Hyderabad...) |
| Engagement | 5% | Completeness × Open-to-work × Response rate |

**Behavioral Multiplier** (0.10–1.25): Applied multiplicatively on the base score. Penalizes ghost candidates, high notice periods, low response rates. Boosts active, engaged, verified candidates.

---

## Hireability Index™

Proprietary single-score trust metric:

| Dimension | Weight | Source |
|---|---|---|
| Technical Fit | 35% | 40% title + 60% skills |
| Career Relevance | 25% | Hybrid career substance score |
| Behavior Signals | 20% | Behavioral multiplier normalized |
| Availability | 10% | Notice + last active + open-to-work |
| Trust Score | 10% | Verifications + completeness + assessments |

---

## Optional: Gemini Reasoning Enrichment

After ranking, optionally enhance reasoning quality:

```bash
# Set your API key
set GEMINI_API_KEY=your_key_here

# Run enrichment (offline step, never called during ranking)
python rank.py --candidates data/candidates.jsonl --out submission.csv --enrich-reasoning
```

The ranker **never** depends on Gemini. This is purely an offline quality improvement step.

---

## Compute Constraints (Hackathon)

| Constraint | Status |
|---|---|
| CPU only | ✓ No GPU required |
| ≤ 5 minutes | ✓ ~30–60 seconds for 100K candidates |
| ≤ 16 GB RAM | ✓ TF-IDF uses sparse matrices |
| No network during ranking | ✓ All scoring is local |

---

## Hackathon Deliverables

1. **`submission.csv`** — Top-100 candidates with: `candidate_id, rank, score, reasoning`
2. **`rank.py`** — The ranker producing the CSV
3. **Streamlit Demo** — `streamlit run app.py` (the APTIVA AI sandbox)
4. **This GitHub repo** — Full code + methodology

---

## Demo Flow (60 seconds)

1. Open `http://localhost:8501` → Rankings table loads automatically
2. See **Hireability Index™** for each candidate
3. Click any candidate → **AI Analysis** page
4. Open **Judge Mode** → see recruiter-style verdicts
5. Open **Compare** → side-by-side comparison
6. Open **Analytics** → dataset-wide insights
