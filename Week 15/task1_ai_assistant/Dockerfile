FROM python:3.12-slim

WORKDIR /app

# CPU-only torch first -- sentence-transformers depends on torch, and letting
# pip resolve it normally can pull a much larger CUDA-enabled build.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data
COPY ingest.py .

# Bake the embedding model into the image so first-request latency doesn't
# include a cold download, and so the container can run fully offline.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Build the FAISS index at image-build time from the bundled corpus.
RUN python ingest.py

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
