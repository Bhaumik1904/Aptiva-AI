FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose Streamlit port
EXPOSE 8501

# Default command: run the ranker
# Override with: docker run ... python rank.py --candidates /data/candidates.jsonl
CMD ["python", "rank.py", "--candidates", "/data/candidates.jsonl", "--out", "/data/submission.csv"]

# To run Streamlit demo:
# docker run -p 8501:8501 aptiva-ai streamlit run app.py --server.address 0.0.0.0
