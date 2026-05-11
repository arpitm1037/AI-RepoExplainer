from app.models.chunk import CodeChunk


MAX_CONTEXT_CHARS = 12000


class PromptBuilder:
    def build_prompt(
        self,
        query: str,
        chunks: list[CodeChunk],
    ) -> str:
        optimized_chunks = (
            self._optimize_chunks(
                chunks
            )
        )

        structured_context = (
            self._build_context(
                optimized_chunks
            )
        )

        prompt = f"""
You are an expert software architect and senior engineer.

Answer the question using ONLY the provided repository context.

If the answer is not clearly present in the context,
say that the repository context is insufficient.

QUESTION:
{query}


REPOSITORY CONTEXT:
{structured_context}


INSTRUCTIONS:
- Explain architecture clearly
- Mention important files and symbols
- Explain relationships between components
- Be technically precise
- Avoid hallucinating nonexistent behavior
"""

        return prompt

    def _optimize_chunks(
        self,
        chunks: list[CodeChunk],
    ):
        optimized_chunks = []

        seen_contents = set()

        current_size = 0

        for chunk in chunks:
            normalized_content = (
                chunk.content.strip()
            )

            if (
                normalized_content
                in seen_contents
            ):
                continue

            chunk_size = len(
                normalized_content
            )

            if (
                current_size
                + chunk_size
                > MAX_CONTEXT_CHARS
            ):
                break

            optimized_chunks.append(
                chunk
            )

            seen_contents.add(
                normalized_content
            )

            current_size += chunk_size

        return optimized_chunks

    def _build_context(
        self,
        chunks: list[CodeChunk],
    ) -> str:
        context_sections = []

        for chunk in chunks:
            section = f"""
========================================
FILE: {chunk.file_path}

SYMBOL: {chunk.symbol_name}

TYPE: {chunk.chunk_type}

LINES: {chunk.start_line}-{chunk.end_line}

CODE:

{chunk.content}
"""

            context_sections.append(
                section
            )

        return "\n".join(
            context_sections
        )