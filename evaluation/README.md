# APTIVA AI — Ranking Evaluation Framework

Standalone evaluation framework for measuring ranking quality against ground truth labels.
Zero dependency on the ranking engine — evaluation is fully independent.

---

## Files

| File | Purpose |
|---|---|
| `../evaluate.py` | Main evaluation script — run this |
| `create_sample_labels.py` | Generates bootstrap labels from `sample_candidates.json` |
| `sample_ground_truth.csv` | Pre-labelled 50-candidate sample (title-only heuristic) |

---

## Quick Start

```bash
# Step 1: Evaluate submission against sample labels
python evaluate.py \
  --predictions submission.xlsx \
  --ground-truth evaluation/sample_ground_truth.csv

# Step 2: Verbose output (per-candidate relevance breakdown)
python evaluate.py \
  --predictions submission.xlsx \
  --ground-truth evaluation/sample_ground_truth.csv \
  --verbose

# Step 3: Save report to file
python evaluate.py \
  --predictions submission.xlsx \
  --ground-truth evaluation/sample_ground_truth.csv \
  --out evaluation/report.txt

# Step 4: Custom K values
python evaluate.py \
  --predictions submission.xlsx \
  --ground-truth evaluation/sample_ground_truth.csv \
  --k 5 10 25 50

# Step 5: JSON metrics output (for scripting)
python evaluate.py \
  --predictions submission.xlsx \
  --ground-truth evaluation/sample_ground_truth.csv \
  --json
```

---

## Ground Truth Format

The ground truth CSV must have exactly two required columns:

```
candidate_id,relevance[,title,note]
CAND_0000031,2,Recommendation Systems Engineer,manually verified
CAND_0000001,1,Backend Engineer,adjacent
CAND_0000002,0,Operations Manager,not relevant
```

| Column | Required | Description |
|---|---|---|
| `candidate_id` | ✅ | Must match `CAND_XXXXXXX` format |
| `relevance` | ✅ | Integer 0, 1, 2, or 3 (see scale below) |
| `title` | Optional | For human review reference |
| `note` | Optional | Annotation comments |

### Relevance Scale

| Score | Label | Description |
|---|---|---|
| **3** | Highly Relevant | Senior/Staff/Lead AI/ML/NLP Engineer — exact JD match |
| **2** | Relevant | AI/ML/NLP Engineer, Applied Scientist, Data Scientist — meets most JD criteria |
| **1** | Adjacent | Software/Data/Backend Engineer — technical but not AI/ML core |
| **0** | Not Relevant | Civil Engineer, Accountant, HR Manager, Honeypot — no JD alignment |

**Relevance threshold for MAP, P@K, MRR:** `rel >= 1` (any score above 0 is "retrieved relevant").

---

## How to Create Ground Truth Labels

### Option A — Manual Expert Annotation (Gold Standard)

1. Take the top-20 candidates from your submission.xlsx
2. For each candidate, review: title, skills, career history, years of experience
3. Assign a relevance score 0–3 using the scale above
4. Save as `evaluation/my_ground_truth.csv`
5. Run: `python evaluate.py --predictions submission.xlsx --ground-truth evaluation/my_ground_truth.csv`

**Estimated time:** 30–45 minutes for 20 candidates, 1.5 hours for 50 candidates.

### Option B — Bootstrap from Title Heuristic (Starting Point)

```bash
# Auto-generates labels from sample_candidates.json using title matching
python evaluation/create_sample_labels.py
# Output: evaluation/sample_ground_truth.csv
```

⚠️ These are **bootstrap labels only** — they use title matching alone and must be manually reviewed and corrected before use as definitive ground truth.

### Option C — Use Sample Ground Truth Directly

`evaluation/sample_ground_truth.csv` contains pre-generated labels for all 50 sample candidates. Run evaluation immediately:

```bash
python evaluate.py \
  --predictions submission.xlsx \
  --ground-truth evaluation/sample_ground_truth.csv
```

> **Note:** The 50-candidate sample contains only 1 AI/ML candidate (Recommendation Systems Engineer). Most of the sample was deliberately filled with honeypots and non-AI profiles to test the Relevance Gate. An evaluation against this sample primarily measures honeypot avoidance, not internal ranking quality.
>
> For a meaningful NDCG score, label the **actual top-100 predicted candidates** and use those as ground truth.

---

## Metric Definitions

### NDCG@K — Normalised Discounted Cumulative Gain at K

**Challenge weight: NDCG@10 = 50%, NDCG@50 = 30%**

Measures ranking quality at position K. Rewards placing highly-relevant candidates at the top. Uses a logarithmic discount (rank 1 is worth twice rank 3, three times rank 7, etc.).

```
DCG@K     = Σ (2^rel_i - 1) / log2(i + 1)    for i = 1..K
NDCG@K    = DCG@K / IDCG@K
IDCG@K    = DCG of the ideal (perfect) ranking
```

**Interpretation:**
- `1.00` = Perfect ranking (most relevant candidates at top K positions)
- `0.90+` = Excellent
- `0.75–0.90` = Strong
- `0.60–0.75` = Adequate
- `< 0.60` = Ordering problems

**Why it matters:** NDCG penalises relevant candidates that appear too low in the list. A highly relevant candidate at rank 20 contributes far less than the same candidate at rank 2.

---

### MAP — Mean Average Precision

**Challenge weight: 15%**

Measures the average precision across all recall levels. For a single query (one JD), this is the Average Precision (AP) over all relevant candidates.

```
AP = (1 / R) × Σ P(k) × rel(k)    for k = 1..N
   where R = total relevant candidates, P(k) = precision at rank k,
         rel(k) = 1 if candidate at rank k is relevant, else 0
```

**Interpretation:**
- High MAP means relevant candidates appear early and consistently
- Low MAP means relevant candidates are scattered across the ranked list

---

### Precision@K — P@10

**Challenge weight: 5%**

Fraction of the top-K retrieved candidates that are relevant.

```
P@K = (# relevant candidates in top-K) / K
```

**Interpretation:**
- `P@10 = 1.0` means all top-10 candidates are relevant
- `P@10 = 0.5` means 5 of 10 top candidates are relevant

---

### Additional Metrics

| Metric | Formula | Use |
|---|---|---|
| **Recall@K** | (relevant in top-K) / (total relevant) | Coverage check |
| **MRR** | 1 / rank(first relevant) | First-result quality |
| **Precision@50** | (relevant in top-50) / 50 | Broader coverage |

---

## Interpreting Results

### Scenario 1 — Perfect Gate, Imperfect Ordering

```
NDCG@10 = 0.85   NDCG@50 = 0.70   MAP = 0.65   P@10 = 1.00
```

All top-10 are relevant (P@10=1.0), but some highly-relevant candidates are ranked lower than they should be (NDCG@10 < 1.0). The Relevance Gate is working. Ordering within the AI/ML pool needs improvement.

**Fix:** Improve career signal (e.g., switch TF-IDF to embeddings).

---

### Scenario 2 — Honeypot Contamination

```
NDCG@10 = 0.45   NDCG@50 = 0.55   MAP = 0.40   P@10 = 0.70
```

3 of top-10 candidates are non-relevant (P@10=0.70). Honeypots or irrelevant profiles in the top positions are suppressing NDCG heavily.

**Fix:** Strengthen the Relevance Gate or honeypot detection.

---

### Scenario 3 — Strong Overall

```
NDCG@10 = 0.92   NDCG@50 = 0.88   MAP = 0.85   P@10 = 1.00
```

Top-10 are all relevant, ranking order closely matches ground truth. Ready for submission.

---

## Notes on Ground Truth Coverage

The `evaluate.py` script handles **partial ground truth** gracefully:

- Candidates in `predictions.csv` but **NOT in `ground_truth.csv`** are treated as **relevance = 0** (conservative assumption)
- This means if you only label 20 candidates, the remaining 80 predicted candidates count as non-relevant
- NDCG will be lower than true NDCG if many relevant candidates are unlabelled

**Best practice:** Label at least the top-30 predicted candidates for a meaningful NDCG@10 score.

---

## Adding Evaluation Evidence to Submission

Once you have NDCG results, add them to the submission:

### In README.md
```markdown
## Ranking Quality — Self-Evaluation

| Metric | Score | Notes |
|---|---|---|
| NDCG@10 | 0.XX | Evaluated on 30-candidate manually-annotated sample |
| NDCG@50 | 0.XX | |
| MAP | 0.XX | |
| P@10 | 0.XX | All top-10 are verified AI/ML engineers |
```

### In `data/submission_metadata_template.yaml`
Add a `self_evaluation` section with your NDCG numbers.

---

## Metric Reference Card

| Challenge Metric | Weight | Your Script | Interpretation target |
|---|---|---|---|
| NDCG@10 | 50% | `NDCG@10` in report | > 0.75 = strong |
| NDCG@50 | 30% | `NDCG@50` in report | > 0.70 = adequate |
| MAP | 15% | `MAP` in report | > 0.65 = good |
| P@10 | 5% | `Precision@10` in report | 1.0 = perfect |
