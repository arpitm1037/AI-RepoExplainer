from app.ingestion.repo_cloner import RepoCloner
from app.ingestion.file_scanner import FileScanner
from app.ingestion.file_loader import FileLoader
from app.processing.chunker import CodeChunker
from app.embeddings.embedding_model import EmbeddingModel
from app.embeddings.vector_store import VectorStore


def main():
    repo_url = "https://github.com/tiangolo/fastapi.git"

    cloner = RepoCloner()
    scanner = FileScanner()
    loader = FileLoader()
    chunker = CodeChunker()
    embedding_model = EmbeddingModel()

    repo_path = cloner.clone_repository(repo_url)

    files = scanner.scan_repository(repo_path)

    documents = loader.load_files(files)

    chunks = chunker.chunk_documents(documents)

    print(f"\nTotal Chunks Created: {len(chunks)}")

    sample_chunks = chunks[:100]

    embeddings = embedding_model.embed_chunks(sample_chunks)

    print(f"\nGenerated Embeddings: {len(embeddings)}")

    vector_store = VectorStore(
        embedding_dimension=len(embeddings[0])
    )

    vector_store.add_embeddings(
        sample_chunks,
        embeddings,
    )

    print("\nFAISS index created successfully")

    query = "How does routing work in FastAPI?"

    print(f"\nQuery: {query}")

    query_embedding = embedding_model.embed_text(query)

    results = vector_store.search(
        query_embedding=query_embedding,
        top_k=3,
    )

    print(f"\nTop Results Found: {len(results)}")

    for index, chunk in enumerate(results, start=1):
        print(f"\nRESULT {index}")
        print(f"File: {chunk.file_path}")
        print(f"Lines: {chunk.start_line}-{chunk.end_line}")

        print("\nPreview:\n")

        print(chunk.content[:500])


if __name__ == "__main__":
    main()