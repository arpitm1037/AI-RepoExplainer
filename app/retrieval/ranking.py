MAX_CHUNKS_PER_FILE = 2


class RetrievalRanker:
    def __init__(self):
        self.chunk_type_weights = {
            "class": 3.0,
            "function": 2.5,
            "method": 2.0,
            None: 1.0,
        }

        self.source_weights = {
            "summary_search": 5.0,
            "symbol_search": 3.0,
            "semantic_search": 2.0,
            "graph_expansion": 1.0,
        }

    def rerank(
        self,
        query: str,
        retrieval_items,
        repository_graph,
    ):
        scored_chunks = []

        query_terms = set(
            query.lower().split()
        )

        for item in retrieval_items:
            chunk = item["chunk"]

            retrieval_source = item[
                "source"
            ]

            score = 0

            score_breakdown = {
                "keyword_score": 0,
                "symbol_score": 0,
                "chunk_type_score": 0,
                "content_bonus": 0,
                "source_score": 0,
                "importance_score": 0,
            }

            chunk_text = (
                chunk.content.lower()
            )

            symbol_name = (
                chunk.symbol_name or ""
            ).lower()

            keyword_matches = 0

            for term in query_terms:
                if term in chunk_text:
                    keyword_matches += 1

            keyword_score = (
                keyword_matches * 2
            )

            score += keyword_score

            score_breakdown[
                "keyword_score"
            ] = keyword_score

            symbol_score = 0

            for term in query_terms:
                if term in symbol_name:
                    symbol_score += 8

            score += symbol_score

            score_breakdown[
                "symbol_score"
            ] = symbol_score

            chunk_type_weight = (
                self.chunk_type_weights.get(
                    chunk.chunk_type,
                    1.0,
                )
            )

            score += chunk_type_weight

            score_breakdown[
                "chunk_type_score"
            ] = chunk_type_weight

            content_length_bonus = min(
                len(chunk.content) / 1000,
                2,
            )

            score += content_length_bonus

            score_breakdown[
                "content_bonus"
            ] = (
                content_length_bonus
            )

            source_score = (
                self.source_weights.get(
                    retrieval_source,
                    1.0,
                )
            )

            score += source_score

            score_breakdown[
                "source_score"
            ] = source_score

            importance_score = (
                repository_graph.get_importance_score(
                    chunk.file_path
                )
            ) / 100

            score += importance_score

            score_breakdown[
                "importance_score"
            ] = round(
                importance_score,
                2,
            )

            retrieval_metadata = {
                "retrieval_source": (
                    retrieval_source
                ),
                "final_score": round(
                    score,
                    2,
                ),
                "score_breakdown": (
                    score_breakdown
                ),
            }

            scored_chunks.append(
                (
                    score,
                    chunk,
                    retrieval_metadata,
                )
            )

        scored_chunks.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        reranked_chunks = []

        file_counts = {}

        for (
            score,
            chunk,
            metadata,
        ) in scored_chunks:
            current_count = (
                file_counts.get(
                    chunk.file_path,
                    0,
                )
            )

            if (
                current_count
                >= MAX_CHUNKS_PER_FILE
            ):
                continue

            reranked_chunks.append(
                {
                    "chunk": chunk,
                    "metadata": metadata,
                }
            )

            file_counts[
                chunk.file_path
            ] = current_count + 1

        return reranked_chunks