# MaaS RAG Example - Quick Start Guide

## ONE-STEP Deployment

### Prerequisites

1. **OpenShift CNV Pool 4.20** - Order from RHDP catalog
2. **LiteMaaS Virtual Keys** - Select these models:
   - ✓ Nomic Embed v1.5 (for embeddings)
   - ✓ Granite 3.2 8B Instruct (for chat)
   - Duration: 7 days or more

Wait for both to deploy. You'll receive:
- OpenShift cluster URL and credentials
- LiteMaaS API URL and virtual key

### Deploy Everything in One Command

```bash
# Clone the repo
git clone https://github.com/prakhar1985/maas-rag-example.git
cd maas-rag-example

# Login to OpenShift
oc login https://YOUR_CLUSTER_URL:6443 --token=YOUR_TOKEN

# Deploy everything in one step
ansible-playbook deploy.yml \
  -e litellm_api_base_url=https://litellm-rhpds.apps.YOUR_CLUSTER.com/v1 \
  -e litellm_virtual_key=sk-YOUR-VIRTUAL-KEY-HERE
```

That's it! The playbook will:
1. ✅ Validate OpenShift connection
2. ✅ Validate LiteMaaS credentials
3. ✅ Install the collection
4. ✅ Build the container image on OpenShift
5. ✅ Deploy PostgreSQL with pgvector
6. ✅ Deploy the Flask RAG application
7. ✅ Create the Route
8. ✅ Display the application URL
9. ✅ Optionally run a test

## Test the Application

The deployment will display the app URL. Test it:

```bash
export APP_URL="https://YOUR_APP_URL"

# Ingest a document
curl -X POST $APP_URL/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "OpenShift Virtualization",
    "content": "OpenShift Virtualization allows you to run VMs alongside containers on OpenShift using KubeVirt."
  }'

# Ask a question
curl -X POST $APP_URL/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is OpenShift Virtualization?"}'

# List documents
curl $APP_URL/documents
```

## Cleanup

Remove everything in one command:

```bash
ansible-playbook cleanup.yml
```

## What You Get

- **Vector Database**: PostgreSQL 16 with pgvector extension
- **RAG Application**: Flask app with document ingestion + Q&A
- **AI Models**:
  - Nomic Embed v1.5 for embeddings
  - Granite 3.2 8B Instruct for chat
  - Accessed via LiteMaaS
- **Web API**: RESTful endpoints accessible via OpenShift Route

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/` | GET | API information |
| `/ingest` | POST | Ingest a document with embedding |
| `/ask` | POST | Ask a question (RAG) |
| `/documents` | GET | List all documents |

## Troubleshooting

### Check deployment status
```bash
oc get pods -n maas-rag-demo
oc get route -n maas-rag-demo
```

### View logs
```bash
# Application logs
oc logs -n maas-rag-demo deployment/maas-rag-app

# PostgreSQL logs
oc logs -n maas-rag-demo statefulset/postgres

# Build logs (if build failed)
oc logs -n maas-rag-demo build/maas-rag-app-1
```

### Test LiteMaaS connection
```bash
curl https://YOUR_LITEMAAS_URL/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

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

## Next Steps

- See [README.md](README.md) for detailed documentation
- Customize variables in `roles/ocp4_workload_maas_rag_example/defaults/main.yml`
- Add more documents and test different questions
- Explore the Flask app source code in `roles/ocp4_workload_maas_rag_example/files/app.py`

## Support

For issues or questions:
- **Repository**: https://github.com/prakhar1985/maas-rag-example
- **Maintainer**: Prakhar Srivastava <psrivast@redhat.com>
