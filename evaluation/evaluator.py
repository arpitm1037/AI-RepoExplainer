class RetrievalEvaluator:
    def evaluate(
        self,
        query: str,
        retrieval_results,
        expected_files: list[str],
    ):
        retrieved_files = set()

        for result in retrieval_results:
            chunk = result["chunk"]

            retrieved_files.add(
                chunk.file_path
            )

        matched_files = set()

        for expected_file in expected_files:
            for retrieved_file in retrieved_files:
                if (
                    expected_file
                    in retrieved_file
                ):
                    matched_files.add(
                        expected_file
                    )

        precision = (
            len(matched_files)
            / max(len(retrieved_files), 1)
        )

        recall = (
            len(matched_files)
            / max(len(expected_files), 1)
        )

        return {
            "query": query,
            "expected_files": (
                expected_files
            ),
            "retrieved_files": list(
                retrieved_files
            ),
            "matched_files": list(
                matched_files
            ),
            "precision": round(
                precision,
                2,
            ),
            "recall": round(
                recall,
                2,
            ),
        }