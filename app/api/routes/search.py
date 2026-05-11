from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from app.core.constants import (
    RETRIEVAL_SNIPPET_MAX_CHARS,
)

from app.models.schemas import (
    AskRequest,
    IngestRequest,
    SearchRequest,
)

from app.services.retrieval_service import (
    RetrievalService,
)


router = APIRouter()

retrieval_service = RetrievalService()


def _format_chunk_result(
    result: dict,
):
    chunk = result["chunk"]

    metadata = result[
        "metadata"
    ]

    snippet = chunk.content[
        :RETRIEVAL_SNIPPET_MAX_CHARS
    ]

    return {
        "file_path": chunk.file_path,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "chunk_type": chunk.chunk_type,
        "symbol_name": chunk.symbol_name,
        "content": snippet,
        "retrieval_metadata": metadata,
    }


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "index_loaded": (
            retrieval_service.vector_store
            is not None
        ),
    }


@router.get("/repository-state")
def repository_state():
    return (
        retrieval_service.get_repository_state()
    )


@router.post("/ingest")
def ingest_repository(
    request: IngestRequest,
):
    try:
        retrieval_service.ingest_repository(
            repo_url=request.repo_url
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    return {
        "message": (
            "Repository ingested successfully"
        )
    }


@router.post("/search")
def search_repository(
    request: SearchRequest,
):
    try:
        results = retrieval_service.search(
            query=request.query,
            top_k=request.top_k,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    formatted_results = []

    for result in results:
        formatted_results.append(
            _format_chunk_result(
                result
            )
        )

    return {
        "results": formatted_results
    }


@router.post("/ask")
def ask_question(
    request: AskRequest,
):
    try:
        response = (
            retrieval_service.ask_question(
                query=request.query,
                top_k=request.top_k,
            )
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    formatted_results = []

    for result in response[
        "retrieved_results"
    ]:
        formatted_results.append(
            _format_chunk_result(
                result
            )
        )

    return {
        "answer": response["answer"],
        "retrieval_results": (
            formatted_results
        ),
        "performance_metrics": (
            response[
                "performance_metrics"
            ]
        ),
    }


@router.get("/dependencies")
def get_dependencies(
    file_path: str,
):
    dependencies = (
        retrieval_service.repository_graph.get_dependencies(
            file_path
        )
    )

    return {
        "file_path": file_path,
        "dependencies": dependencies,
    }


@router.get("/symbols")
def search_symbols(
    query: str,
):
    matches = (
        retrieval_service.symbol_registry.search_symbols(
            query
        )
    )

    return {
        "query": query,
        "matches": matches,
    }


@router.get("/summaries")
def search_summaries(
    query: str,
):
    matches = (
        retrieval_service.summary_registry.search_summaries(
            query=query,
            top_k=5,
        )
    )

    return {
        "query": query,
        "matches": matches,
    }


@router.get("/analytics")
def get_analytics():
    return (
        retrieval_service.get_repository_analytics()
    )


@router.get("/dependency-graph")
def dependency_graph():
    return (
        retrieval_service.get_dependency_graph()
    )


@router.get("/explore")
def explore_repository():
    return (
        retrieval_service.get_repository_exploration_data()
    )


@router.get("/file-inspect")
def inspect_file(
    file_path: str = Query(
        ...,
        description=(
            "Absolute file path as stored during ingestion"
        ),
    ),
):
    try:
        return retrieval_service.inspect_file(
            file_path
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error
