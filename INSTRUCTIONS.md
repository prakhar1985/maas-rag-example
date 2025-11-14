# Testing the RAG Application

After deploying the application, follow these steps to test it.

## Get the Application URL

```bash
oc get route -n maas-rag-demo maas-rag-app -o jsonpath='{.spec.host}'
```

Set it as an environment variable:

```bash
export APP_URL="https://$(oc get route -n maas-rag-demo maas-rag-app -o jsonpath='{.spec.host}')"
echo "App URL: $APP_URL"
```

## Test 1: Health Check

```bash
curl $APP_URL/health
```

**Expected**:
```json
{"status": "healthy"}
```

## Test 2: List Endpoints

```bash
curl $APP_URL/
```

**Expected**: API documentation with available endpoints.

## Test 3: Ingest Documents

Add some documents to the knowledge base:

```bash
# Document 1: OpenShift
curl -X POST $APP_URL/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "What is OpenShift",
    "content": "Red Hat OpenShift is a Kubernetes platform for containerized applications. It provides automated operations, built-in monitoring, and enterprise security."
  }'

# Document 2: Containers
curl -X POST $APP_URL/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Container Technology",
    "content": "Containers package applications with their dependencies, making them portable across environments. Docker and Podman are popular container runtimes."
  }'

# Document 3: Kubernetes
curl -X POST $APP_URL/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Kubernetes Basics",
    "content": "Kubernetes orchestrates containerized applications across clusters. It handles scheduling, scaling, and self-healing of applications."
  }'
```

**Expected**: Each returns:
```json
{
  "id": 1,
  "message": "Document ingested successfully",
  "title": "What is OpenShift"
}
```

## Test 4: List Documents

```bash
curl $APP_URL/documents
```

**Expected**: List of all ingested documents.

## Test 5: Ask Questions (RAG)

Now ask questions using the RAG application:

### Question 1: About OpenShift

```bash
curl -X POST $APP_URL/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is OpenShift?"
  }'
```

**Expected**:
```json
{
  "question": "What is OpenShift?",
  "answer": "Red Hat OpenShift is a Kubernetes platform for containerized applications...",
  "sources": [
    {
      "title": "What is OpenShift",
      "similarity": 0.89
    }
  ]
}
```

### Question 2: About Containers

```bash
curl -X POST $APP_URL/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do containers work?"
  }'
```

### Question 3: About Kubernetes

```bash
curl -X POST $APP_URL/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What does Kubernetes do?"
  }'
```

## Understanding the Response

Each RAG response includes:

1. **question**: Your original question
2. **answer**: Generated answer from Granite model
3. **sources**: Documents used to generate the answer with similarity scores

**Similarity scores**:
- `1.0` = Perfect match
- `0.8-0.9` = Very relevant
- `0.5-0.7` = Somewhat relevant
- `< 0.5` = Not very relevant

## How It Works

When you ask a question:

1. **Embedding**: Your question is converted to a 768-dimensional vector using Nomic Embed
2. **Search**: PostgreSQL finds the 3 most similar documents using vector similarity
3. **Context**: Retrieved documents are provided to Granite model
4. **Generation**: Granite generates an answer based on the context
5. **Response**: Answer + sources returned to you

## Troubleshooting

### Error: "No documents found"

**Cause**: Database is empty.

**Solution**: Ingest some documents first (Test 3).

### Error: Connection refused

**Cause**: App not running or route not created.

**Solution**:
```bash
oc get pods -n maas-rag-demo
oc get route -n maas-rag-demo
```

### Slow responses

**Cause**: Granite model takes 1-2 seconds to generate answers.

**Solution**: This is normal. Embedding is fast (~100ms), generation is slow (~1-2s).

### Low similarity scores

**Cause**: Question doesn't match any documents well.

**Solution**: Ingest more relevant documents or rephrase your question.

## Next Steps

- Ingest your own documents
- Try different questions
- Check the tutorial: [TUTORIAL.md](TUTORIAL.md)
- Explore the code: `roles/ocp4_workload_maas_rag_example/files/app.py`

## Clean Up

When done testing:

```bash
# Delete all documents
# (No endpoint for this - just redeploy or delete namespace)

# Or remove entire application
ansible-playbook cleanup.yml
```
