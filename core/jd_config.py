"""
APTIVA AI — JD Feature Vector
Full configuration for the Senior AI Engineer job description at Redrob AI.
This is the single source of truth for all scoring decisions.
"""

JD_CONFIG = {
    # ── Title Scores (0.0 – 1.0) ─────────────────────────────────────────────
    "title_scores": {
        # Exact matches
        "senior ai engineer": 1.0,
        "senior ml engineer": 1.0,
        "senior machine learning engineer": 1.0,
        "ai engineer": 0.95,
        "ml engineer": 0.95,
        "machine learning engineer": 0.95,
        "nlp engineer": 0.90,
        "retrieval engineer": 0.90,
        "recommendation systems engineer": 0.90,
        "search engineer": 0.88,
        "applied ml engineer": 0.88,
        "llm engineer": 0.88,
        "applied scientist": 0.85,
        "research engineer": 0.80,
        "senior data scientist": 0.80,
        "data scientist": 0.75,
        "computer vision engineer": 0.65,
        "deep learning engineer": 0.75,
        "ai researcher": 0.78,
        "ml researcher": 0.78,
        "principal ml engineer": 1.0,
        "staff ml engineer": 0.95,
        # Adjacent roles (need career substance)
        "software engineer": 0.30,
        "backend engineer": 0.40,
        "data engineer": 0.35,
        "platform engineer": 0.25,
        "devops engineer": 0.05,
        "frontend engineer": 0.05,
        "full stack engineer": 0.20,
        # Non-tech (traps)
        "marketing manager": 0.00,
        "operations manager": 0.00,
        "hr manager": 0.00,
        "product manager": 0.15,
        "accountant": 0.00,
        "content writer": 0.00,
        "graphic designer": 0.00,
        "sales executive": 0.00,
        "customer support": 0.00,
        "business analyst": 0.10,
        "project manager": 0.10,
        # Non-AI engineering disciplines — explicit exclusions so the
        # generic "engineer" catch-all (0.25) in score_title() is never reached.
        # Titles listed here are matched BEFORE the fallback fires.
        "civil engineer":       0.00,  # Structural / construction — irrelevant
        "mechanical engineer":  0.00,  # Manufacturing / CAD — irrelevant
        "chemical engineer":    0.00,  # Process engineering — irrelevant
        "electrical engineer":  0.05,  # Mild adjacency (VLSI, signal processing)
        "qa engineer":          0.10,  # Testing adjacent; some ML QA overlap
        "embedded engineer":    0.10,  # Firmware; small overlap with edge AI
        "network engineer":     0.05,  # Infrastructure; minor ML-ops relevance
        "hardware engineer":    0.05,  # Silicon; minor edge inference relevance
    },

    # ── Core Required Skills (from must-have section of JD) ──────────────────
    "core_skills": [
        "embeddings", "sentence transformers", "sentence-transformers",
        "vector database", "vector db", "retrieval", "information retrieval",
        "ranking", "search ranking", "hybrid search",
        "faiss", "pinecone", "qdrant", "milvus", "weaviate", "elasticsearch",
        "bge", "e5", "openai embeddings", "hugging face", "huggingface",
        "transformers", "bert", "python", "nlp",
        "ndcg", "mrr", "map", "a/b testing", "evaluation framework",
        "learning to rank", "ltr", "semantic search",
    ],

    # ── Bonus / Nice-to-Have Skills ──────────────────────────────────────────
    "bonus_skills": [
        "lora", "qlora", "peft", "fine-tuning", "fine-tune", "fine tuning",
        "xgboost", "lightgbm", "langchain", "llm", "large language model",
        "recommendation systems", "recommender", "mlflow",
        "feature engineering", "scikit-learn", "sklearn",
        "pytorch", "tensorflow", "keras",
        "kafka", "spark", "redis",
        "weights & biases", "wandb", "bentoml", "mlops",
        "kubernetes", "docker", "ray", "triton",
        "reranking", "bm25", "dense retrieval", "sparse retrieval",
        "colbert", "splade", "ann", "hnsw",
    ],

    # ── Experience Targets ───────────────────────────────────────────────────
    "experience_target_min": 5,
    "experience_target_max": 9,
    "experience_sweet_spot_min": 6,
    "experience_sweet_spot_max": 8,

    # ── Preferred Locations ──────────────────────────────────────────────────
    "preferred_locations": [
        "pune", "noida", "delhi", "new delhi", "gurugram", "gurgaon",
        "hyderabad", "mumbai", "bangalore", "bengaluru", "india",
        "ncr", "delhi ncr",
    ],

    # ── Consulting Firms (JD disqualifier) ───────────────────────────────────
    "consulting_firms": [
        "tcs", "tata consultancy",
        "infosys", "infy",
        "wipro",
        "accenture",
        "cognizant", "ctsh",
        "capgemini",
        "hcl", "hcl technologies",
        "tech mahindra",
        "mphasis",
        "hexaware",
        "l&t infotech", "ltimindtree",
        "mindtree",
    ],

    # ── Preferred Industries ─────────────────────────────────────────────────
    "preferred_industries": [
        "ai/ml", "artificial intelligence", "machine learning",
        "fintech", "financial technology",
        "e-commerce", "ecommerce",
        "food delivery", "food tech",
        "transportation", "logistics",
        "saas", "software as a service",
        "product", "startup",
        "technology", "tech",
        "hrtech", "hr tech", "recruitment",
        "edtech", "healthtech", "proptech",
    ],

    # ── JD Career Keywords (for TF-IDF semantic matching) ───────────────────
    "jd_career_keywords": [
        "embedding", "embeddings", "vector", "retrieval", "ranking",
        "recommendation", "recommender", "nlp", "language model", "llm",
        "fine-tun", "fine tuning", "production", "deployed", "deployment",
        "a/b test", "evaluation", "ndcg", "mrr", "precision", "recall",
        "search", "inference", "pipeline", "scale", "latency",
        "feature engineering", "offline", "online", "learning to rank",
        "sentence transformer", "bert", "transformer", "semantic",
        "faiss", "pinecone", "milvus", "weaviate", "elasticsearch",
        "hybrid search", "dense", "sparse", "ann", "approximate nearest neighbor",
        "relevance", "rerank", "retrieval augmented", "rag",
        "query", "document", "index", "corpus",
        "model serving", "model inference", "real-time",
    ],

    # ── Risk Keywords (for risk scoring) ─────────────────────────────────────
    "risk_keywords": [
        "gap", "no production", "only research", "academic",
        "short tenure", "job hopping",
    ],
}
