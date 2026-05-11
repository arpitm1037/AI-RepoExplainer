import json
import time

from pathlib import Path
from datetime import (
    datetime,
    timezone,
)

from app.ingestion.repo_cloner import (
    RepoCloner,
)

from app.ingestion.file_scanner import (
    FileScanner,
)

from app.ingestion.file_loader import (
    FileLoader,
)

from app.processing.chunker import (
    CodeChunker,
)

from app.embeddings.embedding_model import (
    EmbeddingModel,
)

from app.embeddings.vector_store import (
    VectorStore,
)

from app.retrieval.ranking import (
    RetrievalRanker,
)

from app.retrieval.repository_graph import (
    RepositoryGraph,
)

from app.retrieval.symbol_registry import (
    SymbolRegistry,
)

from app.retrieval.summary_registry import (
    SummaryRegistry,
)

from app.retrieval.query_expander import (
    QueryExpander,
)

from app.llm.generator import (
    LLMGenerator,
)


MAX_INSPECT_FILE_BYTES = 400_000


class RetrievalService:
    def __init__(
        self,
        *,
        chat_root: str | Path = "data",
    ):
        self.chat_root = Path(
            chat_root
        )

        self.index_dir = (
            self.chat_root
            / "indexes"
        )
        self.index_path = (
            self.index_dir
            / "faiss.index"
        )
        self.metadata_path = (
            self.index_dir
            / "chunks.json"
        )
        self.repository_state_path = (
            self.index_dir
            / "repository_state.json"
        )

        self.cloner = RepoCloner(
            base_path=str(
                self.chat_root
                / "repos"
            )
        )

        self.scanner = FileScanner()

        self.loader = FileLoader()

        self.chunker = CodeChunker()

        self.embedding_model = (
            EmbeddingModel()
        )

        self.ranker = RetrievalRanker()

        self.repository_graph = (
            RepositoryGraph()
        )

        self.symbol_registry = (
            SymbolRegistry()
        )

        self.summary_registry = (
            SummaryRegistry()
        )

        self.query_expander = (
            QueryExpander()
        )

        self.generator = (
            LLMGenerator()
        )

        self.query_cache = {}

        self.vector_store = None
        self.last_repo_url = None
        self.last_ingested_at = None

        self._load_existing_index()

    def _load_existing_index(
        self,
    ):
        if not self.index_path.exists():
            return

        self.vector_store = (
            VectorStore(
                embedding_dimension=384,
                index_path=self.index_path,
                metadata_path=self.metadata_path,
            )
        )

        self.vector_store.load()

        print(
            "\nExisting FAISS index loaded"
        )

        self._load_repository_state()

    def get_repository_analytics(
        self,
    ):
        if not self.vector_store:
            return {
                "total_chunks": 0,
                "total_symbols": 0,
                "total_files": 0,
                "semantic_search": False,
                "graph_ranking": False,
                "symbol_registry": False,
            }

        total_chunks = len(
            self.vector_store.chunks
        )

        total_symbols = len(
            self.symbol_registry.symbols
        )

        indexed_files = set()

        for chunk in (
            self.vector_store.chunks
        ):
            indexed_files.add(
                chunk.file_path
            )

        return {
            "total_chunks":
                total_chunks,
            "total_symbols":
                total_symbols,
            "total_files":
                len(indexed_files),
            "semantic_search":
                True,
            "graph_ranking":
                True,
            "symbol_registry":
                True,
        }

    def ingest_repository(
        self,
        repo_url: str,
        cancel_event=None,
        on_step=None,
    ):
        """
        Ingest a repository.

        cancel_event: threading.Event — set it to abort mid-pipeline.
        on_step: callable(step_label, step_index) — called at each stage.
        """

        def _step(label: str, idx: int):
            if on_step:
                on_step(label, idx)
            if cancel_event and cancel_event.is_set():
                raise InterruptedError(f"Ingestion cancelled at: {label}")

        _step("Cloning repository…", 1)
        repo_path = self.cloner.clone_repository(repo_url)

        _step("Scanning files…", 2)
        files = self.scanner.scan_repository(repo_path)

        _step("Loading documents…", 3)
        documents = self.loader.load_files(files)

        _step("Building dependency graph…", 4)
        self.repository_graph.build_graph(documents)
        self.summary_registry.build_summaries(documents)

        _step("Chunking code…", 5)
        chunks = self.chunker.chunk_documents(documents)
        self.symbol_registry.register_chunks(chunks)

        _step("Generating embeddings…", 6)
        embeddings = self.embedding_model.embed_chunks(chunks)

        _step("Saving index…", 7)
        self.vector_store = VectorStore(
            embedding_dimension=len(embeddings[0]),
            index_path=self.index_path,
            metadata_path=self.metadata_path,
        )
        self.vector_store.add_embeddings(chunks, embeddings)

        self.last_repo_url = repo_url
        self.last_ingested_at = datetime.now(timezone.utc).isoformat()

        self.vector_store.save()
        self._persist_repository_state()
        self.query_cache.clear()

        print("\nRepository ingestion completed")

    def _persist_repository_state(
        self,
    ):
        self.index_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "repository_graph": (
                self.repository_graph.export_state()
            ),
            "symbols": (
                self.symbol_registry.symbols
            ),
            "summaries": (
                self.summary_registry.summaries
            ),
            "metadata": {
                "last_repo_url": (
                    self.last_repo_url
                ),
                "last_ingested_at": (
                    self.last_ingested_at
                ),
            },
        }

        with open(
            self.repository_state_path,
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                payload,
                handle,
                ensure_ascii=False,
                indent=2,
            )

        print(
            "\nRepository state persisted"
        )

    def _load_repository_state(
        self,
    ):
        path = Path(
            self.repository_state_path
        )

        if not path.exists():
            print(
                "\nNo repository_state.json; "
                "graph and symbols empty until "
                "re-ingest"
            )

            return

        try:
            with open(
                path,
                "r",
                encoding="utf-8",
            ) as handle:
                payload = json.load(
                    handle
                )
        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            print(
                f"\nFailed to load repository state: {error}"
            )

            return

        graph_state = payload.get(
            "repository_graph",
            {},
        )

        self.repository_graph.restore_state(
            graph_state
        )

        self.symbol_registry.restore_symbols(
            payload.get(
                "symbols",
                {},
            )
        )

        self.summary_registry.restore_summaries(
            payload.get(
                "summaries",
                {},
            )
        )
        metadata = payload.get(
            "metadata",
            {},
        )
        self.last_repo_url = (
            metadata.get(
                "last_repo_url"
            )
        )
        self.last_ingested_at = (
            metadata.get(
                "last_ingested_at"
            )
        )

        if (
            self.summary_registry.summaries
        ):
            print(
                "\nRebuilding summary embeddings "
                "from persisted summaries..."
            )

            self.summary_registry.rebuild_summary_embeddings()

        print(
            "\nRepository state restored"
        )

    def get_repository_state(
        self,
    ):
        indexed = (
            self.vector_store
            is not None
        )
        indexed_files = 0

        if self.vector_store:
            indexed_files = len(
                {
                    chunk.file_path
                    for chunk in self.vector_store.chunks
                }
            )

        return {
            "indexed": indexed,
            "last_repo_url": (
                self.last_repo_url
            ),
            "last_ingested_at": (
                self.last_ingested_at
            ),
            "indexed_files": indexed_files,
        }

    def inspect_file(
        self,
        file_path: str,
    ):
        if not self.vector_store:
            raise ValueError(
                "Repository has not been ingested"
            )

        indexed_paths = {
            chunk.file_path
            for chunk in (
                self.vector_store.chunks
            )
        }

        if (
            file_path
            not in indexed_paths
        ):
            raise ValueError(
                "File is not part of the indexed repository"
            )

        path = Path(
            file_path
        )

        if not path.is_file():
            raise ValueError(
                "File is not available on disk "
                "(clone may be missing)"
            )

        raw = path.read_bytes()

        truncated = (
            len(raw) > MAX_INSPECT_FILE_BYTES
        )

        if truncated:
            raw = raw[
                :MAX_INSPECT_FILE_BYTES
            ]

        content = raw.decode(
            "utf-8",
            errors="replace",
        )

        if truncated:
            content += (
                "\n\n... [truncated for inspection cap]"
            )

        dependencies = (
            self.repository_graph.get_dependencies(
                file_path
            )
        )

        summary = (
            self.summary_registry.get_summary(
                file_path
            )
        )

        symbols_detail = []

        for (
            symbol_name,
            metadata,
        ) in self.symbol_registry.symbols.items():
            if (
                metadata.get(
                    "file_path"
                )
                != file_path
            ):
                continue

            symbols_detail.append(
                {
                    "symbol_name": (
                        symbol_name
                    ),
                    "chunk_type": (
                        metadata.get(
                            "chunk_type"
                        )
                    ),
                    "start_line": (
                        metadata.get(
                            "start_line"
                        )
                    ),
                    "end_line": (
                        metadata.get(
                            "end_line"
                        )
                    ),
                    "chunk_id": (
                        metadata.get(
                            "chunk_id"
                        )
                    ),
                }
            )

        symbols_detail.sort(
            key=lambda item: (
                item.get(
                    "start_line",
                    0,
                ),
                item.get(
                    "symbol_name",
                    "",
                ),
            )
        )

        related_files = (
            self.repository_graph.find_related_files(
                file_path
            )
        )

        return {
            "file_path": str(
                path
            ),
            "extension": path.suffix,
            "size_bytes": path.stat().st_size,
            "content": content,
            "truncated": truncated,
            "summary": summary,
            "dependencies": dependencies,
            "related_files": related_files[
                :50
            ],
            "symbols": symbols_detail,
        }

    def _retrieve_summary_matches(
        self,
        query: str,
    ):
        return (
            self.summary_registry.search_summaries(
                query=query,
                top_k=5,
            )
        )

    def _retrieve_chunks_from_files(
        self,
        file_paths: list[str],
    ):
        matching_chunks = []

        seen_chunk_ids = set()

        for file_path in file_paths:
            file_chunks = (
                self.vector_store.get_chunks_by_file(
                    file_path
                )
            )

            for chunk in file_chunks[:5]:
                if (
                    chunk.chunk_id
                    not in seen_chunk_ids
                ):
                    matching_chunks.append(
                        chunk
                    )

                    seen_chunk_ids.add(
                        chunk.chunk_id
                    )

        return matching_chunks

    def _retrieve_symbol_chunks(
        self,
        query: str,
    ):
        matching_chunks = []

        symbol_matches = (
            self.symbol_registry.search_symbols(
                query
            )
        )

        seen_chunk_ids = set()

        for match in symbol_matches:
            metadata = (
                match["metadata"]
            )

            chunk_id = metadata[
                "chunk_id"
            ]

            for chunk in (
                self.vector_store.chunks
            ):
                if (
                    chunk.chunk_id
                    == chunk_id
                ):
                    if (
                        chunk.chunk_id
                        not in seen_chunk_ids
                    ):
                        matching_chunks.append(
                            chunk
                        )

                        seen_chunk_ids.add(
                            chunk.chunk_id
                        )

        return matching_chunks

    def get_dependency_graph(
        self,
    ):
        nodes = set()

        links = []

        for (
            source_file,
            dependencies
        ) in (
            self.repository_graph.graph.items()
        ):
            nodes.add(
                source_file
            )

            for target_file in (
                dependencies
            ):
                nodes.add(
                    target_file
                )

                links.append(
                    {
                        "source":
                            source_file,
                        "target":
                            target_file,
                    }
                )

        return {
            "nodes": [
                {
                    "id": node
                }
                for node in nodes
            ],
            "links": links,
        }

    def _build_repository_context_for_query_expansion(
        self,
        max_chars: int = 4000,
    ) -> str:
        if not self.vector_store:
            return (
                "Repository not indexed; no context "
                "available."
            )

        indexed_files = sorted(
            {
                chunk.file_path
                for chunk in self.vector_store.chunks
            }
        )

        lines = [
            (
                f"Total indexed files: "
                f"{len(indexed_files)}"
            ),
        ]

        preview_limit = 40

        preview_paths = (
            indexed_files[:preview_limit]
        )

        lines.append(
            "Sample paths:\n"
            + "\n".join(
                f"- {path}"
                for path in preview_paths
            )
        )

        if (
            len(indexed_files)
            > preview_limit
        ):
            lines.append(
                f"... and "
                f"{len(indexed_files) - preview_limit} "
                f"additional files."
            )

        summary_blocks = []

        for file_path in indexed_files[
            :35
        ]:
            summary = (
                self.summary_registry.get_summary(
                    file_path
                )
            )

            if not summary:
                continue

            snippet = (
                summary.strip().replace(
                    "\n",
                    " ",
                )[:320]
            )

            summary_blocks.append(
                f"{file_path} :: {snippet}"
            )

        if summary_blocks:
            lines.append(
                "Architecture-oriented summaries "
                "(truncated):\n"
                + "\n".join(
                    summary_blocks[
                        :22
                    ]
                )
            )

        text = "\n\n".join(
            lines
        )

        if (
            len(text)
            > max_chars
        ):
            return (
                text[
                    : max_chars
                    - 3
                ]
                + "..."
            )

        return text

    def search(
        self,
        query: str,
        top_k: int = 2,
    ):
        if not self.vector_store:
            raise ValueError(
                "Repository has not been ingested"
            )

        cache_key = (
            f"search:{query}:{top_k}"
        )

        if cache_key in (
            self.query_cache
        ):
            print(
                "Using cached search results"
            )

            return self.query_cache[
                cache_key
            ]

        repository_context = (
            self._build_repository_context_for_query_expansion()
        )

        expanded_query = (
            self.query_expander.expand_query(
                query,
                repository_context,
            )
        )

        print(
            "\nEXPANDED QUERY:\n"
        )

        print(
            expanded_query
        )

        retrieval_items = []

        summary_matches = (
            self._retrieve_summary_matches(
                expanded_query
            )
        )

        summary_files = [
            match["file_path"]
            for match
            in summary_matches
        ]

        summary_chunks = (
            self._retrieve_chunks_from_files(
                summary_files
            )
        )

        for chunk in summary_chunks:
            retrieval_items.append(
                {
                    "chunk": chunk,
                    "source": (
                        "summary_search"
                    ),
                }
            )

        query_embedding = (
            self.embedding_model.embed_text(
                expanded_query
            )
        )

        semantic_chunks = (
            self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k * 3,
            )
        )

        for chunk in semantic_chunks:
            retrieval_items.append(
                {
                    "chunk": chunk,
                    "source": (
                        "semantic_search"
                    ),
                }
            )

        symbol_chunks = (
            self._retrieve_symbol_chunks(
                expanded_query
            )
        )

        for chunk in symbol_chunks:
            retrieval_items.append(
                {
                    "chunk": chunk,
                    "source": (
                        "symbol_search"
                    ),
                }
            )

        deduplicated_items = []

        seen_chunk_ids = set()

        for item in retrieval_items:
            chunk = item["chunk"]

            if (
                chunk.chunk_id
                not in seen_chunk_ids
            ):
                deduplicated_items.append(
                    item
                )

                seen_chunk_ids.add(
                    chunk.chunk_id
                )

        expanded_items = []

        for item in deduplicated_items:
            expanded_items.append(
                item
            )

            chunk = item["chunk"]

            related_files = (
                self.repository_graph.find_related_files(
                    chunk.file_path
                )
            )

            for file_path in related_files:
                related_chunks = (
                    self.vector_store.get_chunks_by_file(
                        file_path
                    )
                )

                for related_chunk in related_chunks[:2]:
                    if (
                        related_chunk.chunk_id
                        not in seen_chunk_ids
                    ):
                        expanded_items.append(
                            {
                                "chunk":
                                    related_chunk,
                                "source":
                                    "graph_expansion",
                            }
                        )

                        seen_chunk_ids.add(
                            related_chunk.chunk_id
                        )

        reranked_results = (
            self.ranker.rerank(
                query=expanded_query,
                retrieval_items=expanded_items,
                repository_graph=(
                    self.repository_graph
                ),
            )
        )

        final_results = (
            reranked_results[:top_k]
        )

        self.query_cache[
            cache_key
        ] = final_results

        return final_results

    def ask_question(
        self,
        query: str,
        top_k: int = 2,
    ):
        total_start_time = (
            time.time()
        )

        cache_key = (
            f"ask:{query}:{top_k}"
        )

        if cache_key in (
            self.query_cache
        ):
            print(
                "Using cached answer"
            )

            cached_response = (
                self.query_cache[
                    cache_key
                ]
            )

            return {
                "answer": (
                    cached_response[
                        "answer"
                    ]
                ),
                "retrieved_results": (
                    cached_response[
                        "retrieved_results"
                    ]
                ),
                "performance_metrics": {
                    "cache_hit": True,
                    "retrieval_time": 0,
                    "generation_time": 0,
                    "total_time": 0,
                },
            }

        retrieval_start_time = (
            time.time()
        )

        summary_matches = (
            self._retrieve_summary_matches(
                query
            )
        )

        retrieved_results = (
            self.search(
                query=query,
                top_k=top_k,
            )
        )

        retrieval_time = (
            time.time()
            - retrieval_start_time
        )

        retrieved_chunks = [
            result["chunk"]
            for result
            in retrieved_results
        ]

        architecture_context = []

        for match in summary_matches:
            architecture_context.append(
                f"""
FILE:
{match["file_path"]}

SUMMARY:
{match["summary"][:500]}
"""
            )

        architecture_context_text = (
            "\n".join(
                architecture_context
            )
        )

        implementation_context = []

        for chunk in retrieved_chunks:
            implementation_context.append(
                f"""
FILE:
{chunk.file_path}

LINES:
{chunk.start_line}-
{chunk.end_line}

CODE:
{chunk.content[:1200]}
"""
            )

        implementation_context_text = (
            "\n".join(
                implementation_context
            )
        )

        final_prompt = f"""
You are an expert AI codebase analysis system.

Use BOTH:
1. Architectural repository context
2. Implementation-level code context

to answer the question accurately.

========================
ARCHITECTURAL CONTEXT
========================

{architecture_context_text}

========================
IMPLEMENTATION CONTEXT
========================

{implementation_context_text}

========================
QUESTION
========================

{query}
"""

        generation_start_time = (
            time.time()
        )

        answer = (
            self.generator.generate_response(
                final_prompt
            )
        )

        generation_time = (
            time.time()
            - generation_start_time
        )

        total_time = (
            time.time()
            - total_start_time
        )

        response_payload = {
            "answer": answer,
            "retrieved_results":
                retrieved_results,
            "performance_metrics": {
                "cache_hit":
                    False,
                "retrieval_time":
                    round(
                        retrieval_time,
                        2,
                    ),
                "generation_time":
                    round(
                        generation_time,
                        2,
                    ),
                "total_time":
                    round(
                        total_time,
                        2,
                    ),
            },
        }

        self.query_cache[
            cache_key
        ] = response_payload

        return response_payload

    def get_repository_exploration_data(
        self,
    ):
        if not self.vector_store:
            return {"files": []}

        chunk_counts = {}

        indexed_files = set()

        for chunk in self.vector_store.chunks:
            indexed_files.add(
                chunk.file_path
            )

            chunk_counts[
                chunk.file_path
            ] = (
                chunk_counts.get(
                    chunk.file_path,
                    0,
                )
                + 1
            )

        symbols_by_file = {}

        for (
            symbol_name,
            metadata,
        ) in self.symbol_registry.symbols.items():
            file_path = metadata[
                "file_path"
            ]

            if (
                file_path
                not in symbols_by_file
            ):
                symbols_by_file[
                    file_path
                ] = []

            symbols_by_file[
                file_path
            ].append(
                symbol_name
            )

        file_data = []

        for file_path in sorted(
            indexed_files
        ):
            dependencies = (
                self.repository_graph.get_dependencies(
                    file_path
                )
            )

            symbol_names = (
                symbols_by_file.get(
                    file_path,
                    [],
                )
            )

            symbols_preview = sorted(
                symbol_names
            )[:20]

            summary = (
                self.summary_registry.get_summary(
                    file_path
                )
            )

            file_data.append(
                {
                    "file_path": file_path,
                    "summary": summary,
                    "dependency_count": len(
                        dependencies
                    ),
                    "symbol_count": len(
                        symbol_names
                    ),
                    "chunk_count": (
                        chunk_counts.get(
                            file_path,
                            0,
                        )
                    ),
                    "dependencies": dependencies,
                    "symbols_preview": (
                        symbols_preview
                    ),
                }
            )

        return {"files": file_data}