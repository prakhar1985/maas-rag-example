# MaaS RAG Example

Production-ready RAG (Retrieval-Augmented Generation) application demonstrating LiteMaaS integration with PostgreSQL + pgvector on OpenShift.

## Quick Deployment

### Prerequisites

1. **OpenShift Open Environment** from RHDP catalog
2. **LiteMaaS Virtual Keys** with:
   - `nomic-embed-text-v1-5` (embeddings)
   - `granite-3-2-8b-instruct` (chat)

### Deploy

```bash
# SSH to bastion
ssh lab-user@bastion.GUID.dynamic.redhatworkshops.io

# Clone repository
git clone https://github.com/prakhar1985/maas-rag-example.git
cd maas-rag-example

# Install Ansible collections
ansible-galaxy collection install -r requirements.yml

# Deploy application (already logged into OpenShift)
ansible-playbook deploy.yml \
  -e litellm_api_base_url=https://litellm-rhpds.apps.YOUR_CLUSTER.com/v1 \
  -e litellm_virtual_key=sk-YOUR-VIRTUAL-KEY-HERE
```

### Test

```bash
export APP_URL="https://YOUR_APP_URL"

# Ingest document
curl -X POST $APP_URL/ingest \
  -H "Content-Type: application/json" \
  -d '{"title": "OpenShift", "content": "Red Hat OpenShift is a Kubernetes platform."}'

# Ask question
curl -X POST $APP_URL/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is OpenShift?"}'
```

### Cleanup

```bash
ansible-playbook cleanup.yml
```

## Documentation

- **[TUTORIAL.md](TUTORIAL.md)** - Learn how RAG works with LiteMaaS
- **[INSTRUCTIONS.md](INSTRUCTIONS.md)** - Testing the application

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ingest` | POST | Add document with embedding |
| `/ask` | POST | Ask question (RAG) |
| `/documents` | GET | List all documents |

## Configuration

See `roles/ocp4_workload_maas_rag_example/defaults/main.yml` for all variables.

**Key variables:**

```bash
# Pass as extra vars to ansible-playbook
-e ocp4_workload_maas_rag_example_namespace=my-namespace
-e ocp4_workload_maas_rag_example_postgres_storage_size=50Gi
```

## Repository Structure

```
maas-rag-example/
├── deploy.yml           # One-step deployment
├── cleanup.yml          # One-step cleanup
├── requirements.yml     # Collection dependencies
└── roles/
    └── ocp4_workload_maas_rag_example/
        ├── defaults/    # Variables
        ├── tasks/       # Deployment logic
        ├── templates/   # Kubernetes manifests
        └── files/       # Flask app + Containerfile
```

## Support

For issues or questions, open an issue at:
https://github.com/prakhar1985/maas-rag-example/issues

## About

**Author**: Prakhar Srivastava
**Role**: Manager, Technical Marketing at Red Hat
**Email**: psrivast@redhat.com

This project demonstrates how to build production RAG applications using Red Hat's LiteMaaS (LiteLLM as a Service) on OpenShift, combining vector search with AI models for intelligent question answering.

## License

Apache-2.0
