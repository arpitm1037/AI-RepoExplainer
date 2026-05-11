import json
from pathlib import Path

import faiss
import numpy as np

from app.models.chunk import CodeChunk


class VectorStore:
    def __init__(
        self,
        embedding_dimension: int,
        *,
        index_path: str | Path = "data/indexes/faiss.index",
        metadata_path: str | Path = "data/indexes/chunks.json",
    ):
        self.embedding_dimension = (
            embedding_dimension
        )

        self.index_path = Path(
            index_path
        )
        self.metadata_path = Path(
            metadata_path
        )

        self.index = faiss.IndexFlatL2(
            embedding_dimension
        )

        self.chunks: list[
            CodeChunk
        ] = []

    def add_embeddings(
        self,
        chunks: list[CodeChunk],
        embeddings: list[list[float]],
    ):
        embedding_array = np.array(
            embeddings,
            dtype="float32",
        )

        self.index.add(embedding_array)

        self.chunks.extend(chunks)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[CodeChunk]:
        query_array = np.array(
            [query_embedding],
            dtype="float32",
        )

        distances, indices = (
            self.index.search(
                query_array,
                top_k,
            )
        )

        retrieved_chunks = []

        for index in indices[0]:
            if index == -1:
                continue

            retrieved_chunks.append(
                self.chunks[index]
            )

        expanded_chunks = (
            self._expand_context(
                retrieved_chunks
            )
        )

        return expanded_chunks

    def _expand_context(
        self,
        chunks: list[CodeChunk],
    ) -> list[CodeChunk]:
        expanded = []

        seen_chunk_ids = set()

        for chunk in chunks:
            neighbors = (
                self._get_neighbor_chunks(
                    chunk
                )
            )

            for neighbor in neighbors:
                if (
                    neighbor.chunk_id
                    not in seen_chunk_ids
                ):
                    expanded.append(
                        neighbor
                    )

                    seen_chunk_ids.add(
                        neighbor.chunk_id
                    )

        return expanded

    def _get_neighbor_chunks(
        self,
        target_chunk: CodeChunk,
    ) -> list[CodeChunk]:
        neighbors = []

        for chunk in self.chunks:
            same_file = (
                chunk.file_path
                == target_chunk.file_path
            )

            nearby = abs(
                chunk.chunk_index
                - target_chunk.chunk_index
            ) <= 1

            if same_file and nearby:
                neighbors.append(chunk)

        return neighbors

    def get_chunks_by_file(
        self,
        file_path: str,
    ) -> list[CodeChunk]:
        matching_chunks = []

        for chunk in self.chunks:
            if (
                chunk.file_path
                == file_path
            ):
                matching_chunks.append(
                    chunk
                )

        return matching_chunks

    def save(self):
        self.index_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss.write_index(
            self.index,
            str(self.index_path),
        )

        chunk_data = [
            chunk.model_dump()
            for chunk in self.chunks
        ]

        with open(
            self.metadata_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                chunk_data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print(
            "\nVector store saved successfully"
        )

    def load(self):
        if not self.index_path.exists():
            raise FileNotFoundError(
                "FAISS index file not found"
            )

        if not self.metadata_path.exists():
            raise FileNotFoundError(
                "Chunk metadata file not found"
            )

        self.index = faiss.read_index(
            str(self.index_path)
        )

        with open(
            self.metadata_path,
            "r",
            encoding="utf-8",
        ) as file:
            chunk_data = json.load(file)

        self.chunks = [
            CodeChunk(**chunk)
            for chunk in chunk_data
        ]

        print(
            "\nVector store loaded successfully"
        )