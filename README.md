# AI-RepoExplainer

AI-powered codebase understanding and repository exploration tool.

AI-RepoExplainer allows developers to ingest a GitHub repository and ask questions about its codebase using semantic search, code retrieval, and LLM-powered answers.

## Features

- GitHub repository ingestion
- Source-code scanning and parsing
- Intelligent code chunking
- Code embeddings using Sentence Transformers
- FAISS-based semantic search
- Query expansion and result ranking
- Repository symbol and dependency analysis
- RAG-based codebase question answering
- Groq-powered LLM responses
- Retrieved source references
- Repository Explorer
- Repository analytics
- Response performance metrics
- Clean developer-focused frontend

## How It Works

```text
GitHub Repository
        ↓
Repository Ingestion
        ↓
File Scanning & Parsing
        ↓
Code Chunking
        ↓
Embeddings
        ↓
FAISS Vector Index
        ↓
Semantic Retrieval
        ↓
Relevant Code Context
        ↓
Groq LLM
        ↓
AI-Generated Answer
Tech Stack
Backend
Python
FastAPI
Sentence Transformers
FAISS
Groq API
Frontend
React
Vite
Tailwind CSS
Axios
React Markdown
Screenshots
AI Codebase Chat
<img width="1280" height="800" alt="AI-RepoExplainer Chat" src="https://github.com/user-attachments/assets/3fbc1ecb-4a8a-4973-83c5-3095fca6bb31" />
Repository Explorer
<img width="1280" height="800" alt="AI-RepoExplainer Repository Explorer" src="https://github.com/user-attachments/assets/924fe0a5-3b5d-467e-bfcf-f63fa8a1668a" />
Installation
Backend
git clone <your-repository-url>
cd AI-RepoExplainer

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

Create a .env file:

GROQ_API_KEY=your_groq_api_key

Start the backend:

uvicorn app.main:app --reload

Backend:

http://127.0.0.1:8000
Frontend

Open another terminal:

cd frontend
npm install
npm run dev

Frontend:

http://localhost:5173
Usage
Start the backend and frontend.
Open the web application.
Enter a GitHub repository URL.
Ingest the repository.
Explore the repository structure.
Ask questions about the codebase.
Inspect the retrieved source files and AI-generated explanations.
Project Structure
AI-RepoExplainer/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── embeddings/
│   ├── ingestion/
│   ├── llm/
│   ├── models/
│   ├── processing/
│   ├── retrieval/
│   └── services/
│
├── frontend/
│   └── src/
│
├── data/
├── requirements.txt
├── .env
└── README.md
Goal

AI-RepoExplainer aims to make unfamiliar codebases easier to understand by combining traditional code analysis with semantic search and generative AI.

Instead of manually searching through hundreds of files, developers can interact with their repository using natural language.

Author

Arpit Mishra

B.Tech CSE (AI/ML)
