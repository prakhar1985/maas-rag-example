# MaaS RAG Example - Quick Start Guide

## Simple 3-Step Deployment

### Step 1: Order Resources from RHDP

1. **OpenShift CNV Pool 4.20** - Order from RHDP catalog
2. **LiteMaaS Virtual Keys** - Select these models:
   - ✓ Nomic Embed v1.5 (for embeddings)
   - ✓ Granite 3.2 8B Instruct (for chat)
   - Duration: 7 days or more

Wait for both to deploy. You'll receive:
- OpenShift cluster URL and credentials
- LiteMaaS API URL and virtual key

### Step 2: Build & Push Container Image

```bash
# Clone the repo
git clone https://github.com/prakhar1985/maas-rag-example.git
cd maas-rag-example/roles/ocp4_workload_maas_rag_example/files

# Build image (replace YOUR_USERNAME with your Quay.io username)
podman build -t quay.io/YOUR_USERNAME/maas-rag-app:latest -f Containerfile .

# Login and push
podman login quay.io
podman push quay.io/YOUR_USERNAME/maas-rag-app:latest

# Update image reference
cd ../../..
sed -i '' 's|quay.io/psrivast/maas-rag-app:latest|quay.io/YOUR_USERNAME/maas-rag-app:latest|' \
  roles/ocp4_workload_maas_rag_example/defaults/main.yml
```

### Step 3: Deploy to OpenShift

```bash
# Install collection
ansible-galaxy collection install .

# Create vars file with your credentials
cat > vars.yml <<EOF
---
litellm_api_base_url: YOUR_LITEMAAS_URL    # From LiteMaaS order
litellm_virtual_key: YOUR_VIRTUAL_KEY       # From LiteMaaS order
openshift_api_url: YOUR_OPENSHIFT_URL       # From CNV Pool order
openshift_api_key: YOUR_OPENSHIFT_TOKEN     # From CNV Pool order
EOF

# Create deployment playbook
cat > deploy.yml <<EOF
---
- name: Deploy MaaS RAG Example
  hosts: localhost
  gather_facts: false
  vars_files:
    - vars.yml
  tasks:
    - name: Run workload
      ansible.builtin.include_role:
        name: maas_rag_example.maas_rag_example.ocp4_workload_maas_rag_example
      vars:
        ACTION: provision
EOF

# Deploy!
ansible-playbook deploy.yml
```

The deployment will:
- Create `maas-rag-demo` namespace
- Deploy PostgreSQL 16 with pgvector
- Deploy Flask RAG application
- Create OpenShift Route
- Display the application URL

## Test It Out

Get the app URL from the deployment output, then:

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
```

## Cleanup

```bash
cat > cleanup.yml <<EOF
---
- name: Remove MaaS RAG Example
  hosts: localhost
  gather_facts: false
  vars_files:
    - vars.yml
  tasks:
    - name: Run workload removal
      ansible.builtin.include_role:
        name: maas_rag_example.maas_rag_example.ocp4_workload_maas_rag_example
      vars:
        ACTION: destroy
EOF

ansible-playbook cleanup.yml
```

## What You Get

- **RAG Application**: Document ingestion + question answering
- **Vector Database**: PostgreSQL with pgvector extension
- **AI Models**: Nomic for embeddings, Granite for chat (via LiteMaaS)
- **Web Interface**: Accessible via OpenShift Route

## Next Steps

- See [README.md](README.md) for detailed documentation
- Check API endpoints at `$APP_URL/`
- Customize variables in `roles/ocp4_workload_maas_rag_example/defaults/main.yml`
