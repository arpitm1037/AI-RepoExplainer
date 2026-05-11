from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.services.retrieval_service import RetrievalService


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ChatSessionMeta:
    chat_id: str
    title: str
    created_at: str
    updated_at: str
    repo_url: str | None = None


@dataclass
class IngestionStatus:
    """Tracks live ingestion progress for a single chat."""
    running: bool = False
    step: str = ""
    step_index: int = 0
    total_steps: int = 7
    cancel_event: threading.Event = field(default_factory=threading.Event)

    def reset(self) -> None:
        self.running = False
        self.step = ""
        self.step_index = 0
        self.cancel_event.clear()

    def start(self) -> None:
        self.cancel_event.clear()
        self.running = True
        self.step_index = 0
        self.step = "Starting…"

    def advance(self, step: str, index: int) -> None:
        self.step = step
        self.step_index = index

    def stop(self) -> None:
        self.cancel_event.set()
        self.running = False
        self.step = "Stopped"

    def finish(self) -> None:
        self.running = False
        self.step = "Done"
        self.step_index = self.total_steps

    @property
    def cancelled(self) -> bool:
        return self.cancel_event.is_set()

    def to_dict(self) -> dict:
        return {
            "running": self.running,
            "step": self.step,
            "step_index": self.step_index,
            "total_steps": self.total_steps,
            "cancelled": self.cancelled,
        }


class ChatManager:
    """
    Owns chat-scoped state and persistence.

    Root guarantee: no cross-chat leakage.
    Each chat_id gets an isolated directory:
      data/chats/<chat_id>/{indexes,repos,chat.json}
    """

    def __init__(self, base_dir: str | Path = "data/chats"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self._services: dict[str, RetrievalService] = {}
        self._ingestion_status: dict[str, IngestionStatus] = {}

    def __getattr__(self, name: str):
        # Safety net: if a stale instance is missing new attributes added after
        # the instance was created (e.g. during uvicorn --reload), initialise
        # them lazily so we never get AttributeError on live instances.
        if name == "_ingestion_status":
            object.__setattr__(self, "_ingestion_status", {})
            return self._ingestion_status
        if name == "_lock":
            object.__setattr__(self, "_lock", threading.RLock())
            return self._lock
        if name == "_services":
            object.__setattr__(self, "_services", {})
            return self._services
        raise AttributeError(f"'ChatManager' object has no attribute '{name}'")

    # ── ingestion status helpers ──────────────────────────────────────────────

    def get_ingestion_status(self, chat_id: str) -> IngestionStatus:
        with self._lock:
            if chat_id not in self._ingestion_status:
                self._ingestion_status[chat_id] = IngestionStatus()
            return self._ingestion_status[chat_id]

    def cancel_ingestion(self, chat_id: str) -> None:
        status = self.get_ingestion_status(chat_id)
        status.stop()

    # ── private helpers ───────────────────────────────────────────────────────

    def _chat_dir(self, chat_id: str) -> Path:
        return self.base_dir / chat_id

    def _meta_path(self, chat_id: str) -> Path:
        return self._chat_dir(chat_id) / "chat.json"

    def _load_meta(self, chat_id: str) -> ChatSessionMeta:
        path = self._meta_path(chat_id)
        if not path.exists():
            raise KeyError(f"Unknown chat_id: {chat_id}")

        payload = json.loads(path.read_text(encoding="utf-8"))
        return ChatSessionMeta(**payload["meta"])

    def _save_meta(self, meta: ChatSessionMeta) -> None:
        chat_dir = self._chat_dir(meta.chat_id)
        chat_dir.mkdir(parents=True, exist_ok=True)

        path = self._meta_path(meta.chat_id)
        payload: dict[str, Any] = {
            "meta": {
                "chat_id": meta.chat_id,
                "title": meta.title,
                "created_at": meta.created_at,
                "updated_at": meta.updated_at,
                "repo_url": meta.repo_url,
            },
            "messages": self.get_history(meta.chat_id),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def create_chat(self, *, title: str = "New chat") -> ChatSessionMeta:
        with self._lock:
            chat_id = uuid4().hex
            now = _utc_now_iso()
            meta = ChatSessionMeta(
                chat_id=chat_id,
                title=title,
                created_at=now,
                updated_at=now,
                repo_url=None,
            )
            # initialize empty chat file
            self._chat_dir(chat_id).mkdir(parents=True, exist_ok=True)
            self._meta_path(chat_id).write_text(
                json.dumps({"meta": meta.__dict__, "messages": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return meta

    def list_chats(self) -> list[ChatSessionMeta]:
        with self._lock:
            metas: list[ChatSessionMeta] = []
            for child in self.base_dir.iterdir():
                if not child.is_dir():
                    continue
                meta_path = child / "chat.json"
                if not meta_path.exists():
                    continue
                try:
                    payload = json.loads(meta_path.read_text(encoding="utf-8"))
                    metas.append(ChatSessionMeta(**payload["meta"]))
                except Exception:
                    continue
            metas.sort(key=lambda m: m.updated_at, reverse=True)
            return metas

    def get_history(self, chat_id: str) -> list[dict[str, Any]]:
        path = self._meta_path(chat_id)
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            messages = payload.get("messages", [])
            return messages if isinstance(messages, list) else []
        except Exception:
            return []

    def append_history(self, chat_id: str, message: dict[str, Any]) -> None:
        with self._lock:
            path = self._meta_path(chat_id)
            if not path.exists():
                raise KeyError(f"Unknown chat_id: {chat_id}")
            payload = json.loads(path.read_text(encoding="utf-8"))
            messages = payload.get("messages", [])
            if not isinstance(messages, list):
                messages = []
            messages.append(message)
            payload["messages"] = messages
            payload["meta"]["updated_at"] = _utc_now_iso()
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_or_create_service(self, chat_id: str) -> RetrievalService:
        with self._lock:
            # validate existence
            _ = self._load_meta(chat_id)
            if chat_id not in self._services:
                self._services[chat_id] = RetrievalService(chat_root=self._chat_dir(chat_id))
            return self._services[chat_id]

    def reset_chat_state(self, chat_id: str) -> None:
        """
        Hard reset ingestion/index state for the chat without deleting messages.
        """
        with self._lock:
            chat_dir = self._chat_dir(chat_id)
            if not chat_dir.exists():
                raise KeyError(f"Unknown chat_id: {chat_id}")

            # Drop in-memory service (so caches can't leak)
            self._services.pop(chat_id, None)

            # Reset ingestion status
            if chat_id in self._ingestion_status:
                self._ingestion_status[chat_id].reset()

            # Delete chat-scoped indexes + repos
            for sub in ("indexes", "repos"):
                target = chat_dir / sub
                if target.exists():
                    for p in sorted(target.rglob("*"), reverse=True):
                        if p.is_file():
                            p.unlink(missing_ok=True)
                        elif p.is_dir():
                            p.rmdir()
                    target.rmdir()

            # Clear repo_url in meta
            payload = json.loads(self._meta_path(chat_id).read_text(encoding="utf-8"))
            payload["meta"]["repo_url"] = None
            payload["meta"]["updated_at"] = _utc_now_iso()
            self._meta_path(chat_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def set_repo_url(self, chat_id: str, repo_url: str | None) -> None:
        with self._lock:
            payload = json.loads(self._meta_path(chat_id).read_text(encoding="utf-8"))
            payload["meta"]["repo_url"] = repo_url
            payload["meta"]["updated_at"] = _utc_now_iso()
            self._meta_path(chat_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_chat(self, chat_id: str) -> dict[str, Any]:
        meta = self._load_meta(chat_id)
        return {
            "meta": meta.__dict__,
            "messages": self.get_history(chat_id),
        }

    def delete_chat(self, chat_id: str) -> None:
        with self._lock:
            chat_dir = self._chat_dir(chat_id)
            if not chat_dir.exists():
                raise KeyError(f"Unknown chat_id: {chat_id}")

            self._services.pop(chat_id, None)
            self._ingestion_status.pop(chat_id, None)

            for p in sorted(chat_dir.rglob("*"), reverse=True):
                if p.is_file():
                    p.unlink(missing_ok=True)
                elif p.is_dir():
                    p.rmdir()
            chat_dir.rmdir()

    """
    Owns chat-scoped state and persistence.

    Root guarantee: no cross-chat leakage.
    Each chat_id gets an isolated directory:
      data/chats/<chat_id>/{indexes,repos,chat.json}
    """

    def __init__(self, base_dir: str | Path = "data/chats"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.RLock()
        self._services: dict[str, RetrievalService] = {}

    def _chat_dir(self, chat_id: str) -> Path:
        return self.base_dir / chat_id

    def _meta_path(self, chat_id: str) -> Path:
        return self._chat_dir(chat_id) / "chat.json"

    def _load_meta(self, chat_id: str) -> ChatSessionMeta:
        path = self._meta_path(chat_id)
        if not path.exists():
            raise KeyError(f"Unknown chat_id: {chat_id}")

        payload = json.loads(path.read_text(encoding="utf-8"))
        return ChatSessionMeta(**payload["meta"])

    def _save_meta(self, meta: ChatSessionMeta) -> None:
        chat_dir = self._chat_dir(meta.chat_id)
        chat_dir.mkdir(parents=True, exist_ok=True)

        path = self._meta_path(meta.chat_id)
        payload: dict[str, Any] = {
            "meta": {
                "chat_id": meta.chat_id,
                "title": meta.title,
                "created_at": meta.created_at,
                "updated_at": meta.updated_at,
                "repo_url": meta.repo_url,
            },
            "messages": self.get_history(meta.chat_id),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def create_chat(self, *, title: str = "New chat") -> ChatSessionMeta:
        with self._lock:
            chat_id = uuid4().hex
            now = _utc_now_iso()
            meta = ChatSessionMeta(
                chat_id=chat_id,
                title=title,
                created_at=now,
                updated_at=now,
                repo_url=None,
            )
            # initialize empty chat file
            self._chat_dir(chat_id).mkdir(parents=True, exist_ok=True)
            self._meta_path(chat_id).write_text(
                json.dumps({"meta": meta.__dict__, "messages": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return meta

    def list_chats(self) -> list[ChatSessionMeta]:
        with self._lock:
            metas: list[ChatSessionMeta] = []
            for child in self.base_dir.iterdir():
                if not child.is_dir():
                    continue
                meta_path = child / "chat.json"
                if not meta_path.exists():
                    continue
                try:
                    payload = json.loads(meta_path.read_text(encoding="utf-8"))
                    metas.append(ChatSessionMeta(**payload["meta"]))
                except Exception:
                    continue
            metas.sort(key=lambda m: m.updated_at, reverse=True)
            return metas

    def get_history(self, chat_id: str) -> list[dict[str, Any]]:
        path = self._meta_path(chat_id)
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            messages = payload.get("messages", [])
            return messages if isinstance(messages, list) else []
        except Exception:
            return []

    def append_history(self, chat_id: str, message: dict[str, Any]) -> None:
        with self._lock:
            path = self._meta_path(chat_id)
            if not path.exists():
                raise KeyError(f"Unknown chat_id: {chat_id}")
            payload = json.loads(path.read_text(encoding="utf-8"))
            messages = payload.get("messages", [])
            if not isinstance(messages, list):
                messages = []
            messages.append(message)
            payload["messages"] = messages
            payload["meta"]["updated_at"] = _utc_now_iso()
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_or_create_service(self, chat_id: str) -> RetrievalService:
        with self._lock:
            # validate existence
            _ = self._load_meta(chat_id)
            if chat_id not in self._services:
                self._services[chat_id] = RetrievalService(chat_root=self._chat_dir(chat_id))
            return self._services[chat_id]

    def reset_chat_state(self, chat_id: str) -> None:
        """
        Hard reset ingestion/index state for the chat without deleting messages.
        """
        with self._lock:
            chat_dir = self._chat_dir(chat_id)
            if not chat_dir.exists():
                raise KeyError(f"Unknown chat_id: {chat_id}")

            # Drop in-memory service (so caches can't leak)
            self._services.pop(chat_id, None)

            # Delete chat-scoped indexes + repos
            for sub in ("indexes", "repos"):
                target = chat_dir / sub
                if target.exists():
                    for p in sorted(target.rglob("*"), reverse=True):
                        if p.is_file():
                            p.unlink(missing_ok=True)
                        elif p.is_dir():
                            p.rmdir()
                    target.rmdir()

            # Clear repo_url in meta
            payload = json.loads(self._meta_path(chat_id).read_text(encoding="utf-8"))
            payload["meta"]["repo_url"] = None
            payload["meta"]["updated_at"] = _utc_now_iso()
            self._meta_path(chat_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def set_repo_url(self, chat_id: str, repo_url: str | None) -> None:
        with self._lock:
            payload = json.loads(self._meta_path(chat_id).read_text(encoding="utf-8"))
            payload["meta"]["repo_url"] = repo_url
            payload["meta"]["updated_at"] = _utc_now_iso()
            self._meta_path(chat_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_chat(self, chat_id: str) -> dict[str, Any]:
        meta = self._load_meta(chat_id)
        return {
            "meta": meta.__dict__,
            "messages": self.get_history(chat_id),
        }

    def delete_chat(self, chat_id: str) -> None:
        with self._lock:
            chat_dir = self._chat_dir(chat_id)
            if not chat_dir.exists():
                raise KeyError(f"Unknown chat_id: {chat_id}")

            self._services.pop(chat_id, None)

            for p in sorted(chat_dir.rglob("*"), reverse=True):
                if p.is_file():
                    p.unlink(missing_ok=True)
                elif p.is_dir():
                    p.rmdir()
            chat_dir.rmdir()

