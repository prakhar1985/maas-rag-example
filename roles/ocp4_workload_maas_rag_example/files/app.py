#!/usr/bin/env python3
"""
MaaS RAG Example Application

Simple Flask app demonstrating:
- Document ingestion with embeddings (Nomic via LiteMaaS)
- Semantic search using PostgreSQL + pgvector
- Answer generation with chat model (Granite via LiteMaaS)
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Track if database has been initialized
_db_initialized = False

# Configuration from environment variables
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DATABASE', 'ragdb')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'raguser')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')

LITEMAAS_API_URL = os.getenv('LITEMAAS_API_URL')
LITEMAAS_API_KEY = os.getenv('LITEMAAS_API_KEY')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text-v1-5')
CHAT_MODEL = os.getenv('CHAT_MODEL', 'granite-3-2-8b-instruct')


def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )


def init_db():
    """Initialize database schema with pgvector"""
    global _db_initialized

    if _db_initialized:
        return

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Install pgvector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Create documents table with vector column
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding vector(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cur.close()
        conn.close()

        _db_initialized = True
        print("Database initialized successfully", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"Database initialization error: {e}", file=sys.stderr, flush=True)
        raise


def get_embedding(text):
    """Get embedding from LiteMaaS"""
    response = requests.post(
        f"{LITEMAAS_API_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {LITEMAAS_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": EMBEDDING_MODEL,
            "input": text
        }
    )
    response.raise_for_status()
    return response.json()['data'][0]['embedding']


def chat_completion(messages):
    """Get chat completion from LiteMaaS"""
    response = requests.post(
        f"{LITEMAAS_API_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {LITEMAAS_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": CHAT_MODEL,
            "messages": messages
        }
    )
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']


@app.before_request
def ensure_db_initialized():
    """Ensure database is initialized before handling any request"""
    init_db()


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


@app.route('/')
def index():
    """Landing page"""
    return jsonify({
        "message": "MaaS RAG Example API",
        "endpoints": {
            "/health": "Health check",
            "/ingest": "POST - Ingest a document",
            "/ask": "POST - Ask a question",
            "/documents": "GET - List all documents"
        }
    }), 200


@app.route('/ingest', methods=['POST'])
def ingest():
    """Ingest a document and store its embedding"""
    data = request.json
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({"error": "Title and content required"}), 400

    try:
        # Get embedding from LiteMaaS
        embedding = get_embedding(content)

        # Store in database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO documents (title, content, embedding) VALUES (%s, %s, %s) RETURNING id",
            (title, content, embedding)
        )
        doc_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "id": doc_id,
            "title": title,
            "message": "Document ingested successfully"
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/ask', methods=['POST'])
def ask():
    """Answer a question using RAG"""
    data = request.json
    question = data.get('question')

    if not question:
        return jsonify({"error": "Question required"}), 400

    try:
        # Get question embedding
        question_embedding = get_embedding(question)
        print(f"Question: {question}, Embedding length: {len(question_embedding)}", file=sys.stderr, flush=True)

        # Search for similar documents
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT title, content,
                   1 - (embedding <=> %s::vector) as similarity
            FROM documents
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 3
        """, (question_embedding, question_embedding))

        results = cur.fetchall()
        print(f"Found {len(results)} results", file=sys.stderr, flush=True)
        cur.close()
        conn.close()

        if not results:
            return jsonify({
                "answer": "No documents found in the database. Please ingest some documents first.",
                "sources": []
            }), 200

        # Build context from top results
        context = "\n\n".join([
            f"Document: {r['title']}\n{r['content']}"
            for r in results
        ])

        # Generate answer using chat model
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer questions based on the provided context. If the context doesn't contain enough information, say so."
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            }
        ]

        answer = chat_completion(messages)

        return jsonify({
            "question": question,
            "answer": answer,
            "sources": [
                {"title": r['title'], "similarity": float(r['similarity'])}
                for r in results
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/documents', methods=['GET'])
def list_documents():
    """List all documents"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, title, created_at FROM documents ORDER BY created_at DESC")
        documents = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({"documents": documents}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    app.run(host='0.0.0.0', port=5000)
