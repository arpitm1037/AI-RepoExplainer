# AI Repo Explainer

AI-powered codebase understanding system built using FastAPI, RAG, FAISS, and LLMs.

This project helps developers understand software repositories by enabling semantic code search and AI-based explanations of code structure and functionality.

---

## Features

* Repository-aware semantic search
* RAG (Retrieval-Augmented Generation) pipeline
* FAISS vector database for fast retrieval
* Code chunking and embeddings
* AI-generated explanations for code queries
* Query improvement before retrieval
* Context-aware response generation
* FastAPI backend
* Simple frontend interface

---

## Tech Stack

### Backend

* FastAPI
* Python

### AI / Retrieval

* SentenceTransformers
* FAISS
* Gemini / OpenRouter APIs

### Frontend

* HTML
* CSS
* JavaScript

---

## How It Works

1. Repository code is scanned and extracted
2. Code is split into smaller chunks
3. Embeddings are generated for each chunk
4. FAISS indexes embeddings for fast similarity search
5. User query is improved and embedded
6. Relevant code chunks are retrieved
7. Retrieved context is passed to the LLM
8. AI generates contextual explanation/answer

---

## Example Workflow

```text
User Query
   ↓
Query Improvement
   ↓
Embedding Generation
   ↓
FAISS Retrieval
   ↓
Relevant Code Chunks
   ↓
LLM Response Generation
```

---

## Current Limitations

* Works best on small-to-medium repositories
* Retrieval quality depends on chunking strategy
* No multi-repository indexing yet
* Limited architecture-level reasoning

---

## Future Improvements

* AST-based code chunking
* Multi-file dependency understanding
* Repository graph visualization
* Better reranking and retrieval evaluation
* LangGraph agent workflows
* Docker deployment

---

## Learning Goals Behind This Project

This project was built to deeply understand:

* RAG systems
* embeddings and vector search
* semantic retrieval
* code-aware AI systems
* scalable GenAI backend architecture

---

## Run Locally

```bash
git clone https://github.com/arpitm1037/AI-RepoExplainer.git

cd AI-RepoExplainer

pip install -r requirements.txt

uvicorn main:app --reload
```

---

## Author

Arpit Mishra
