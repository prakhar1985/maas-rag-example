# MaaS RAG Example

RAG (Retrieval-Augmented Generation) application demonstrating LiteMaaS integration with PostgreSQL + pgvector.

## What This Does

- **Document Ingestion**: Upload documents and generate embeddings using Nomic Embed via LiteMaaS
- **Vector Storage**: Store embeddings in PostgreSQL with pgvector extension
- **Semantic Search**: Find relevant documents using vector similarity
- **Answer Generation**: Generate answers using Granite chat model via LiteMaaS

## Architecture

```
┌─────────────────┐
│  Flask App      │
│  (Python)       │
└────┬────────┬───┘
     │        │
     │        └──────────> LiteMaaS API
     │                     - Nomic Embed (embeddings)
     │                     - Granite 3.2 8B (chat)
     │
     └────────────────────> PostgreSQL 16
                            - pgvector extension
                            - Vector similarity search
```

## Quick Start (ONE Command)

### Prerequisites

1. **Order OpenShift CNV Pool 4.20** from RHDP catalog
2. **Order LiteMaaS Virtual Keys** with:
   - `nomic-embed-text-v1-5` (for embeddings)
   - `granite-3-2-8b-instruct` (for chat)
   - Duration: 7 days or more

### Deploy Everything in One Step

```bash
# Clone the repository
git clone https://github.com/prakhar1985/maas-rag-example.git
cd maas-rag-example

# Install required Ansible collections
ansible-galaxy collection install -r requirements.yml

# Login to OpenShift cluster
oc login https://api.YOUR_CLUSTER.com:6443 --token=YOUR_TOKEN

# Deploy everything (replace with your actual credentials)
ansible-playbook deploy.yml \
  -e litellm_api_base_url=https://litellm-rhpds.apps.YOUR_CLUSTER.com/v1 \
  -e litellm_virtual_key=sk-YOUR-VIRTUAL-KEY-HERE
```

**That's it!** The playbook will:
1. ✅ Validate OpenShift connection
2. ✅ Validate LiteMaaS credentials
3. ✅ Install this collection automatically
4. ✅ Build container image on OpenShift (no Quay.io needed)
5. ✅ Deploy PostgreSQL 16 with pgvector extension
6. ✅ Deploy Flask RAG application
7. ✅ Create OpenShift Route
8. ✅ Display application URL
9. ✅ Optionally run a quick test

### Test the Application

The deployment playbook displays the application URL. Use it to test:

```bash
oc get route -n maas-rag-demo maas-rag-app -o jsonpath='{.spec.host}'
```

#### Ingest a Document

```bash
curl -X POST https://YOUR_APP_URL/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "OpenShift Basics",
    "content": "Red Hat OpenShift is a Kubernetes platform for containerized applications. It provides automated operations and enterprise security."
  }'
```

#### Ask a Question

```bash
curl -X POST https://YOUR_APP_URL/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is OpenShift?"
  }'
```

Response:

```json
{
  "question": "What is OpenShift?",
  "answer": "Red Hat OpenShift is a Kubernetes platform designed for containerized applications, offering automated operations and enterprise-grade security features.",
  "sources": [
    {
      "title": "OpenShift Basics",
      "similarity": 0.89
    }
  ]
}
```

#### List Documents

```bash
curl https://YOUR_APP_URL/documents
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/` | GET | API information |
| `/ingest` | POST | Ingest a document |
| `/ask` | POST | Ask a question |
| `/documents` | GET | List all documents |

## Configuration Variables

See `roles/ocp4_workload_maas_rag_example/defaults/main.yml` for all available variables.

### Key Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ocp4_workload_maas_rag_example_namespace` | `maas-rag-demo` | Namespace for deployment |
| `ocp4_workload_maas_rag_example_postgres_storage_size` | `20Gi` | PostgreSQL storage size |
| `ocp4_workload_maas_rag_example_embedding_model` | `nomic-embed-text-v1-5` | Embedding model |
| `ocp4_workload_maas_rag_example_chat_model` | `granite-3-2-8b-instruct` | Chat model |

## Cleanup

Remove everything with one command:

```bash
ansible-playbook cleanup.yml
```

## Development

### Directory Structure

```
maas-rag-example/
├── galaxy.yml                           # Collection metadata
├── requirements.yml                     # Ansible collection dependencies
├── deploy.yml                           # One-step deployment playbook
├── cleanup.yml                          # One-step cleanup playbook
├── README.md                            # Full documentation (this file)
├── QUICKSTART.md                        # Quick start guide
├── INSTRUCTIONS.md                      # Simple one-page instructions
└── roles/
    └── ocp4_workload_maas_rag_example/
        ├── defaults/main.yml            # Default variables
        ├── tasks/
        │   ├── main.yml                 # Entry point
        │   ├── pre_workload.yml         # Pre-deployment validation
        │   ├── workload.yml             # Main deployment (with BuildConfig)
        │   ├── post_workload.yml        # Post-deployment user info
        │   └── remove_workload.yml      # Cleanup tasks
        ├── templates/
        │   ├── postgresql-statefulset.yml.j2  # PostgreSQL with pgvector
        │   ├── postgresql-service.yml.j2
        │   ├── app-imagestream.yml.j2         # Image registry
        │   ├── app-buildconfig.yml.j2         # Build from GitHub
        │   ├── app-deployment.yml.j2          # Flask app deployment
        │   ├── app-service.yml.j2
        │   └── app-route.yml.j2               # External access
        └── files/
            ├── app.py                   # Flask RAG application
            ├── requirements.txt         # Python dependencies
            └── Containerfile            # Container build definition
```

### Container Image Building

The container image is **automatically built on OpenShift** during deployment:

- BuildConfig pulls source from GitHub
- Builds using the Containerfile in `files/`
- Stores in OpenShift internal registry
- **No external registry (Quay.io) required**

To disable auto-build and use a pre-built image:

```yaml
# In defaults/main.yml
ocp4_workload_maas_rag_example_build_image: false
ocp4_workload_maas_rag_example_app_image: quay.io/YOUR_USERNAME/maas-rag-app:latest
```

## How It Works

### 1. Document Ingestion

When you POST to `/ingest`:

1. Flask app receives document (title + content)
2. Calls LiteMaaS `/embeddings` endpoint with Nomic model
3. Stores document + embedding vector in PostgreSQL
4. Returns document ID

### 2. Question Answering

When you POST to `/ask`:

1. Flask app receives question
2. Generates embedding for question using Nomic
3. Performs vector similarity search in PostgreSQL (cosine similarity)
4. Retrieves top 3 most similar documents
5. Builds context from retrieved documents
6. Calls LiteMaaS `/chat/completions` with Granite model
7. Returns generated answer + source documents

### 3. Vector Search

PostgreSQL with pgvector extension provides:

- **Vector data type**: Store 768-dimensional embeddings
- **Similarity functions**: Cosine distance for semantic search
- **IVFFLAT index**: Fast approximate nearest neighbor search

## Troubleshooting

### PostgreSQL pod not starting

Check if pgvector extension installed:

```bash
oc logs -n maas-rag-demo postgres-0 -c install-pgvector
```

### App can't connect to PostgreSQL

Check connectivity:

```bash
oc exec -n maas-rag-demo deployment/maas-rag-app -- \
  curl postgres:5432
```

### LiteMaaS API errors

Verify credentials:

```bash
oc get secret -n maas-rag-demo litemaas-credentials -o yaml
```

Test API directly:

```bash
curl https://YOUR_LITEMAAS_URL/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

## Support

For issues or questions:

- **Repository**: https://github.com/prakhar1985/maas-rag-example
- **Maintainer**: Prakhar Srivastava <psrivast@redhat.com>

## License

Apache-2.0
