from app.llm.generator import (
    LLMGenerator,
)


class QueryExpander:
    def __init__(self):
        self.generator = (
            LLMGenerator()
        )

    def expand_query(
        self,
        query: str,
        repository_context: str = "",
    ):
        context_block = (
            repository_context.strip()
            or (
                "No structured repository context "
                "was provided; expand using only "
                "the user query."
            )
        )

        prompt = f"""
You are expanding a repository retrieval query.

Your goal is improving semantic code retrieval.

IMPORTANT:
Expand the query ONLY using concepts,
terminology, and architecture relevant
to the repository context.

DO NOT introduce:
- unrelated frameworks
- unrelated ecosystems
- generic software concepts
- external technologies
- internet-wide terminology

ONLY use repository-relevant language.

REPOSITORY CONTEXT:
{context_block}

USER QUERY:
{query}

IMPORTANT:
Return ONLY the expanded query.
"""

        try:
            expanded_query = (
                self.generator.generate_response(
                    prompt
                )
            )

            return expanded_query

        except Exception:
            return query