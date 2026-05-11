import numpy as np

from app.models.document import (
    CodeDocument,
)

from app.llm.generator import (
    LLMGenerator,
)

from app.embeddings.embedding_model import (
    EmbeddingModel,
)


MIN_SUMMARY_FILE_SIZE = 1500


class SummaryRegistry:
    def __init__(self):
        self.summaries = {}

        self.summary_embeddings = {}

        self.generator = (
            LLMGenerator()
        )

        self.embedding_model = (
            EmbeddingModel()
        )

    def build_summaries(
        self,
        documents: list[CodeDocument],
    ):
        for document in documents:
            if (
                len(document.content)
                < MIN_SUMMARY_FILE_SIZE
            ):
                continue

            summary = (
                self._generate_summary(
                    document
                )
            )

            embedding = (
                self.embedding_model.embed_text(
                    summary
                )
            )

            self.summaries[
                document.file_path
            ] = summary

            self.summary_embeddings[
                document.file_path
            ] = embedding

            print(
                f"\nSummary created for:"
                f" {document.file_path}"
            )

    def _generate_summary(
        self,
        document: CodeDocument,
    ) -> str:
        truncated_content = (
            document.content[:5000]
        )

        prompt = f"""
You are generating a retrieval-oriented
semantic repository summary.

Your goal is NOT readability.

Your goal is maximizing semantic retrieval quality.

Analyze this code file and produce a dense,
architecture-aware summary.

Include:
- subsystem responsibilities
- architectural role
- important APIs
- important classes
- important functions
- routing behavior
- dependency behavior
- middleware behavior
- lifecycle management
- authentication behavior
- serialization behavior
- validation behavior
- request handling
- response handling
- data flow concepts
- internal framework concepts

IMPORTANT:
Use highly searchable technical terms.

IMPORTANT:
Do NOT explain casually.

IMPORTANT:
Compress maximum semantic meaning
into concise technical language.

FILE PATH:
{document.file_path}

CODE:
{truncated_content}
"""

        try:
            summary = (
                self.generator.generate_response(
                    prompt
                )
            )

            return summary

        except Exception as error:
            return (
                f"Summary generation failed: "
                f"{str(error)}"
            )

    def get_summary(
        self,
        file_path: str,
    ):
        return self.summaries.get(
            file_path
        )

    def search_summaries(
        self,
        query: str,
        top_k: int = 5,
    ):
        query_embedding = (
            self.embedding_model.embed_text(
                query
            )
        )

        scored_summaries = []

        for (
            file_path,
            summary_embedding,
        ) in self.summary_embeddings.items():
            similarity = (
                self._cosine_similarity(
                    query_embedding,
                    summary_embedding,
                )
            )

            scored_summaries.append(
                (
                    similarity,
                    file_path,
                )
            )

        scored_summaries.sort(
            reverse=True,
            key=lambda item: item[0],
        )

        matches = []

        for (
            similarity,
            file_path,
        ) in scored_summaries[:top_k]:
            matches.append(
                {
                    "file_path": (
                        file_path
                    ),
                    "summary": (
                        self.summaries[
                            file_path
                        ]
                    ),
                    "similarity": round(
                        similarity,
                        3,
                    ),
                }
            )

        return matches

    def _cosine_similarity(
        self,
        vector_a,
        vector_b,
    ):
        vector_a = np.array(
            vector_a
        )

        vector_b = np.array(
            vector_b
        )

        numerator = np.dot(
            vector_a,
            vector_b,
        )

        denominator = (
            np.linalg.norm(vector_a)
            * np.linalg.norm(vector_b)
        )

        if denominator == 0:
            return 0

        return numerator / denominator

    def restore_summaries(
        self,
        summaries: dict,
    ):
        self.summaries = {}

        self.summary_embeddings = (
            {}
        )

        if not summaries:
            return

        for (
            file_path,
            summary_text,
        ) in summaries.items():
            self.summaries[
                str(file_path)
            ] = str(
                summary_text
            )

    def rebuild_summary_embeddings(
        self,
    ):
        self.summary_embeddings = (
            {}
        )

        for (
            file_path,
            summary_text,
        ) in self.summaries.items():
            self.summary_embeddings[
                file_path
            ] = (
                self.embedding_model.embed_text(
                    summary_text
                )
            )