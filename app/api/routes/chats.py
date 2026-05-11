from fastapi import APIRouter, HTTPException, Query
import threading

from app.models.schemas import AskRequest, IngestRequest, SearchRequest
from app.services.chat_manager import ChatManager
from app.core.constants import RETRIEVAL_SNIPPET_MAX_CHARS

# NOTE: chat_manager is a module-level singleton. After changing chat_manager.py
# or retrieval_service.py, do a FULL restart of uvicorn (not just --reload) so
# the new class definition is picked up by this singleton instance.
router = APIRouter()

chat_manager = ChatManager()


def _format_chunk_result(result: dict):
    chunk = result["chunk"]
    metadata = result["metadata"]
    snippet = chunk.content[:RETRIEVAL_SNIPPET_MAX_CHARS]
    return {
        "file_path": chunk.file_path,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "chunk_type": chunk.chunk_type,
        "symbol_name": chunk.symbol_name,
        "content": snippet,
        "retrieval_metadata": metadata,
    }


@router.post("/chats")
def create_chat():
    meta = chat_manager.create_chat()
    return meta.__dict__


@router.get("/chats")
def list_chats():
    return {
        "chats": [m.__dict__ for m in chat_manager.list_chats()]
    }


@router.get("/chats/{chat_id}")
def get_chat(chat_id: str):
    try:
        return chat_manager.get_chat(chat_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/chats/{chat_id}")
def delete_chat(chat_id: str):
    try:
        chat_manager.delete_chat(chat_id)
        return {"deleted": True}
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/chats/{chat_id}/reset")
def reset_chat(chat_id: str):
    try:
        chat_manager.reset_chat_state(chat_id)
        return {"reset": True}
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/chats/{chat_id}/repository-state")
def repository_state(chat_id: str):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        state = svc.get_repository_state()
        return state
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/chats/{chat_id}/ingest")
def ingest_repository(chat_id: str, request: IngestRequest):
    try:
        status = chat_manager.get_ingestion_status(chat_id)

        # Prevent duplicate concurrent ingestion
        if status.running:
            raise HTTPException(status_code=409, detail="Ingestion already in progress")

        # Reset old state cleanly
        chat_manager.reset_chat_state(chat_id)
        status = chat_manager.get_ingestion_status(chat_id)
        status.start()

        svc = chat_manager.get_or_create_service(chat_id)

        def _on_step(label: str, idx: int):
            status.advance(label, idx)

        try:
            svc.ingest_repository(
                repo_url=request.repo_url,
                cancel_event=status.cancel_event,
                on_step=_on_step,
            )
        except InterruptedError:
            # Clean cancellation — reset index so state is consistent
            chat_manager.reset_chat_state(chat_id)
            return {"message": "Ingestion cancelled", "cancelled": True}

        status.finish()
        chat_manager.set_repo_url(chat_id, request.repo_url)
        return {"message": "Repository ingested successfully", "cancelled": False}

    except HTTPException:
        raise
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        # Mark status as not running on unexpected error
        try:
            chat_manager.get_ingestion_status(chat_id).reset()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        # Always ensure running flag is cleared
        try:
            s = chat_manager.get_ingestion_status(chat_id)
            if s.running:
                s.running = False
        except Exception:
            pass


@router.post("/chats/{chat_id}/ingest/cancel")
def cancel_ingestion(chat_id: str):
    """Signal the running ingestion to stop cleanly."""
    try:
        chat_manager.cancel_ingestion(chat_id)
        return {"message": "Cancellation requested"}
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/chats/{chat_id}/ingest/status")
def ingestion_status(chat_id: str):
    """Poll current ingestion progress."""
    try:
        status = chat_manager.get_ingestion_status(chat_id)
        return status.to_dict()
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/chats/{chat_id}/search")
def search_repository(chat_id: str, request: SearchRequest):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        results = svc.search(query=request.query, top_k=request.top_k)
        formatted = [_format_chunk_result(r) for r in results]
        return {"results": formatted}
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/chats/{chat_id}/ask")
def ask_question(chat_id: str, request: AskRequest):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        response = svc.ask_question(query=request.query, top_k=request.top_k)
        formatted_results = [_format_chunk_result(r) for r in response["retrieved_results"]]

        chat_manager.append_history(
            chat_id,
            {"role": "user", "content": request.query, "ts": _now_localish()},
        )
        chat_manager.append_history(
            chat_id,
            {
                "role": "assistant",
                "content": response["answer"],
                "retrievalResults": formatted_results,
                "performanceMetrics": response["performance_metrics"],
                "ts": _now_localish(),
            },
        )

        return {
            "answer": response["answer"],
            "retrieval_results": formatted_results,
            "performance_metrics": response["performance_metrics"],
        }
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


def _now_localish() -> str:
    from datetime import datetime
    return datetime.now().strftime("%H:%M")


@router.get("/chats/{chat_id}/analytics")
def get_analytics(chat_id: str):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        return svc.get_repository_analytics()
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/chats/{chat_id}/dependency-graph")
def dependency_graph(chat_id: str):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        return svc.get_dependency_graph()
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/chats/{chat_id}/explore")
def explore_repository(chat_id: str):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        return svc.get_repository_exploration_data()
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/chats/{chat_id}/file-inspect")
def inspect_file(
    chat_id: str,
    file_path: str = Query(..., description="Absolute file path as stored during ingestion"),
):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        return svc.inspect_file(file_path)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error



def _format_chunk_result(result: dict):
    chunk = result["chunk"]
    metadata = result["metadata"]
    snippet = chunk.content[:RETRIEVAL_SNIPPET_MAX_CHARS]
    return {
        "file_path": chunk.file_path,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "chunk_type": chunk.chunk_type,
        "symbol_name": chunk.symbol_name,
        "content": snippet,
        "retrieval_metadata": metadata,
    }


@router.post("/chats")
def create_chat():
    meta = chat_manager.create_chat()
    return meta.__dict__


@router.get("/chats")
def list_chats():
    return {
        "chats": [m.__dict__ for m in chat_manager.list_chats()]
    }


@router.get("/chats/{chat_id}")
def get_chat(chat_id: str):
    try:
        return chat_manager.get_chat(chat_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/chats/{chat_id}")
def delete_chat(chat_id: str):
    try:
        chat_manager.delete_chat(chat_id)
        return {"deleted": True}
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/chats/{chat_id}/reset")
def reset_chat(chat_id: str):
    try:
        chat_manager.reset_chat_state(chat_id)
        return {"reset": True}
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/chats/{chat_id}/repository-state")
def repository_state(chat_id: str):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        state = svc.get_repository_state()
        return state
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/chats/{chat_id}/ingest")
def ingest_repository(chat_id: str, request: IngestRequest):
    try:
        # Ingest is chat-scoped: blow away old index+repo for this chat first.
        chat_manager.reset_chat_state(chat_id)
        svc = chat_manager.get_or_create_service(chat_id)
        svc.ingest_repository(repo_url=request.repo_url)
        chat_manager.set_repo_url(chat_id, request.repo_url)
        return {"message": "Repository ingested successfully"}
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/chats/{chat_id}/search")
def search_repository(chat_id: str, request: SearchRequest):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        results = svc.search(query=request.query, top_k=request.top_k)
        formatted = [_format_chunk_result(r) for r in results]
        return {"results": formatted}
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/chats/{chat_id}/ask")
def ask_question(chat_id: str, request: AskRequest):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        response = svc.ask_question(query=request.query, top_k=request.top_k)
        formatted_results = [_format_chunk_result(r) for r in response["retrieved_results"]]

        chat_manager.append_history(
            chat_id,
            {"role": "user", "content": request.query, "ts": _now_localish()},
        )
        chat_manager.append_history(
            chat_id,
            {
                "role": "assistant",
                "content": response["answer"],
                "retrievalResults": formatted_results,
                "performanceMetrics": response["performance_metrics"],
                "ts": _now_localish(),
            },
        )

        return {
            "answer": response["answer"],
            "retrieval_results": formatted_results,
            "performance_metrics": response["performance_metrics"],
        }
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


def _now_localish() -> str:
    # Frontend displays this as a plain string; keep it simple.
    from datetime import datetime

    return datetime.now().strftime("%H:%M")


@router.get("/chats/{chat_id}/analytics")
def get_analytics(chat_id: str):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        return svc.get_repository_analytics()
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/chats/{chat_id}/dependency-graph")
def dependency_graph(chat_id: str):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        return svc.get_dependency_graph()
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/chats/{chat_id}/explore")
def explore_repository(chat_id: str):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        return svc.get_repository_exploration_data()
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/chats/{chat_id}/file-inspect")
def inspect_file(
    chat_id: str,
    file_path: str = Query(..., description="Absolute file path as stored during ingestion"),
):
    try:
        svc = chat_manager.get_or_create_service(chat_id)
        return svc.inspect_file(file_path)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

