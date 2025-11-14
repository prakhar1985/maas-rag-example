# Architecture & Tutorial: RAG with LiteMaaS

This document explains how this RAG (Retrieval-Augmented Generation) application works and how it uses LiteMaaS for AI capabilities.

## Table of Contents

- [What is RAG?](#what-is-rag)
- [Architecture Overview](#architecture-overview)
- [How LiteMaaS is Used](#how-litemaas-is-used)
- [Component Details](#component-details)
- [How It Works: Step by Step](#how-it-works-step-by-step)
- [Why This Architecture?](#why-this-architecture)

## What is RAG?

**RAG (Retrieval-Augmented Generation)** combines:
1. **Information Retrieval** - Finding relevant documents
2. **AI Generation** - Using LLMs to generate answers

Instead of the LLM answering from memory (which can hallucinate), RAG:
1. Retrieves relevant documents from a knowledge base
2. Provides those documents as context to the LLM
3. Generates accurate, grounded answers

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         User Request                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │  Flask API App │
                   │   (Python)     │
                   └────┬──────┬────┘
                        │      │
           ┌────────────┘      └──────────────┐
           │                                   │
           ▼                                   ▼
    ┌──────────────┐                   ┌─────────────┐
    │ PostgreSQL + │                   │  LiteMaaS   │
    │   pgvector   │                   │     API     │
    │              │                   │             │
    │ Vector Store │                   │ AI Models:  │
    │ (Embeddings) │                   │ - Nomic     │
    └──────────────┘                   │ - Granite   │
                                       └─────────────┘
```

### Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Vector Database** | PostgreSQL 16 + pgvector | Stores document embeddings for similarity search |
| **Application** | Flask (Python) | API endpoints for ingestion and Q&A |
| **Embedding Model** | Nomic Embed v1.5 (via LiteMaaS) | Converts text to 768-dimensional vectors |
| **Chat Model** | Granite 3.2 8B (via LiteMaaS) | Generates answers from context |
| **Platform** | OpenShift | Container orchestration and networking |

## How LiteMaaS is Used

**LiteMaaS** (LiteLLM as a Service) provides OpenAI-compatible API access to multiple AI models.

### 1. Embeddings (Nomic Embed v1.5)

**Purpose**: Convert text into numerical vectors for similarity search.

**Endpoint**: `/v1/embeddings`

**Request**:
```python
response = requests.post(
    f"{LITEMAAS_API_URL}/embeddings",
    headers={"Authorization": f"Bearer {LITEMAAS_API_KEY}"},
    json={
        "model": "nomic-embed-text-v1-5",
        "input": "Red Hat OpenShift is a Kubernetes platform"
    }
)
```

**Response**:
```json
{
  "data": [{
    "embedding": [0.123, -0.456, 0.789, ...],  // 768 dimensions
    "index": 0
  }]
}
```

**Use Cases**:
- Document ingestion: Embed each document's content
- Query processing: Embed user's question
- Similarity search: Find documents similar to question

### 2. Chat Completions (Granite 3.2 8B)

**Purpose**: Generate natural language answers from retrieved context.

**Endpoint**: `/v1/chat/completions`

**Request**:
```python
response = requests.post(
    f"{LITEMAAS_API_URL}/chat/completions",
    headers={"Authorization": f"Bearer {LITEMAAS_API_KEY}"},
    json={
        "model": "granite-3-2-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Context: ...\n\nQuestion: What is OpenShift?"}
        ]
    }
)
```

**Response**:
```json
{
  "choices": [{
    "message": {
      "content": "Red Hat OpenShift is a Kubernetes platform..."
    }
  }]
}
```

## Component Details

### PostgreSQL with pgvector

**pgvector** is a PostgreSQL extension that adds:
- `vector` data type for storing embeddings
- Similarity search operators (cosine, L2, inner product)
- IVFFLAT indexing for fast approximate nearest neighbor search

**Schema**:
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),  -- 768-dimensional vector from Nomic
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX documents_embedding_idx
ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Why 768 dimensions?**
Nomic Embed v1.5 produces 768-dimensional vectors. Each dimension captures different semantic features of the text.

### Flask Application

**Technology Stack**:
- Flask: Web framework
- psycopg2: PostgreSQL client
- requests: HTTP client for LiteMaaS

**Key Functions**:
```python
def get_embedding(text):
    """Get 768-dim vector from LiteMaaS Nomic Embed"""
    # Calls /v1/embeddings endpoint

def chat_completion(messages):
    """Get answer from LiteMaaS Granite model"""
    # Calls /v1/chat/completions endpoint

def init_db():
    """Initialize PostgreSQL with pgvector extension"""
    # Creates tables and indexes
```

## How It Works: Step by Step

### Document Ingestion Flow

```
1. User sends document
   POST /ingest {"title": "...", "content": "..."}

2. Flask app calls LiteMaaS
   POST /v1/embeddings
   {
     "model": "nomic-embed-text-v1-5",
     "input": "document content"
   }

3. LiteMaaS returns embedding
   {
     "data": [{
       "embedding": [768 numbers]
     }]
   }

4. Store in PostgreSQL
   INSERT INTO documents (title, content, embedding)
   VALUES ('...', '...', [768 numbers])
```

### Question Answering Flow

```
1. User asks question
   POST /ask {"question": "What is OpenShift?"}

2. Embed the question
   Call LiteMaaS: "What is OpenShift?" → [768 numbers]

3. Vector similarity search
   SELECT title, content,
          1 - (embedding <=> [768 numbers]) as similarity
   FROM documents
   ORDER BY embedding <=> [768 numbers]
   LIMIT 3

   Returns top 3 most similar documents

4. Build context from results
   context = """
   Document: OpenShift Overview
   Red Hat OpenShift is a Kubernetes platform...

   Document: OpenShift Features
   OpenShift provides automated operations...
   """

5. Generate answer with Granite
   Call LiteMaaS:
   {
     "model": "granite-3-2-8b-instruct",
     "messages": [
       {"role": "system", "content": "Answer based on context"},
       {"role": "user", "content": "Context: ...\n\nQuestion: ..."}
     ]
   }

6. Return answer to user
   {
     "question": "What is OpenShift?",
     "answer": "Red Hat OpenShift is...",
     "sources": [{"title": "...", "similarity": 0.89}]
   }
```

### Vector Similarity Search Explained

**Cosine Similarity**:
```
similarity = 1 - (embedding1 <=> embedding2)

Where:
  <=> is the cosine distance operator
  embedding1 = question vector
  embedding2 = document vector
```

**Example**:
```
Question: "What is Kubernetes?"
Documents in database:
  1. "Kubernetes orchestrates containers" → similarity: 0.92
  2. "Python is a programming language" → similarity: 0.23
  3. "OpenShift is built on Kubernetes" → similarity: 0.85

Top 3 retrieved: docs 1, 3, 2 (in that order)
```

## Why This Architecture?

### PostgreSQL + pgvector vs ChromaDB/Pinecone

**Advantages**:
- ✅ **Single database** - No separate vector store to manage
- ✅ **ACID transactions** - Data consistency guarantees
- ✅ **Production ready** - PostgreSQL is battle-tested
- ✅ **On-premise** - Runs entirely on OpenShift
- ✅ **Cost effective** - No external vector DB costs
- ✅ **SQL queries** - Combine vector search with filters

**Trade-offs**:
- ⚠️ **Performance** - Specialized vector DBs may be faster at extreme scale
- ⚠️ **Features** - Fewer advanced vector search features

**Best for**: Most enterprise applications (< 10M documents)

### LiteMaaS vs Direct Model Access

**Advantages**:
- ✅ **Unified API** - One endpoint for all models
- ✅ **OpenAI compatible** - Standard SDK works
- ✅ **Virtual keys** - Easy access management
- ✅ **Multiple models** - Switch models without code changes
- ✅ **No infrastructure** - Models managed for you

### Nomic Embed v1.5

**Why this model?**
- ✅ **High quality** - SOTA performance on benchmarks
- ✅ **768 dimensions** - Good balance of quality vs size
- ✅ **Open source** - Transparent and auditable
- ✅ **Multilingual** - Supports many languages

### Granite 3.2 8B

**Why this model?**
- ✅ **Enterprise focused** - Designed by IBM for business use
- ✅ **Instruction tuned** - Follows instructions well
- ✅ **8B parameters** - Good balance of quality vs speed
- ✅ **Context window** - Handles long contexts

## Performance Characteristics

### Latency Breakdown

Typical request latencies:

| Step | Time | Component |
|------|------|-----------|
| Embed question | 50-100ms | LiteMaaS (Nomic) |
| Vector search | 10-50ms | PostgreSQL |
| Generate answer | 500-2000ms | LiteMaaS (Granite) |
| **Total** | **~600-2200ms** | End-to-end |

### Scalability

**Current configuration**:
- PostgreSQL: 1 pod, 500m CPU, 1Gi RAM, 20Gi storage
- Flask app: 1 replica, 250m CPU, 512Mi RAM

**Scaling considerations**:
```yaml
# Horizontal scaling (more replicas)
ocp4_workload_maas_rag_example_app_replicas: 3

# Vertical scaling (more resources)
ocp4_workload_maas_rag_example_postgres_cpu_limit: 2000m
ocp4_workload_maas_rag_example_postgres_memory_limit: 4Gi

# Storage scaling
ocp4_workload_maas_rag_example_postgres_storage_size: 100Gi
```

**Limits**:
- Single PostgreSQL: ~1M documents recommended
- For more: Consider read replicas or sharding

## Code Walkthrough

### Document Ingestion

**File**: `roles/ocp4_workload_maas_rag_example/files/app.py`

```python
@app.route('/ingest', methods=['POST'])
def ingest():
    data = request.json
    title = data.get('title')
    content = data.get('content')

    # 1. Get embedding from LiteMaaS
    embedding = get_embedding(content)

    # 2. Store in PostgreSQL
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents (title, content, embedding) VALUES (%s, %s, %s) RETURNING id",
        (title, content, embedding)
    )
    doc_id = cur.fetchone()[0]
    conn.commit()

    return jsonify({"id": doc_id, "title": title}), 201
```

### Question Answering

```python
@app.route('/ask', methods=['POST'])
def ask():
    question = request.json.get('question')

    # 1. Embed question
    question_embedding = get_embedding(question)

    # 2. Vector similarity search
    cur.execute("""
        SELECT title, content,
               1 - (embedding <=> %s::vector) as similarity
        FROM documents
        ORDER BY embedding <=> %s::vector
        LIMIT 3
    """, (question_embedding, question_embedding))
    results = cur.fetchall()

    # 3. Build context
    context = "\n\n".join([
        f"Document: {r['title']}\n{r['content']}"
        for r in results
    ])

    # 4. Generate answer with Granite
    messages = [
        {"role": "system", "content": "Answer based on context"},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
    ]
    answer = chat_completion(messages)

    return jsonify({
        "question": question,
        "answer": answer,
        "sources": [{"title": r['title'], "similarity": r['similarity']} for r in results]
    })
```

## Deployment Architecture

### OpenShift Resources

```
Namespace: maas-rag-demo
├── StatefulSet/postgres
│   ├── Pod/postgres-0
│   │   └── Container: postgres (PostgreSQL 16 + pgvector)
│   └── PVC/postgres-data-postgres-0 (20Gi RBD)
├── Deployment/maas-rag-app
│   └── Pod/maas-rag-app-xxx
│       └── Container: app (Flask)
├── Service/postgres (ClusterIP: None - headless)
├── Service/maas-rag-app (ClusterIP)
├── Route/maas-rag-app (TLS edge termination)
├── BuildConfig/maas-rag-app (builds from GitHub)
└── ImageStream/maas-rag-app (internal registry)
```

### Network Flow

```
Internet → OpenShift Router → Route → Service → Pod

External:
  https://maas-rag-app-maas-rag-demo.apps.cluster.com

Internal:
  postgres-0.postgres.maas-rag-demo.svc:5432
  maas-rag-app.maas-rag-demo.svc:80
```

## Best Practices Implemented

### Security
- ✅ Secrets for database credentials
- ✅ Secrets for LiteMaaS API keys
- ✅ TLS termination at route
- ✅ No hardcoded passwords

### Reliability
- ✅ Liveness probes (PostgreSQL, Flask)
- ✅ Readiness probes (health checks)
- ✅ Resource limits (CPU, memory)
- ✅ Persistent storage (StatefulSet)

### Observability
- ✅ Structured logging
- ✅ Health check endpoints
- ✅ Error handling with messages

### Operations
- ✅ Idempotent deployment
- ✅ One-command cleanup
- ✅ Automatic image builds
- ✅ GitOps compatible

## Further Reading

- **pgvector documentation**: https://github.com/pgvector/pgvector
- **LiteLLM API reference**: https://docs.litellm.ai/
- **RAG patterns**: https://www.pinecone.io/learn/retrieval-augmented-generation/
- **Vector databases comparison**: https://benchmark.vectorview.ai/

## Summary

This application demonstrates:
1. **RAG pattern** - Combining retrieval with generation
2. **LiteMaaS integration** - Using embeddings and chat models
3. **Vector search** - PostgreSQL + pgvector for similarity
4. **Production deployment** - On OpenShift with proper resources

The architecture is simple, maintainable, and scalable for most enterprise use cases.
