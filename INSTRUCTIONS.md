# ONE COMMAND DEPLOYMENT

## What You Need

1. OpenShift CNV Pool 4.20 from RHDP
2. LiteMaaS Virtual Keys (Nomic Embed + Granite 3.2 8B)

## Deploy Everything

```bash
# 1. Pull latest changes
cd /home/lab-user/maas-rag-example
git pull origin main

# 2. Login to OpenShift
oc login https://api.YOUR_CLUSTER.com:6443 --token=YOUR_TOKEN

# 3. Deploy (replace with your actual values)
ansible-playbook deploy.yml \
  -e litellm_api_base_url=https://litellm-rhpds.apps.YOUR_CLUSTER.com/v1 \
  -e litellm_virtual_key=sk-YOUR-VIRTUAL-KEY-HERE
```

Done! 🎉

## Test It

The playbook will show you the app URL. Use these commands:

```bash
export APP_URL="https://YOUR_APP_URL_FROM_OUTPUT"

# Add a document
curl -X POST $APP_URL/ingest \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content": "OpenShift is a Kubernetes platform."}'

# Ask a question
curl -X POST $APP_URL/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is OpenShift?"}'
```

## Remove Everything

```bash
ansible-playbook cleanup.yml
```

That's it!
