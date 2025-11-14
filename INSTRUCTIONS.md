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
# Document 1: Coffee Facts
curl -X POST $APP_URL/ingest -H "Content-Type: application/json" -d '{"title":"Coffee Facts","content":"Coffee is a magical bean juice that turns I cannot into I can."}'

# Document 2: Debugging
curl -X POST $APP_URL/ingest -H "Content-Type: application/json" -d '{"title":"Debugging","content":"Debugging is like being a detective in a crime movie where you are also the murderer."}'

# Document 3: Kubernetes
curl -X POST $APP_URL/ingest -H "Content-Type: application/json" -d '{"title":"Kubernetes","content":"Kubernetes kills your pods when they misbehave. It is basically pod jail."}'

# Document 4: Superhero Movies
curl -X POST $APP_URL/ingest -H "Content-Type: application/json" -d '{"title":"Superhero Movies","content":"Every superhero movie is just people in fancy pajamas solving problems they created."}'

# Document 5: Programming Joke
curl -X POST $APP_URL/ingest -H "Content-Type: application/json" -d '{"title":"Programming Joke","content":"Why do programmers prefer dark mode? Because light attracts bugs."}'
```

**Expected**: Each returns:
```json
{
  "id": 1,
  "message": "Document ingested successfully",
  "title": "Coffee Facts"
}
```

## Test 4: List Documents

```bash
curl $APP_URL/documents
```

**Expected**: List of all ingested documents.

## Test 5: Ask Questions (RAG)

Now ask questions using the RAG application:

### Question 1: About Coffee

```bash
curl -X POST $APP_URL/ask -H "Content-Type: application/json" -d '{"question":"What is coffee?"}'
```

**Expected**:
```json
{
  "question": "What is coffee?",
  "answer": "Coffee is a magical bean juice that turns 'I cannot' into 'I can.'",
  "sources": [
    {
      "title": "Coffee Facts",
      "similarity": 0.87
    }
  ]
}
```

### Question 2: About Debugging

```bash
curl -X POST $APP_URL/ask -H "Content-Type: application/json" -d '{"question":"Tell me about debugging"}'
```

### Question 3: About Kubernetes

```bash
curl -X POST $APP_URL/ask -H "Content-Type: application/json" -d '{"question":"What happens to misbehaving pods?"}'
```

### Question 4: About Superheroes

```bash
curl -X POST $APP_URL/ask -H "Content-Type: application/json" -d '{"question":"Tell me about superhero movies"}'
```

### Question 5: About Dark Mode

```bash
curl -X POST $APP_URL/ask -H "Content-Type: application/json" -d '{"question":"Why do programmers like dark mode?"}'
```

## How Do You Know It's Actually Working?

Here's the magic of RAG - watch this happen:

**1. You ask a question you NEVER explicitly answered**

Try this question that's not in any document:
```bash
curl -X POST $APP_URL/ask -H "Content-Type: application/json" -d '{"question":"Why do developers need coffee?"}'
```

**What happens:**
- The app searches your documents using vector similarity
- Finds "Coffee Facts" document (even though the question is different)
- Granite model reads that document and generates a NEW answer
- You get an answer that combines the document content with the question

**2. The similarity score shows you what it found**

Look at the `sources` in the response:
```json
{
  "answer": "Based on the context, coffee helps developers by turning 'I cannot' into 'I can'...",
  "sources": [
    {
      "title": "Coffee Facts",
      "similarity": 0.82
    }
  ]
}
```

The `0.82` similarity means it found a pretty good match!

**3. Try a question that has NO match**

```bash
curl -X POST $APP_URL/ask -H "Content-Type: application/json" -d '{"question":"What is the capital of France?"}'
```

You'll see:
- Low similarity scores (like 0.15 or 0.25)
- The model will say "The context doesn't contain information about this"

**This proves:**
- ✅ Embedding model (Nomic) is converting text to vectors
- ✅ Vector search (pgvector) is finding similar documents
- ✅ Chat model (Granite) is reading context and generating answers
- ✅ The whole RAG pipeline is working!

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
